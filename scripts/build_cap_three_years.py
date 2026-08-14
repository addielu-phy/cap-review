#!/usr/bin/env python
"""Build 113-115 CAP self-study sites from official PDFs.

The generator keeps screenshots as the audit source of truth. It builds missing
subject/year sites while preserving the hand-curated 114 Chinese and Science
sites unless --force-existing is passed.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import zipfile
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "cap-official"
QA_DIR = ROOT / "docs" / "qa"
YEARS = (113, 114, 115)
SUBJECTS = ("chinese", "english", "math", "social", "science")
SUBJECT_INFO = {
    "chinese": ("國文科", "國", "國文科語文基礎、單題與題組閱讀"),
    "english": ("英語科", "英", "英語閱讀 43 題＋官方英語聽力 21 題與逐題音檔"),
    "math": ("數學科", "數", "數學選擇題 25 題＋非選擇題 2 題"),
    "social": ("社會科", "社", "歷史、地理、公民與跨領域題組"),
    "science": ("自然科", "自", "生物、理化、地球科學與探究題組"),
}
PDF_SLUG = {
    "chinese": "chinese.pdf",
    "english": "english-reading.pdf",
    "math": "math.pdf",
    "social": "social.pdf",
    "science": "science.pdf",
}
ANSWER_COLUMN = {
    "chinese": 1,
    "english-reading": 2,
    "english-listening": 3,
    "math": 4,
    "social": 5,
    "science": 6,
}
EXPECTED = {
    "chinese": 42,
    "english-reading": 43,
    "english-listening": 21,
    "math": 25,
    "social": 54,
    "science": 50,
}
# Listening PDFs are image-based and share the same official layout for 113-115.
# Page indices are zero-based. Fractions are relative vertical crop positions.
LISTENING_LAYOUT = {
    1: [(1, .20, .60), (2, .56, .95)],
    2: [(3, .03, .34), (4, .58, .70), (5, .69, .81), (6, .80, .96)],
    3: [(7, .03, .15), (8, .14, .26), (9, .25, .37), (10, .36, .48), (11, .47, .60), (12, .80, .96)],
    4: [(13, .03, .14), (14, .13, .25), (15, .24, .36), (16, .35, .47), (17, .46, .58), (18, .57, .69), (19, .68, .82), (20, .81, .96)],
    5: [(21, .03, .20)],
}
PRESERVE = {("chinese", 114), ("science", 114)}


def jpeg_bytes(page: fitz.Page, rect: fitz.Rect, zoom: float, quality: int = 84) -> bytes:
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=rect, alpha=False)
    return pix.tobytes("jpeg", jpg_quality=quality)


def save_jpeg(page: fitz.Page, rect: fitz.Rect, path: Path, zoom: float, quality: int = 84) -> None:
    path.write_bytes(jpeg_bytes(page, rect, zoom, quality))


def answer_tables(year: int) -> dict[str, list[str]]:
    doc = fitz.open(DOCS / str(year) / "answers.pdf")
    by_subject: dict[str, dict[int, str]] = {key: {} for key in ANSWER_COLUMN}
    for page in doc:
        tables = page.find_tables().tables
        if len(tables) != 1:
            raise RuntimeError(f"{year} answer page {page.number + 1}: expected one table, got {len(tables)}")
        for row in tables[0].extract()[2:]:
            try:
                no = int((row[0] or "").strip())
            except ValueError:
                continue
            for subject, column in ANSWER_COLUMN.items():
                value = (row[column] or "").strip()
                if value in "ABCD" and len(value) == 1:
                    by_subject[subject][no] = value
    result = {}
    for subject, count in EXPECTED.items():
        values = [by_subject[subject].get(no, "") for no in range(1, count + 1)]
        missing = [i + 1 for i, value in enumerate(values) if value not in "ABCD"]
        if missing:
            raise RuntimeError(f"{year} {subject}: missing official answers {missing}")
        result[subject] = values
    return result


def block_text(block: dict) -> str:
    return "".join(span["text"] for line in block["lines"] for span in line["spans"]).strip()


def locate_questions(doc: fitz.Document, count: int) -> dict[int, tuple[int, float, str]]:
    candidates: dict[int, list[tuple[int, float, str]]] = {no: [] for no in range(1, count + 1)}
    for page_index in range(1, len(doc)):  # page 1 is cover/instructions
        page = doc[page_index]
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            text = block_text(block)
            match = re.match(r"^(\d{1,2})\.\s*", text)
            if not match:
                continue
            no = int(match.group(1))
            if no in candidates:
                candidates[no].append((page_index, float(block["bbox"][1]), text))
    chosen = {}
    last_page = 1
    for no in range(1, count + 1):
        choices = [item for item in candidates[no] if item[0] >= last_page]
        if not choices:
            raise RuntimeError(f"question {no}: no sequential text-block position found")
        # Earliest occurrence after the previous question excludes numbered instructions
        # on the cover and later repeated numbering inside passages.
        item = sorted(choices, key=lambda row: (row[0], row[1]))[0]
        chosen[no] = item
        last_page = item[0]
    return chosen


def prompt_from(text: str, fallback: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:1200] or fallback


def subject_unit(subject: str, no: int) -> str:
    if subject == "chinese":
        return "國文題組閱讀" if no >= 25 else "國文語文與單題理解"
    if subject == "math":
        return "數學非選擇題" if no > 25 else "數學選擇題"
    if subject == "social":
        if no <= 18:
            return "社會綜合（一）"
        if no <= 36:
            return "社會綜合（二）"
        return "社會題組與跨域判讀"
    if subject == "science":
        if no <= 16:
            return "自然科綜合（一）"
        if no <= 34:
            return "自然科綜合（二）"
        return "自然科題組與探究"
    return "英語閱讀"


def render_regular_assets(year: int, subject: str, out: Path) -> list[dict]:
    pdf = DOCS / str(year) / PDF_SLUG[subject]
    doc = fitz.open(pdf)
    count = EXPECTED[subject if subject != "english" else "english-reading"]
    positions = locate_questions(doc, count)
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    source_paths = {}
    for page_index in sorted({row[0] for row in positions.values()}):
        path = assets / f"source_p{page_index + 1:02d}.jpg"
        save_jpeg(doc[page_index], doc[page_index].rect, path, 1.35, 78)
        source_paths[page_index] = f"assets/{path.name}"

    questions = []
    for no in range(1, count + 1):
        page_index, y0, text = positions[no]
        page = doc[page_index]
        next_item = positions.get(no + 1)
        if next_item and next_item[0] == page_index:
            y1 = next_item[1] - 7
        else:
            y1 = page.rect.height - 35
        y0 = max(35, y0 - 7)
        if y1 <= y0 + 35:
            y1 = min(page.rect.height - 35, y0 + 180)
        rect = fitz.Rect(34, y0, page.rect.width - 34, y1)
        prefix = "r" if subject == "english" else "q"
        crop = assets / f"{prefix}{no:03d}.jpg"
        save_jpeg(page, rect, crop, 2.05, 86)
        context = []
        if page_index - 1 in source_paths:
            context.append(source_paths[page_index - 1])
        context.append(source_paths[page_index])
        questions.append({
            "sourceNo": no,
            "prompt": prompt_from(text, f"第 {no} 題"),
            "images": [f"assets/{crop.name}"],
            "contextImages": list(dict.fromkeys(context)),
        })
    return questions


def extract_listening(year: int, out: Path) -> list[dict]:
    zip_path = DOCS / str(year) / "english-listening.zip"
    assets = out / "assets"
    audio_out = assets / "audio"
    audio_out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        pdf_name = next(name for name in archive.namelist() if name.lower().endswith(".pdf"))
        doc = fitz.open(stream=archive.read(pdf_name), filetype="pdf")
        audio_members = {}
        for name in archive.namelist():
            match = re.search(r"第(\d+)題\.mp3$", name)
            if match:
                audio_members[int(match.group(1))] = name
                continue
            # Some official ZIPs omit the UTF-8 filename flag; zipfile then
            # exposes mojibake names, but the stable 04..26 prefixes still map
            # exactly to listening questions 1..21.
            prefix = re.search(r"/(\d{2}) [^/]+\.mp3$", name)
            official_question_tracks = [4, 5, 6, *range(8, 16), *range(17, 27)]
            if prefix and int(prefix.group(1)) in official_question_tracks:
                audio_members[official_question_tracks.index(int(prefix.group(1))) + 1] = name
        if sorted(audio_members) != list(range(1, 22)):
            raise RuntimeError(f"{year} listening audio set is incomplete: {sorted(audio_members)}")
        source_paths = {}
        for page_index in range(1, len(doc)):
            path = assets / f"listen_source_p{page_index + 1:02d}.jpg"
            save_jpeg(doc[page_index], doc[page_index].rect, path, 1.35, 80)
            source_paths[page_index] = f"assets/{path.name}"
        questions = []
        for page_index, ranges in LISTENING_LAYOUT.items():
            page = doc[page_index]
            for no, top, bottom in ranges:
                rect = fitz.Rect(30, page.rect.height * top, page.rect.width - 30, page.rect.height * bottom)
                crop = assets / f"l{no:03d}.jpg"
                save_jpeg(page, rect, crop, 2.05, 88)
                audio = audio_out / f"l{no:03d}.mp3"
                audio.write_bytes(archive.read(audio_members[no]))
                questions.append({
                    "sourceNo": no,
                    "prompt": f"英語聽力第 {no} 題",
                    "images": [f"assets/{crop.name}"],
                    "contextImages": [source_paths[page_index]],
                    "audio": f"assets/audio/{audio.name}",
                })
        questions.sort(key=lambda row: row["sourceNo"])
        if len(questions) != 21:
            raise RuntimeError(f"{year}: expected 21 listening crops, got {len(questions)}")
        return questions


def nonchoice_math(year: int, out: Path) -> list[dict]:
    doc = fitz.open(DOCS / str(year) / "math.pdf")
    # Last page is formulas; the two preceding pages contain non-choice Q1 and Q2.
    result = []
    for index, page_index in enumerate((len(doc) - 3, len(doc) - 2), start=1):
        page = doc[page_index]
        crop = out / "assets" / f"q{25 + index:03d}.jpg"
        save_jpeg(page, fitz.Rect(32, 35, page.rect.width - 32, page.rect.height - 32), crop, 2.0, 87)
        result.append({
            "sourceNo": index,
            "displayNo": f"非選擇題 {index}",
            "prompt": prompt_from(page.get_text("text"), f"數學非選擇題 {index}"),
            "images": [f"assets/{crop.name}"],
            "contextImages": [],
            "answerType": "self",
        })
    return result


def index_html(year: int, title: str, description: str) -> str:
    return f'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b1220"><title>{year}會考{title}｜自學評量</title>
<meta name="description" content="{year}年國中教育會考{title}：官方原題截圖、隨手練習、正式測驗、錯題練習、自動評分與教師端統計。">
<link rel="stylesheet" href="../../shared/style.css"></head><body>
<main class="wrap" id="app"><noscript>此頁需要啟用 JavaScript 才能作答。</noscript></main>
<div class="lb" id="lightbox"><img id="lbimg" alt="放大原題截圖"></div><button class="btn sm" id="themeToggle" aria-label="切換深淺色">☀️</button>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore-compat.js"></script>
<script src="data.js?v={year}-three-year-cap"></script><script src="firebase-config.js?v={year}-three-year-cap"></script><script src="../../shared/quiz-app.js?v=three-year-cap"></script>
</body></html>\n'''


def teacher_html(year: int, title: str) -> str:
    return f'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b1220"><title>教師端｜{year}會考{title}</title><meta name="description" content="{year}會考{title}教師端：學生作答、成績、最常錯題、單元弱點與 CSV。">
<link rel="stylesheet" href="../../shared/style.css"></head><body>
<main class="wrap" id="app"></main><button class="btn sm" id="themeToggle" aria-label="切換深淺色">☀️</button>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js"></script><script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-auth-compat.js"></script><script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore-compat.js"></script>
<script src="data.js?v={year}-three-year-cap"></script><script src="firebase-config.js?v={year}-three-year-cap"></script><script src="../../shared/teacher.js?v=three-year-cap"></script>
</body></html>\n'''


def make_questions(year: int, subject: str, answers: dict[str, list[str]], out: Path) -> list[dict]:
    regular = render_regular_assets(year, subject, out)
    questions = []
    if subject == "english":
        for item, answer in zip(regular, answers["english-reading"], strict=True):
            no = len(questions) + 1
            questions.append({"no": no, "displayNo": f"閱讀 {item['sourceNo']}", "unit": "英語閱讀", "answer": answer, "options": ["A", "B", "C", "D"], "weight": 80 / 43, **item,
                              "explanation": f"官方參考答案為 {answer}。請回到原題與選文，核對文法、語意或文本證據。"})
        listening = extract_listening(year, out)
        for item, answer in zip(listening, answers["english-listening"], strict=True):
            no = len(questions) + 1
            questions.append({"no": no, "displayNo": f"聽力 {item['sourceNo']}", "unit": "英語聽力", "answer": answer, "options": ["A", "B", "C"], "weight": 20 / 21, **item,
                              "explanation": f"官方參考答案為 {answer}。可重播本題官方音檔，核對關鍵字、對話語意與圖片／選項。"})
        return questions

    for item, answer in zip(regular, answers[subject], strict=True):
        no = item["sourceNo"]
        unit = subject_unit(subject, no)
        weight = 85 / 25 if subject == "math" else 100 / EXPECTED[subject]
        questions.append({"no": no, "displayNo": f"第 {no} 題", "unit": unit, "answer": answer, "options": ["A", "B", "C", "D"], "weight": weight, **item,
                          "explanation": f"本題考查「{unit}」。官方參考答案為 {answer}；請以原題截圖、題組前文與題幹條件逐項排除。"})
    if subject == "math":
        for item in nonchoice_math(year, out):
            no = len(questions) + 1
            questions.append({"no": no, "unit": "數學非選擇題", "answer": "", "options": [], **item,
                              "explanation": "本題為官方非選擇題，需完整呈現計算過程與理由；平台不以單一字串自動評分，請完成後依官方評分原則自行核對。"})
    return questions


def write_contact_sheet(year: int, subject: str, questions: list[dict], out: Path) -> Path:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    cells = []
    for question in questions:
        image_path = out / question["images"][0]
        image = Image.open(image_path).convert("RGB")
        image.thumbnail((300, 220))
        cell = Image.new("RGB", (320, 260), "white")
        cell.paste(image, ((320 - image.width) // 2, 28))
        ImageDraw.Draw(cell).text((8, 7), str(question.get("displayNo") or question["no"]), fill="black")
        cells.append(cell)
    cols = 4
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 320, rows * 260), (218, 224, 232))
    for index, cell in enumerate(cells):
        sheet.paste(cell, ((index % cols) * 320, (index // cols) * 260))
    path = QA_DIR / f"{year}-{subject}-contact.jpg"
    sheet.save(path, quality=88)
    return path


def build_site(year: int, subject: str, answers: dict[str, list[str]], force_existing: bool) -> dict:
    out = ROOT / subject / str(year)
    if (subject, year) in PRESERVE and not force_existing:
        return {"year": year, "subject": subject, "status": "preserved", "path": out.relative_to(ROOT).as_posix()}
    if out.exists():
        shutil.rmtree(out)
    (out / "assets").mkdir(parents=True, exist_ok=True)
    title, _, description = SUBJECT_INFO[subject]
    questions = make_questions(year, subject, answers, out)
    quiz = {
        "id": f"cap-{year}-{subject}",
        "siteTitle": "會考三年五科自學平台",
        "title": f"{year}年國中教育會考{title}",
        "subject": title,
        "grade": "國中會考",
        "scoreScale": "weighted",
        "perScore": 1,
        "totalScore": 100,
        "scoreNote": ("英語依官方比例換算：閱讀 80%、聽力 20%，合計滿分 100。" if subject == "english" else
                      "數學選擇題自動換算 85 分；2 題非選擇題共 15 分需依官方 0–3 級分規準自行核對。" if subject == "math" else
                      f"共 {len(questions)} 題，依答對比例換算為 100 分。"),
        "sourceLabel": f"{year}年國中教育會考{title}官方公開試題、參考答案" + ("與官方逐題聽力音檔" if subject == "english" else ""),
        "sourceUrl": "https://cap.rcpet.edu.tw/examination.html",
        "description": description + "；保留官方原題截圖，提供隨手練習、正式測驗、錯題練習與教師端統計。",
        "questions": questions,
    }
    data = "/* Generated from official CAP PDFs. Screenshots are the audit source of truth. */\n"
    data += "window.CLOUD = window.CLOUD || { enabled: false, teacherEmail: \"\", config: {} };\n"
    data += "window.QUIZ = " + json.dumps(quiz, ensure_ascii=False, indent=2) + ";\n"
    (out / "data.js").write_text(data, encoding="utf-8")
    (out / "index.html").write_text(index_html(year, title, description), encoding="utf-8")
    (out / "teacher.html").write_text(teacher_html(year, title), encoding="utf-8")
    shutil.copy2(ROOT / "science" / "114" / "firebase-config.js", out / "firebase-config.js")
    contact = write_contact_sheet(year, subject, questions, out)
    return {"year": year, "subject": subject, "status": "built", "questions": len(questions), "path": out.relative_to(ROOT).as_posix(), "contact": contact.relative_to(ROOT).as_posix()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="*", type=int, default=list(YEARS))
    parser.add_argument("--subjects", nargs="*", choices=SUBJECTS, default=list(SUBJECTS))
    parser.add_argument("--force-existing", action="store_true")
    args = parser.parse_args()
    report = []
    for year in args.years:
        answers = answer_tables(year)
        for subject in args.subjects:
            row = build_site(year, subject, answers, args.force_existing)
            report.append(row)
            print(json.dumps(row, ensure_ascii=False))
    QA_DIR.mkdir(parents=True, exist_ok=True)
    (QA_DIR / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"processed {len(report)} subject-year sites")


if __name__ == "__main__":
    main()
