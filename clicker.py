import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright


TARGET_URL = "https://student.iclicker.com"


def write_status_line(message: str) -> None:
    """Render a single-line status update without growing the terminal."""
    padded_message = message.ljust(write_status_line.last_length)
    sys.stdout.write("\r" + padded_message)
    sys.stdout.flush()
    write_status_line.last_length = max(write_status_line.last_length, len(message))


write_status_line.last_length = 0


async def monitor_and_click(
    selector: str,
    poll_seconds: float,
    headless: bool,
    state_file: str,
    geolocation: dict[str, float] | None,
) -> None:
    state_path = Path(state_file).expanduser()
    state_exists = state_path.is_file()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context_kwargs = {"storage_state": str(state_path)} if state_exists else {}
        if geolocation is not None:
            context_kwargs["geolocation"] = geolocation
            context_kwargs["permissions"] = ["geolocation"]
        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()

        if state_exists:
            print(f"Loaded cached login state from {state_path}.")
        else:
            print(f"No cached login state found at {state_path}.")

        if geolocation is not None:
            print(
                "Using spoofed geolocation: "
                f"{geolocation['latitude']}, {geolocation['longitude']} "
                f"(accuracy {geolocation['accuracy']}m)."
            )

        print(f"Opening {TARGET_URL} ...")
        await page.goto(TARGET_URL)

        if state_exists:
            input("Press Enter to start monitoring...")
        else:
            input("Log in manually, then press Enter to save login state and start monitoring...")
            state_path.parent.mkdir(parents=True, exist_ok=True)
            await context.storage_state(path=str(state_path))
            print(f"Saved login state to {state_path}.")
            await page.goto(TARGET_URL)

        locator = page.locator(selector)
        was_visible = False

        try:
            while True:
                checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                write_status_line(f"Last checked: {checked_at}")

                try:
                    is_visible = await locator.is_visible()
                except Exception:
                    write_status_line(
                        f"Last checked: {checked_at} | visibility check failed"
                    )
                    is_visible = False

                if is_visible and not was_visible:
                    try:
                        await locator.click()
                        write_status_line(
                            f"Last checked: {checked_at} | clicked {selector}"
                        )
                        was_visible = True
                    except Exception:
                        write_status_line(
                            f"Last checked: {checked_at} | click failed"
                        )
                elif not is_visible:
                    was_visible = False

                await asyncio.sleep(poll_seconds)
        finally:
            sys.stdout.write("\n")
            sys.stdout.flush()
            await browser.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Open a browser, let you log in, then poll for a selector and click it when it appears."
    )
    parser.add_argument(
        "--selector",
        default="#multiple-choice-a",
        help="CSS selector for the element to wait for and click. Defaults to the iClicker A answer button.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=3.0,
        help="Delay between visibility checks.",
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
    parser.add_argument(
        "--latitude",
        type=float,
        help="Spoofed geolocation latitude for sites using the browser Geolocation API.",
    )
    parser.add_argument(
        "--longitude",
        type=float,
        help="Spoofed geolocation longitude for sites using the browser Geolocation API.",
    )
    parser.add_argument(
        "--accuracy",
        type=float,
        default=100.0,
        help="Spoofed geolocation accuracy in meters. Defaults to 100.",
    )
    args = parser.parse_args()

    if (args.latitude is None) != (args.longitude is None):
        parser.error("Pass both --latitude and --longitude to enable geolocation spoofing.")
    if args.latitude is not None and not -90 <= args.latitude <= 90:
        parser.error("--latitude must be between -90 and 90.")
    if args.longitude is not None and not -180 <= args.longitude <= 180:
        parser.error("--longitude must be between -180 and 180.")
    if args.accuracy < 0:
        parser.error("--accuracy must be non-negative.")

    return args


if __name__ == "__main__":
    args = parse_args()
    geolocation = None
    if args.latitude is not None and args.longitude is not None:
        geolocation = {
            "latitude": args.latitude,
            "longitude": args.longitude,
            "accuracy": args.accuracy,
        }
    asyncio.run(
        monitor_and_click(
            selector=args.selector,
            poll_seconds=args.poll_seconds,
            headless=args.headless,
            state_file=args.state_file,
            geolocation=geolocation,
        )
    )
