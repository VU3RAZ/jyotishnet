# SPDX-License-Identifier: AGPL-3.0-or-later
"""The slider with the API stopped (M3.5): charts, running periods and the ribbon's
boundary marks all come from the browser engine (Swiss Ephemeris as WebAssembly in a
Web Worker), and the page never asks the API for them.

Run with only the web app up (no API on port 8000):

    cd web && npx next start -p 3000 &
    python web/e2e/offline.py [http://localhost:3000]

Equality with the API's numbers is checked by web/e2e/engine_parity.py.
"""

import asyncio
import sys
import time
from urllib.parse import urlparse

from playwright.async_api import async_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
SLIDER_PATHS = ("/api/v1/chart", "/api/v1/dasha", "/api/v1/boundaries")


async def main() -> int:
    asked: list[str] = []
    page_errors: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1320, "height": 1000})
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("request", lambda r: asked.append(r.url) if urlparse(r.url).path in SLIDER_PATHS else None)

        def check(ok: bool, what: str) -> None:
            if not ok:
                print(f"FAIL {what}")
                raise SystemExit(1)
            print(f"ok  {what}")

        await page.goto(URL)
        await page.wait_for_selector(".chart-svg")
        await page.wait_for_selector("[data-engine=browser]")
        check(True, "chart drawn by the browser engine")

        # Scrub the ribbon across four hours, one value per frame, and watch the Lagna.
        lagnas = set()
        t0 = time.perf_counter()
        for v in range(-7200, 7201, 240):
            await page.evaluate("""(v) => { const i = document.querySelector('#ribbon-input');
                const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                set.call(i, String(v)); i.dispatchEvent(new Event('input', {bubbles: true})); }""", v)
            await page.wait_for_timeout(40)
            lagnas.add(await page.locator(".chart-svg >> nth=0").locator(".sign-num >> nth=0").text_content())
        per_step = (time.perf_counter() - t0) / 61
        check(len(lagnas) >= 2, f"Lagna follows the slider ({sorted(lagnas)}; {per_step * 1000:.0f} ms a step)")

        await page.wait_for_selector(".ribbon-ticks .tick:not(.zero)", state="attached")
        check(True, "boundary marks on the ribbon")
        await page.fill(".dasha-date input", "1900-06-01")   # the preset was born in 1869
        await page.wait_for_selector(".dasha-lord")
        check(await page.locator(".dasha-lord").count() == 3, "running maha, antar and pratyantar")
        check(not await page.locator(".service-error").count(), "no service error shown")
        check(not asked, f"no slider request reached the API ({asked[:3]})")
        check(not page_errors, "no page errors" + (f": {page_errors[:3]}" if page_errors else ""))
        await browser.close()
    print("offline test passed")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
