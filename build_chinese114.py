import json
import re
import shutil
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent
PDF = ROOT / "docs" / "chinese114" / "114-chinese.pdf"
OUT = ROOT / "chinese" / "114"
ASSETS = OUT / "assets"

ANSWERS = [
    "D", "B", "B", "B", "A", "A", "B", "C", "C", "A",
    "D", "C", "C", "A", "A", "A", "C", "D", "A", "D",
    "D", "B", "D", "B", "B", "A", "B", "C", "C", "D",
    "C", "C", "D", "A", "D", "B", "C", "A", "D", "B",
    "D", "B",
]
assert len(ANSWERS) == 42, len(ANSWERS)

# PDF page indices are zero-based; page 0 is the cover/instructions.
PAGE_QS = {
    1: list(range(1, 5)),
    2: list(range(5, 8)),
    3: list(range(8, 12)),
    4: list(range(12, 18)),
    5: list(range(18, 22)),
    6: list(range(22, 25)),
    7: list(range(25, 27)),
    8: list(range(27, 29)),
    9: [29],
    10: list(range(30, 34)),
    11: list(range(34, 36)),
    12: list(range(36, 38)),
    13: list(range(38, 40)),
    14: list(range(40, 43)),
}
UNITS = {
    1: "資訊判讀與語用", 2: "文意理解與情境推論", 3: "文字形義與六書", 4: "現代詩理解",
    5: "文字演變與字體", 6: "圖表資訊判讀", 7: "對聯與國學常識", 8: "曲文閱讀與修辭",
    9: "生活文本閱讀", 10: "文言文閱讀", 11: "文意脈絡與寫作", 12: "標點符號與語意",
    13: "詞語運用", 14: "字音辨識", 15: "文學常識與閱讀", 16: "字形與成語",
    17: "古典詩詞鑑賞", 18: "古典詩閱讀", 19: "成語詞語運用", 20: "文言人物與語意",
    21: "圖表推論與文言閱讀", 22: "文言人物與語意", 23: "文言政論閱讀", 24: "文言議論閱讀",
    25: "題組閱讀：現代散文", 26: "題組閱讀：寫作分析", 27: "題組閱讀：圖文整合", 28: "題組閱讀：圖文整合",
    29: "題組閱讀：劇本與視覺化寫作", 30: "題組閱讀：劇本分析", 31: "題組閱讀：劇本分析",
    32: "題組閱讀：現代散文", 33: "題組閱讀：現代散文", 34: "題組閱讀：生活消費文本", 35: "題組閱讀：生活消費文本",
    36: "題組閱讀：歷史文化文本", 37: "題組閱讀：歷史文化文本", 38: "題組閱讀：文言人物關係", 39: "題組閱讀：文言人物關係",
    40: "題組閱讀：文言書信", 41: "題組閱讀：文言書信", 42: "題組閱讀：文言書信",
}


def clean_prompt(s: str) -> str:
    s = re.sub(r"\s+", " ", s.replace("\x0c", " ").replace("\b", " ")).strip()
    return s[:900]


def question_positions(page, nums):
    found = {}
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        text = "".join(s["text"] for line in b["lines"] for s in line["spans"]).strip()
        m = re.match(r"^(\d{1,2})\.\s*", text)
        if not m:
            continue
        n = int(m.group(1))
        if n in nums and n not in found:
            found[n] = b["bbox"][1]
    missing = [n for n in nums if n not in found]
    if missing:
        raise RuntimeError(f"Missing question positions on page {page.number + 1}: {missing}")
    return found


def extract_prompts(doc):
    prompts = {}
    for page_index, nums in PAGE_QS.items():
        txt = doc[page_index].get_text("text")
        starts = []
        for m in re.finditer(r"(?m)^\s*(\d{1,2})\.\s*", txt):
            n = int(m.group(1))
            if n in nums:
                starts.append((n, m.start()))
        starts = sorted(dict(starts).items(), key=lambda x: x[1])
        for i, (n, pos) in enumerate(starts):
            end = starts[i + 1][1] if i + 1 < len(starts) else len(txt)
            prompts[n] = clean_prompt(txt[pos:end])
    return prompts


