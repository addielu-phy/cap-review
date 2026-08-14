#!/usr/bin/env python
"""Validate the generated CAP catalog and all linked destinations."""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SERIES = 15
EXPECTED_RESOURCES = 23


def load_assignment(text: str, name: str) -> list[dict]:
    match = re.search(rf"window\.{re.escape(name)}\s*=\s*(\[.*?\]);", text, re.S)
    if not match:
        raise ValueError(f"missing window.{name} assignment")
    return json.loads(match.group(1))


def check_url(url: str) -> tuple[int | str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 CAP catalog validator"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.url
    except urllib.error.HTTPError as exc:
        return exc.code, url
    except Exception as exc:
        return "ERR", str(exc)


def local_target(url: str) -> Path | None:
    if not url or url.startswith("https://"):
        return None
    return ROOT / url.split("?", 1)[0].split("#", 1)[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    data_path = ROOT / "catalog-data.js"
    index_path = ROOT / "index.html"
    app_path = ROOT / "catalog-app.js"
    for path in (data_path, index_path, app_path, ROOT / "teacher.html"):
        if not path.is_file():
            errors.append(f"missing {path.relative_to(ROOT)}")

    if errors:
        print("\n".join(errors))
        raise SystemExit(1)

    text = data_path.read_text(encoding="utf-8")
    series = load_assignment(text, "CAP_SERIES")
    resources = load_assignment(text, "CAP_RESOURCES")
    if len(series) != EXPECTED_SERIES:
        errors.append(f"expected {EXPECTED_SERIES} series entries, got {len(series)}")
    if len(resources) != EXPECTED_RESOURCES:
        errors.append(f"expected {EXPECTED_RESOURCES} resource entries, got {len(resources)}")

    ids = [item.get("id") for item in [*series, *resources]]
    if len(ids) != len(set(ids)):
        errors.append("catalog IDs are not unique")

    public_text = index_path.read_text(encoding="utf-8") + text + app_path.read_text(encoding="utf-8")
    if re.search(r"[A-Za-z]:\\(?:Users|Program Files|Windows|Temp)(?:\\|\b)|/Users/|AppData[/\\]", public_text):
        errors.append("public catalog contains an absolute local path")
    for marker in ("會考自學總入口", "113–115 三年五科", "catalogSearch", "CAP_SERIES", "CAP_RESOURCES"):
        if marker not in public_text:
            errors.append(f"catalog marker missing: {marker}")

    external: dict[str, list[str]] = {}
    for item in series:
        for key in ("studentHref", "teacherHref"):
            url = item.get(key, "")
            target = local_target(url)
            if target and not target.exists():
                errors.append(f"{item.get('id')}: missing local {key} target {url}")
    for item in resources:
        status = item.get("status")
        href = item.get("href", "")
        repo = item.get("repoHref", "")
        if status == "planned":
            if href:
                errors.append(f"{item.get('id')}: planned item must not expose a live site href")
            if not repo.startswith("https://github.com/"):
                errors.append(f"{item.get('id')}: planned item needs a GitHub repository link")
        elif not href:
            errors.append(f"{item.get('id')}: live/legacy item is missing href")
        for key in ("href", "teacherHref", "repoHref"):
            url = item.get(key, "")
            if not url:
                continue
            if url.startswith("http://"):
                errors.append(f"{item.get('id')}: insecure URL {url}")
            target = local_target(url)
            if target and not target.exists():
                errors.append(f"{item.get('id')}: missing local {key} target {url}")
            if url.startswith("https://") and not args.no_network:
                external.setdefault(url, []).append(item.get("id", ""))

    link_results = []
    for url, owners in external.items():
        status, final = check_url(url)
        link_results.append({"url": url, "status": status, "final": final, "owners": owners})
        if status != 200:
            errors.append(f"external URL failed ({status}): {url}")

    counts = {
        "series": len(series),
        "resources": len(resources),
        "liveOrLegacyResources": sum(item.get("status") != "planned" for item in resources),
        "plannedResources": sum(item.get("status") == "planned" for item in resources),
        "externalUrlsChecked": len(link_results),
    }
    print(json.dumps(counts, ensure_ascii=False))
    print(f"errors={len(errors)} warnings={len(warnings)}")
    for error in errors:
        print("ERROR", error)
    for warning in warnings:
        print("WARN", warning)
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
