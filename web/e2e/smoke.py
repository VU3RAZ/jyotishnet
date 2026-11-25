# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Rahul Sathe
"""Browser smoke test for the workbench: fails on any page error.

Needs the API and the web app running (scripts/start.sh, or uvicorn + next start)
and Python Playwright with a Chromium:  pip install playwright && playwright install chromium

    python web/e2e/smoke.py [http://localhost:3000]
"""

import asyncio
import sys

from playwright.async_api import async_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
VARGAS = ["2", "3", "4", "7", "10", "12", "16", "20", "24", "27", "30", "40", "45", "60", "9"]


async def main() -> int:
    errors: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1320, "height": 1000})
        page.on("pageerror", lambda e: errors.append(f"page error: {e}"))
        page.on("console", lambda m: errors.append(f"console: {m.text}") if m.type == "error" else None)

        async def step(name: str, wait_ms: int = 900):
            await page.wait_for_timeout(wait_ms)
            if errors:
                print(f"FAIL at {name}:\n  " + "\n  ".join(errors[:5]))
                raise SystemExit(1)
            print(f"ok  {name}")

        await page.goto(URL)
        await page.wait_for_selector(".chart-svg")
        await step("load", 1500)

        for style in ["South Indian", "North Indian"]:
            for v in VARGAS:
                await page.select_option(".varga-pick select", v)
                await step(f"{style} D{v}", 600)
            await page.click(f"text={style}")

        # Move the ribbon, then pick a varga while charts are refreshing.
        await page.evaluate("""() => { const i = document.querySelector('#ribbon-input');
            const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            for (const v of ['300', '-600', '900']) { set.call(i, v); i.dispatchEvent(new Event('input', {bubbles: true})); } }""")
        await page.select_option(".varga-pick select", "60")
        await step("slider + D60 while loading")

        # Multi-varga canvas (M3.2): linked highlighting, varga sets, the slider.
        await page.click("[role=tab]:has-text('Vargas')")
        await page.wait_for_function("document.querySelectorAll('.canvas-grid .chart-svg').length === 10")
        await page.click(".follow-chips button:has-text('Ju')")
        await page.wait_for_function("document.querySelectorAll('.canvas-grid .planet.linked').length === 10")
        await page.wait_for_selector("caption:has-text('Jupiter in each varga')")
        await page.click(".canvas-controls button:has-text('Shodashavarga')")
        await page.wait_for_function("document.querySelectorAll('.canvas-grid .chart-svg').length === 16")
        await page.evaluate("""() => { const i = document.querySelector('#ribbon-input');
            const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            for (const v of ['-1200', '400']) { set.call(i, v); i.dispatchEvent(new Event('input', {bubbles: true})); } }""")
        await page.wait_for_function("document.querySelectorAll('.canvas-grid .planet.linked').length === 16")
        await page.hover(".canvas-grid .chart-card:nth-child(3) .planet >> nth=0")
        await step("varga canvas", 1200)

        for tab in ["Yogas", "Ashtakavarga", "Strengths", "Transits", "Dashas", "Positions"]:
            await page.click(f"[role=tab]:has-text('{tab}')")
            await step(f"tab {tab}", 1500)
            if tab == "Yogas":
                await page.select_option(".yoga-options label:has-text('Gajakesari') select", "phaladeepika")
                await page.select_option(".yoga-options label:has-text('Strong Lagna') select", "shadbala")
                await page.wait_for_selector(".yoga-group")
            if tab == "Strengths":
                await page.wait_for_selector("caption:has-text('Bhava bala')", state="attached")
                await page.wait_for_selector("caption:has-text('Vimshopaka')", state="attached")
                await page.select_option(".vimshopaka select", "jhora")
                await step("vimshopaka JHora weights", 900)
                await page.wait_for_selector("caption:has-text('Avasthas')", state="attached")
            if tab == "Transits":
                await page.wait_for_selector("caption:has-text('Gochara')", state="attached")
            if tab == "Positions":
                await page.click("summary:has-text('Special lagnas')")
                await page.wait_for_selector("th:has-text('Yama Ghantaka')")
                await page.click("summary:has-text('Chara karakas and arudhas')")
                await page.wait_for_selector("th:has-text('Of house')")
                await page.click("summary:has-text('Panchanga')")
                await page.wait_for_selector("th:has-text('Rahu kala')")
                await page.wait_for_selector("th:has-text('Janma ghatis')")
        for system in ["Ashtottari", "Yogini", "Vimshottari"]:
            await page.click(f"[role=tab]:has-text('Dashas')")
            await page.click(f"text={system}")
            await step(f"dasha {system}", 1200)
        for rasi in ["chara", "narayana", "sudasa", "drig", "shoola", "brahma", "padanaathamsa", "varnada"]:
            await page.select_option(".rasi-pick select", rasi)
            await page.wait_for_selector(".tl-seg")
            await step(f"rasi dasha {rasi}", 1200)

        await page.click("text=Transits")
        await step("transit mode", 1500)
        await page.click("text=±12 years")
        await step("transit ±12 years")
        await page.click("text=Rectify birth time")
        await step("back to rectify", 1500)

        # Time-zone warning in the birth form (1943 Delhi at +5:30: war time was +6:30).
        await page.fill(".birth-form input[type=date]", "1943-05-01")
        await page.fill(".birth-form label:has-text('Latitude') input", "28.61")
        await page.fill(".birth-form label:has-text('Longitude') input", "77.21")
        await page.fill(".birth-form label:has-text('UTC offset') input", "5.5")
        await page.wait_for_selector(".form-warning", timeout=5000)
        text = await page.inner_text(".form-warning")
        if "war time" not in text:
            print(f"FAIL: expected a war-time warning, got {text!r}")
            raise SystemExit(1)
        await page.fill(".birth-form label:has-text('UTC offset') input", "6.5")
        await page.wait_for_selector(".form-warning", state="detached", timeout=5000)
        await step("birth form time-zone warning")

        # Saved charts and notes (M3.1): save, annotate, open another, reopen, delete.
        page.on("dialog", lambda d: asyncio.ensure_future(d.accept()))
        await page.click("summary:has-text('Saved charts and notes')")
        await page.click("button:has-text('Save this chart')")
        await page.wait_for_selector(".library-list li[aria-current=true]")
        saved = (await page.inner_text("h1")).strip()
        await page.fill("textarea[aria-label='New note']", "Smoke-test note")
        await page.click("button:has-text('Add note')")
        await page.wait_for_selector(".note-list p:has-text('Smoke-test note')")
        await step("save chart + note")
        await page.select_option(".field.preset select", index=2)
        await page.wait_for_function("(s) => document.querySelector('h1').innerText.trim() !== s", arg=saved)
        await page.click(f".library-open:has-text('{saved}')")
        await page.wait_for_function("(s) => document.querySelector('h1').innerText.trim() === s", arg=saved,
                                     timeout=5000)
        await page.wait_for_selector(".note-list p:has-text('Smoke-test note')")
        await step("reopen saved chart")
        await page.click(f".library-list li[aria-current=true] button:has-text('Delete')")
        await page.wait_for_selector(".library-list li[aria-current=true]", state="detached")
        await step("delete saved chart")
        await browser.close()
    print("smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