def save_clip(page, rect, path, zoom=2.4):
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=rect, alpha=False)
    pix.save(path)


def main():
    if not PDF.exists():
        raise SystemExit(f"Missing source PDF: {PDF}")
    OUT.mkdir(parents=True, exist_ok=True)
    if ASSETS.exists():
        shutil.rmtree(ASSETS)
    ASSETS.mkdir(parents=True)

    doc = fitz.open(PDF)
    prompts = extract_prompts(doc)
    q_page = {}
    q_crop = {}

    # Full page images for題組/跨頁 context.
    for page_index in range(1, len(doc)):
        page = doc[page_index]
        page_file = ASSETS / f"source_p{page_index+1:02d}.jpg"
        save_clip(page, page.rect, page_file, zoom=1.8)

    for page_index, nums in PAGE_QS.items():
        page = doc[page_index]
        ypos = question_positions(page, nums)
        ordered = sorted(nums)
        for idx, n in enumerate(ordered):
            y0 = max(40, ypos[n] - 10)
            next_y = ypos[ordered[idx + 1]] if idx + 1 < len(ordered) else page.rect.height - 42
            y1 = min(page.rect.height - 42, next_y - 8)
            if y1 <= y0 + 40:
                y1 = min(page.rect.height - 42, y0 + 180)
            rect = fitz.Rect(48, y0, page.rect.width - 45, y1)
            out = ASSETS / f"q{n:03d}.jpg"
            save_clip(page, rect, out, zoom=2.4)
            q_page[n] = page_index + 1
            q_crop[n] = out.name

    questions = []
    for n in range(1, 43):
        images = []
        # 題組題提供完整頁面作為選文/圖表來源；30-31 的共同選文在前一頁。
        if n in (30, 31):
            images.append("assets/source_p10.jpg")
        if n >= 25:
            images.append(f"assets/source_p{q_page[n]:02d}.jpg")
        images.append(f"assets/{q_crop[n]}")
        # Preserve order without duplicates.
        seen = set(); images = [x for x in images if not (x in seen or seen.add(x))]
        ans = ANSWERS[n - 1]
        unit = UNITS[n]
        questions.append({
            "no": n,
            "unit": unit,
            "answer": ans,
            "options": ["A", "B", "C", "D"],
            "images": images,
            "prompt": prompts.get(n, f"第 {n} 題"),
            "explanation": f"本題考點：{unit}。正解為 {ans}。請回到原題截圖／選文中的關鍵語句、圖表或文意脈絡核對；{ans} 最符合題幹要求，其餘選項多屬與文本不符、推論過度或語詞使用不當。"
        })

    quiz = {
        "id": "cap-114-chinese",
        "siteTitle": "會考複習自學平台",
        "title": "114年國中教育會考國文科",
        "subject": "國文科",
        "grade": "國中會考",
        "perScore": 1,
        "totalScore": 42,
        "sourceLabel": "114年國中教育會考國文科官方公開試題與參考答案",
        "sourceUrl": "https://cap.rcpet.edu.tw/examination.html",
        "description": "以官方公開試題 PDF 製作的國文科自學練習：保留原題截圖、題組選文、自動評分、錯題練習、逐題考點提示與教師版統計。",
        "questions": questions,
    }

    data = "/* 114 CAP Chinese self-study quiz data. Source screenshots are the audit source of truth. */\n"
    data += "window.CLOUD = window.CLOUD || { enabled: false, teacherEmail: \"\", config: {} };\n"
    data += "window.QUIZ = " + json.dumps(quiz, ensure_ascii=False, indent=2) + ";\n"
    (OUT / "data.js").write_text(data, encoding="utf-8")
    print(f"wrote {OUT / 'data.js'} with {len(questions)} questions")
    print(f"assets: {len(list(ASSETS.glob('*')))} files")


if __name__ == "__main__":
    main()
