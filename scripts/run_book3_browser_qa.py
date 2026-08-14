#!/usr/bin/env python
"""Browser QA for the curated Book 3 quiz. Run with `uv run --with playwright`."""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "qa"
CHROME_CANDIDATES = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
]


def browser_path() -> str:
    for path in CHROME_CANDIDATES:
        if path.is_file():
            return str(path)
    raise FileNotFoundError("Chrome/Edge executable not found")


async def run(base: str, label: str) -> dict:
    base = base.rstrip("/")
    report: dict = {"base": base, "label": label, "viewports": {}, "errors": []}
    OUT.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=browser_path())
        for width in (390, 320):
            context = await browser.new_context(viewport={"width": width, "height": 844})
            page = await context.new_page()
            console_errors: list[str] = []
            page_errors: list[str] = []
            failed_requests: list[str] = []
            http_errors: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on("requestfailed", lambda request: failed_requests.append(f"{request.url}: {request.failure}"))
            page.on("response", lambda response: http_errors.append(f"{response.status} {response.url}") if response.status >= 400 else None)

            await page.goto(f"{base}/science/book3/?qa={label}-{width}", wait_until="networkidle")
            await page.locator("#nm").fill(f"BROWSER-QA-{width}")
            await page.get_by_role("button", name="開始練習 →").click()
            await page.wait_for_selector(".modegrid")
            dashboard_text = await page.locator("#app").inner_text()
            student_overflow = await page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
            if "每回隨機抽 10 題" not in dashboard_text or "完整 25 題測驗" not in dashboard_text:
                report["errors"].append(f"{width}px: mode labels missing")

            await page.evaluate("window.CLOUD.enabled=false")
            await page.locator(".modecard").nth(0).click()
            practice = await page.evaluate("({mode:session.mode,count:session.ids.length,unique:new Set(session.ids).size})")
            if practice != {"mode": "practice", "count": 10, "unique": 10}:
                report["errors"].append(f"{width}px: bad practice session {practice}")

            await page.evaluate("session.ids.forEach(id=>session.answers[id]=QMAP[id].answer); finishSession()")
            practice_score = int(await page.locator(".score").inner_text())
            if practice_score != 100:
                report["errors"].append(f"{width}px: practice score {practice_score}")

            await page.evaluate(
                "viewDashboard('BROWSER-QA-%d'); startMode(encodeURIComponent('BROWSER-QA-%d'),'full'); "
                "session.ids.forEach(id=>session.answers[id]=QMAP[id].answer); finishSession();" % (width, width)
            )
            full_score = int(await page.locator(".score").inner_text())
            review_cards = await page.locator(".card.tight").count()
            image_result = await page.evaluate(
                """async()=>{const imgs=[...document.querySelectorAll('.source-img')];const failed=[];
                for(const img of imgs){img.loading='eager';try{await img.decode();if(!img.naturalWidth)failed.push(img.src);}catch(e){failed.push(img.src);}}
                return {count:imgs.length,failed};}"""
            )
            if full_score != 100 or review_cards != 25 or image_result != {"count": 25, "failed": []}:
                report["errors"].append(f"{width}px: full test failed score={full_score} cards={review_cards} images={image_result}")

            await page.goto(f"{base}/?qa={label}-{width}", wait_until="networkidle")
            await page.locator("#catalogSearch").fill("第三冊")
            await page.wait_for_timeout(150)
            catalog_text = await page.locator("#resourceGrid").inner_text()
            catalog_overflow = await page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
            if "113–115 會考第三冊理化精選25題" not in catalog_text:
                report["errors"].append(f"{width}px: catalog entry missing")
            await page.screenshot(path=str(OUT / f"book3-{label}-mobile-{width}.png"), full_page=True)

            actionable_console = [item for item in console_errors if not item.startswith("Failed to load resource")]
            actionable_http = [item for item in http_errors if "favicon" not in item]
            report["viewports"][str(width)] = {
                "studentOverflow": student_overflow,
                "catalogOverflow": catalog_overflow,
                "practice": practice,
                "practiceScore": practice_score,
                "fullScore": full_score,
                "reviewCards": review_cards,
                "images": image_result,
                "consoleErrors": actionable_console,
                "pageErrors": page_errors,
                "httpErrors": actionable_http,
                "failedRequests": [item for item in failed_requests if "favicon" not in item],
            }
            if student_overflow or catalog_overflow or actionable_console or page_errors or actionable_http:
                report["errors"].append(
                    f"{width}px: overflow/student={student_overflow}, catalog={catalog_overflow}, console={actionable_console}, page={page_errors}, http={actionable_http}"
                )
            await context.close()

        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()
        teacher_errors: list[str] = []
        page.on("pageerror", lambda error: teacher_errors.append(str(error)))
        await page.goto(f"{base}/science/book3/teacher.html?qa={label}", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        teacher_text = await page.locator("#app").inner_text()
        report["teacher"] = {
            "loginRendered": "教師版雲端登入" in teacher_text,
            "localFallback": "本機匯入模式" in teacher_text,
            "pageErrors": teacher_errors,
        }
        if not report["teacher"]["loginRendered"] or not report["teacher"]["localFallback"] or teacher_errors:
            report["errors"].append(f"teacher page failed: {report['teacher']}")

        await page.goto(f"{base}/teacher.html?qa={label}", wait_until="networkidle")
        teacher_hub_text = await page.locator("body").inner_text()
        card_count = await page.locator("#cards article").count()
        report["teacherHub"] = {"entryPresent": "第三冊理化25題" in teacher_hub_text, "cards": card_count}
        if not report["teacherHub"]["entryPresent"] or card_count != 16:
            report["errors"].append(f"teacher hub failed: {report['teacherHub']}")
        await context.close()
        await browser.close()

    return report


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8765")
    parser.add_argument("--label", default="local")
    args = parser.parse_args()
    report = await run(args.base, args.label)
    path = OUT / f"book3-browser-qa-{args.label}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"base": report["base"], "viewports": report["viewports"], "teacher": report["teacher"], "teacherHub": report["teacherHub"], "errors": report["errors"]}, ensure_ascii=False))
    print(f"report={path}")
    raise SystemExit(1 if report["errors"] else 0)


if __name__ == "__main__":
    asyncio.run(main())
