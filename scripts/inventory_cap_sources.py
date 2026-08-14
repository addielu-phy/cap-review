#!/usr/bin/env python
"""Inventory official CAP exam links for 113-115.

Fetches the official year pages, extracts labelled links, records Google Drive
file IDs, and writes a deterministic JSON manifest used by the quiz builders.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "cap-sources.json"
YEARS = (113, 114, 115)
USER_AGENT = "Mozilla/5.0 (compatible; CAP self-study educational archive QA)"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self._href = ""
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        data = dict(attrs)
        self._href = data.get("href") or ""
        self._parts = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._href:
            return
        label = re.sub(r"\s+", " ", "".join(self._parts)).strip()
        self.links.append({"label": label, "url": self._href})
        self._href = ""
        self._parts = []


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def drive_id(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    if qs.get("id"):
        return qs["id"][0]
    match = re.search(r"/(?:file/d|document/d)/([^/?#]+)", parsed.path)
    return match.group(1) if match else ""


def keep_link(label: str) -> bool:
    wanted = (
        "參考答案",
        "國文科",
        "英語（閱讀）",
        "英語(閱讀)",
        "英語（聽力）",
        "英語(聽力)",
        "數學科",
        "社會科",
        "自然科",
        "試題疑義",
        "釋復",
        "計分與閱卷結果",
        "各題通過率",
    )
    return any(key in label for key in wanted)


def build_manifest(years: tuple[int, ...]) -> dict:
    result = {
        "schemaVersion": 1,
        "officialArchive": "https://cap.rcpet.edu.tw/examination.html",
        "years": {},
    }
    for year in years:
        year_url = f"https://cap.rcpet.edu.tw/exam/{year}/{year}exam.html"
        raw = fetch(year_url)
        parser = LinkParser()
        parser.feed(raw.decode("utf-8", "ignore"))
        links = []
        for item in parser.links:
            label = item["label"]
            if not keep_link(label):
                continue
            url = urllib.parse.urljoin(year_url, item["url"])
            links.append(
                {
                    "label": label,
                    "url": url,
                    "driveId": drive_id(url),
                }
            )
        result["years"][str(year)] = {
            "pageUrl": year_url,
            "pageSha256": hashlib.sha256(raw).hexdigest(),
            "links": links,
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--years", nargs="*", type=int, default=list(YEARS))
    args = parser.parse_args()
    manifest = build_manifest(tuple(args.years))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for year, data in manifest["years"].items():
        print(f"{year}: {len(data['links'])} relevant links")
        for item in data["links"]:
            suffix = f" [{item['driveId']}]" if item["driveId"] else ""
            print(f"  - {item['label']}: {item['url']}{suffix}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
