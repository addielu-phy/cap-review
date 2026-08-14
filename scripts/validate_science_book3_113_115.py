#!/usr/bin/env python
"""Deterministic validation for the 113-115 Book 3 curated science quiz."""
from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from pathlib import Path

from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "science" / "book3"
EXPECTED_SELECTED = [
    (113, 4), (113, 18), (113, 27), (113, 32), (113, 36),
    (114, 1), (114, 2), (114, 4), (114, 7), (114, 11), (114, 14),
    (114, 17), (114, 26), (114, 29), (114, 38), (114, 40),
    (115, 1), (115, 2), (115, 3), (115, 5), (115, 9), (115, 16),
    (115, 18), (115, 30), (115, 36),
]
EXPECTED_CHAPTERS = {
    "第1章 基本測量與科學探究": 5,
    "第2章 物質的世界": 4,
    "第3章 波動與聲音": 3,
    "第4章 光": 3,
    "第5章 溫度與熱": 5,
    "第6章 物質的基本結構": 5,
}


def load_assignment(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\.QUIZ\s*=\s*(\{.*\})\s*;\s*$", text, re.S)
    if not match:
        raise ValueError(f"window.QUIZ assignment missing in {path}")
    return json.loads(match.group(1))


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    for filename in ("index.html", "teacher.html", "data.js", "firebase-config.js", "README.md"):
        if not (SITE / filename).is_file():
            errors.append(f"missing science/book3/{filename}")

    quiz = load_assignment(SITE / "data.js")
    questions = quiz.get("questions", [])
    if quiz.get("id") != "cap-113-115-science-book3":
        errors.append(f"unexpected quizId: {quiz.get('id')}")
    if quiz.get("practiceCount") != 10:
        errors.append("practiceCount must be 10")
    if len(questions) != 25:
        errors.append(f"expected 25 questions, got {len(questions)}")
    if [q.get("no") for q in questions] != list(range(1, 26)):
        errors.append("subset numbers are not sequential 1..25")

    selected = [(q.get("sourceYear"), q.get("sourceNo")) for q in questions]
    if selected != EXPECTED_SELECTED:
        errors.append(f"selected source list changed: {selected}")
    if len(selected) != len(set(selected)):
        errors.append("duplicate source question")

    chapters = Counter(q.get("unit") for q in questions)
    if dict(chapters) != EXPECTED_CHAPTERS:
        errors.append(f"chapter distribution mismatch: {dict(chapters)}")

    source_cache: dict[int, dict] = {}
    image_metrics = []
    for q in questions:
        year = q["sourceYear"]
        if year not in source_cache:
            source_cache[year] = load_assignment(ROOT / "science" / str(year) / "data.js")
        source = source_cache[year]["questions"][q["sourceNo"] - 1]
        if q.get("answer") != source.get("answer"):
            errors.append(f"{q['displayNo']}: answer differs from official source")
        if q.get("prompt") != source.get("prompt"):
            errors.append(f"{q['displayNo']}: prompt differs from source data")
        if q.get("answer") not in "ABCD":
            errors.append(f"{q['displayNo']}: invalid answer")
        if len(q.get("explanation", "")) < 35:
            errors.append(f"{q['displayNo']}: explanation too short")
        if "請以原題截圖" in q.get("explanation", "") or "詳解產生中" in q.get("explanation", ""):
            errors.append(f"{q['displayNo']}: placeholder explanation")
        images = q.get("images", [])
        if len(images) != 1:
            errors.append(f"{q['displayNo']}: expected one primary image")
        for rel in images:
            path = (SITE / rel).resolve()
            if not path.is_file():
                errors.append(f"{q['displayNo']}: missing image {rel}")
                continue
            with Image.open(path) as image:
                sample = image.convert("L")
                sample.thumbnail((320, 320))
                stat = ImageStat.Stat(sample)
                image_metrics.append({"question": q["displayNo"], "width": image.width, "height": image.height, "stddev": round(stat.stddev[0], 2)})
                if image.width < 450 or image.height < 100 or stat.stddev[0] < 5:
                    errors.append(f"{q['displayNo']}: suspicious image {image.width}x{image.height}, stddev={stat.stddev[0]:.2f}")

    for html_name, script_name in (("index.html", "quiz-app.js"), ("teacher.html", "teacher.js")):
        html = (SITE / html_name).read_text(encoding="utf-8")
        for marker in ("data.js", "firebase-config.js", script_name):
            if marker not in html:
                errors.append(f"{html_name}: missing {marker}")

    js_files = [SITE / "data.js", SITE / "firebase-config.js", ROOT / "shared" / "quiz-app.js", ROOT / "shared" / "teacher.js"]
    for path in js_files:
        result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        if result.returncode:
            errors.append(f"node --check failed: {path.relative_to(ROOT)}: {result.stderr.strip()}")

    if quiz.get("scoreScale") != "percent" or quiz.get("totalScore") != 100:
        errors.append("quiz must use 0-100 percent scoring")
    all_correct_score = round(sum(1 for q in questions if q["answer"] == q["answer"]) / len(questions) * 100)
    all_wrong_score = round(sum(1 for q in questions if ({"A": "B", "B": "C", "C": "D", "D": "A"}[q["answer"]] == q["answer"])) / len(questions) * 100)
    if all_correct_score != 100 or all_wrong_score != 0:
        errors.append("scoring anchors failed")

    report = {
        "quizId": quiz.get("id"),
        "questions": len(questions),
        "practiceCount": quiz.get("practiceCount"),
        "sourceYears": dict(Counter(str(y) for y, _ in selected)),
        "chapters": dict(chapters),
        "imagesChecked": len(image_metrics),
        "scoreAnchors": {"allCorrect": all_correct_score, "allWrong": all_wrong_score},
        "errors": errors,
        "warnings": warnings,
        "imageMetrics": image_metrics,
    }
    report_path = ROOT / "docs" / "qa" / "book3-validation-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("quizId", "questions", "practiceCount", "sourceYears", "chapters", "imagesChecked", "scoreAnchors")}, ensure_ascii=False))
    print(f"errors={len(errors)} warnings={len(warnings)} report={report_path}")
    for error in errors:
        print("ERROR", error)
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
