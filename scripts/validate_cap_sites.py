#!/usr/bin/env python
"""Deterministic validation for the 113-115 CAP sites and screenshot assets."""
from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
from pathlib import Path

from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[1]
YEARS = (113, 114, 115)
SUBJECTS = ("chinese", "english", "math", "social", "science")
EXPECTED = {"chinese": 42, "english": 64, "math": 27, "social": 54, "science": 50}


def load_quiz(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\.QUIZ\s*=\s*(\{.*\})\s*;\s*$", text, re.S)
    if not match:
        raise ValueError("window.QUIZ JSON assignment not found")
    return json.loads(match.group(1))


def image_metrics(path: Path) -> dict:
    with Image.open(path) as image:
        gray = image.convert("L")
        sample = gray.copy()
        sample.thumbnail((320, 320))
        stat = ImageStat.Stat(sample)
        pixels = list(sample.getdata())
        dark_ratio = sum(value < 235 for value in pixels) / max(1, len(pixels))
        return {
            "width": image.width,
            "height": image.height,
            "mean": round(stat.mean[0], 2),
            "stddev": round(stat.stddev[0], 2),
            "darkRatio": round(dark_ratio, 5),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=ROOT / "docs" / "qa" / "validation-report.json")
    args = parser.parse_args()
    errors: list[str] = []
    warnings: list[str] = []
    sites = []
    quiz_ids = set()
    all_primary_images = []
    all_context_images = []
    all_audio = []

    for year in YEARS:
        for subject in SUBJECTS:
            site = ROOT / subject / str(year)
            label = f"{year}-{subject}"
            for name in ("index.html", "teacher.html", "data.js", "firebase-config.js"):
                if not (site / name).is_file():
                    errors.append(f"{label}: missing {name}")
            if errors and not (site / "data.js").is_file():
                continue
            try:
                quiz = load_quiz(site / "data.js")
            except Exception as exc:
                errors.append(f"{label}: cannot parse data.js: {exc}")
                continue
            questions = quiz.get("questions") or []
            if len(questions) != EXPECTED[subject]:
                errors.append(f"{label}: expected {EXPECTED[subject]} questions, got {len(questions)}")
            expected_id = f"cap-{year}-{subject}"
            if quiz.get("id") != expected_id:
                errors.append(f"{label}: quiz id {quiz.get('id')!r}, expected {expected_id!r}")
            if quiz.get("id") in quiz_ids:
                errors.append(f"{label}: duplicate quiz id {quiz.get('id')}")
            quiz_ids.add(quiz.get("id"))
            numbers = [q.get("no") for q in questions]
            if numbers != list(range(1, len(questions) + 1)):
                errors.append(f"{label}: question numbers are not sequential/unique")
            self_count = 0
            for question in questions:
                qlabel = question.get("displayNo") or question.get("no")
                if question.get("answerType") == "self":
                    self_count += 1
                elif question.get("answer") not in "ABCD":
                    errors.append(f"{label} {qlabel}: invalid answer {question.get('answer')!r}")
                images = question.get("images") or []
                if not images:
                    errors.append(f"{label} {qlabel}: no primary screenshot")
                for rel in images:
                    path = site / rel
                    if not path.is_file():
                        errors.append(f"{label} {qlabel}: missing image {rel}")
                        continue
                    metrics = image_metrics(path)
                    all_primary_images.append({"site": label, "question": qlabel, "path": rel, **metrics})
                    if metrics["width"] < 450 or metrics["height"] < 70:
                        warnings.append(f"{label} {qlabel}: suspiciously small crop {metrics['width']}x{metrics['height']}")
                    if metrics["stddev"] < 5 or metrics["darkRatio"] < 0.003:
                        errors.append(f"{label} {qlabel}: screenshot appears blank/near-blank ({metrics})")
                for rel in question.get("contextImages") or []:
                    path = site / rel
                    if not path.is_file():
                        errors.append(f"{label} {qlabel}: missing context {rel}")
                    else:
                        all_context_images.append({"site": label, "question": qlabel, "path": rel})
                if question.get("audio"):
                    path = site / question["audio"]
                    if not path.is_file():
                        errors.append(f"{label} {qlabel}: missing audio {question['audio']}")
                    elif path.stat().st_size < 10_000:
                        errors.append(f"{label} {qlabel}: audio too small ({path.stat().st_size} bytes)")
                    else:
                        all_audio.append({"site": label, "question": qlabel, "path": question["audio"], "bytes": path.stat().st_size})
            if subject == "math" and self_count != 2:
                errors.append(f"{label}: expected 2 self-rated non-choice questions, got {self_count}")
            if subject == "english" and len([q for q in questions if q.get("audio")]) != 21:
                errors.append(f"{label}: expected 21 listening audio questions")
            sites.append({"year": year, "subject": subject, "quizId": quiz.get("id"), "questions": len(questions), "selfRated": self_count})

    js_files = [ROOT / "shared" / "quiz-app.js", ROOT / "shared" / "teacher.js"]
    for year in YEARS:
        for subject in SUBJECTS:
            js_files.extend([ROOT / subject / str(year) / "data.js", ROOT / subject / str(year) / "firebase-config.js"])
    js_failures = []
    for path in js_files:
        result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        if result.returncode:
            js_failures.append({"path": path.relative_to(ROOT).as_posix(), "stderr": result.stderr.strip()})
            errors.append(f"JS syntax failed: {path.relative_to(ROOT)}")

    report = {
        "sites": sites,
        "counts": {
            "sites": len(sites),
            "questions": sum(row["questions"] for row in sites),
            "primaryImages": len(all_primary_images),
            "contextReferences": len(all_context_images),
            "audioFiles": len(all_audio),
            "jsFilesChecked": len(js_files),
        },
        "errors": errors,
        "warnings": warnings,
        "jsFailures": js_failures,
        "primaryImageMetrics": all_primary_images,
        "audio": all_audio,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], ensure_ascii=False))
    print(f"errors={len(errors)} warnings={len(warnings)} report={args.report}")
    for item in errors[:30]:
        print("ERROR", item)
    for item in warnings[:30]:
        print("WARN", item)
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
