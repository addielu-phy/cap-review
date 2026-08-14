#!/usr/bin/env python
"""Download official CAP question and answer PDFs listed in cap-sources.json."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "cap-sources.json"
OUT_ROOT = ROOT / "docs" / "cap-official"
USER_AGENT = "Mozilla/5.0 (compatible; CAP self-study educational archive QA)"
LABEL_TO_SLUG = {
    "參考答案": "answers",
    "國文科": "chinese",
    "英語（閱讀）": "english-reading",
    "英語(閱讀)": "english-reading",
    "英語（聽力）": "english-listening",
    "英語(聽力)": "english-listening",
    "數學科": "math",
    "社會科": "social",
    "自然科": "science",
}


def slug_for(label: str) -> str:
    for key, slug in LABEL_TO_SLUG.items():
        if key in label:
            return slug
    return ""


def download_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:
        raw = response.read()
    if b"Google Drive - Virus scan warning" not in raw:
        return raw

    class ConfirmParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.action = ""
            self.fields: dict[str, str] = {}

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            data = dict(attrs)
            if tag == "form" and data.get("id") == "download-form":
                self.action = data.get("action") or ""
            if tag == "input" and data.get("type") == "hidden" and data.get("name"):
                self.fields[data["name"]] = data.get("value") or ""

    parser = ConfirmParser()
    parser.feed(raw.decode("utf-8", "ignore"))
    if not parser.action or not parser.fields:
        raise RuntimeError("Google Drive confirmation form was not found")
    confirm_url = parser.action + "?" + urllib.parse.urlencode(parser.fields)
    request = urllib.request.Request(confirm_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=240) as response:
        return response.read()


def one(job: tuple[int, dict, Path, bool]) -> dict:
    year, item, out_dir, force = job
    slug = slug_for(item["label"])
    extension = ".zip" if slug == "english-listening" else ".pdf"
    path = out_dir / f"{slug}{extension}"
    source_url = item["url"]
    if item.get("driveId"):
        source_url = f"https://drive.google.com/uc?export=download&id={item['driveId']}"
    if path.exists() and not force:
        raw = path.read_bytes()
    else:
        raw = download_bytes(source_url)
        path.write_bytes(raw)
    if slug == "english-listening":
        if not raw.startswith(b"PK"):
            raise RuntimeError(f"{year} {slug}: downloaded content is not ZIP ({len(raw)} bytes)")
    elif not raw.startswith(b"%PDF"):
        raise RuntimeError(f"{year} {slug}: downloaded content is not PDF ({len(raw)} bytes)")
    return {
        "year": year,
        "slug": slug,
        "label": item["label"],
        "officialUrl": item["url"],
        "driveId": item.get("driveId", ""),
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    source = json.loads(MANIFEST.read_text(encoding="utf-8"))
    jobs = []
    for year_text, year_data in source["years"].items():
        year = int(year_text)
        out_dir = OUT_ROOT / year_text
        out_dir.mkdir(parents=True, exist_ok=True)
        for item in year_data["links"]:
            if not slug_for(item["label"]):
                continue
            jobs.append((year, item, out_dir, args.force))
    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for record in pool.map(one, jobs):
            records.append(record)
            print(f"{record['year']} {record['slug']}: {record['bytes']} bytes {record['sha256'][:12]}")
    records.sort(key=lambda row: (row["year"], row["slug"]))
    (OUT_ROOT / "downloads.json").write_text(
        json.dumps({"files": records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"downloaded/verified {len(records)} official PDFs")


if __name__ == "__main__":
    main()
