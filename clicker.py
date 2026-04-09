import argparse
import asyncio
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright


async def monitor_and_click(
    selector: str,
    wait_timeout_ms: int,
    poll_seconds: float,
    headless: bool,
    state_file: str,
) -> None:
    state_path = Path(state_file).expanduser()
    state_exists = state_path.is_file()
    target_url = "https://student.iclicker.com"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context_kwargs = {"storage_state": str(state_path)} if state_exists else {}
        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()

        if state_exists:
            print(f"Loaded cached login state from {state_path}.")
        else:
            print(f"No cached login state found at {state_path}.")

        print(f"Opening {target_url} ...")
        await page.goto(target_url)

        if not state_exists:
            input("Log in manually, then press Enter to save login state and start monitoring...")
            state_path.parent.mkdir(parents=True, exist_ok=True)
            await context.storage_state(path=str(state_path))
            print(f"Saved login state to {state_path}.")
            print(f"Opening {target_url} ...")
            await page.goto(target_url)

        try:
            while True:
                try:
                    button = await page.wait_for_selector(selector, timeout=wait_timeout_ms)
                    print(f"Found {selector}. Clicking...")
                    await button.click()
                except PlaywrightTimeoutError:
                    print(f"Not found yet ({selector}). Checking again in {poll_seconds}s...")
                await asyncio.sleep(poll_seconds)
        finally:
            await context.close()
            await browser.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Open a browser, let you log in, then poll for a selector and click it."
    )
    parser.add_argument(
        "--selector",
        default="#multiple-choice-a",
        help="CSS selector for the element to wait for and click. Defaults to the iClicker A answer button.",
    )
    parser.add_argument(
        "--wait-timeout-ms",
        type=int,
        default=5000,
        help="Max time (ms) to wait per poll attempt before retrying.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=3.0,
        help="Delay between retries when the selector is not found.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run headless (default is visible browser for manual login).",
    )
    parser.add_argument(
        "--state-file",
        default="playwright_state.json",
        help="Path to the Playwright storage state JSON used to cache login.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(
        monitor_and_click(
            selector=args.selector,
            wait_timeout_ms=args.wait_timeout_ms,
            poll_seconds=args.poll_seconds,
            headless=args.headless,
            state_file=args.state_file,
        )
    )
