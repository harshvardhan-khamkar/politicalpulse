from __future__ import annotations

import argparse
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://www.eci.gov.in/EBooks/ge_2024_results_ebook/files/mobile/{page}.jpg"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "ebook"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def download_page(page: int, output_dir: Path, overwrite: bool = False) -> bool:
    output_path = output_dir / f"{page}.jpg"
    if output_path.exists() and not overwrite:
        print(f"[skip] Page {page} already exists: {output_path.name}")
        return True

    url = BASE_URL.format(page=page)
    request = Request(url, headers=DEFAULT_HEADERS)

    try:
        with urlopen(request, timeout=30) as response:
            content_type = response.headers.get("Content-Type", "")
            if "image" not in content_type.lower():
                print(f"[fail] Page {page} did not return an image: {content_type or 'unknown'}")
                return False

            output_path.write_bytes(response.read())
            print(f"[ok] Downloaded page {page} -> {output_path.name}")
            return True
    except HTTPError as exc:
        print(f"[http {exc.code}] Page {page} not downloaded")
        return False
    except URLError as exc:
        print(f"[network] Page {page} failed: {exc.reason}")
        return False
    except Exception as exc:
        print(f"[error] Page {page} failed: {exc}")
        return False


def download_with_browser(
    start: int,
    end: int | None,
    output_dir: Path,
    overwrite: bool = False,
    delay: float = 0.2,
    max_misses: int = 3,
    browser_channel: str = "chrome",
) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit(
            "Playwright is not installed. Install it with: pip install playwright"
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)

    page_number = start
    misses = 0
    downloaded = 0

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=browser_channel, headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 900},
            user_agent=DEFAULT_HEADERS["User-Agent"],
        )

        while True:
            if end is not None and page_number > end:
                break

            output_path = output_dir / f"{page_number}.jpg"
            if output_path.exists() and not overwrite:
                print(f"[skip] Page {page_number} already exists: {output_path.name}")
                downloaded += 1
                misses = 0
                page_number += 1
                if delay > 0:
                    time.sleep(delay)
                continue

            url = BASE_URL.format(page=page_number)
            try:
                response = page.goto(url, wait_until="load", timeout=60000)
                if response is None:
                    print(f"[fail] Page {page_number} returned no response")
                    misses += 1
                elif response.status != 200:
                    print(f"[http {response.status}] Page {page_number} not downloaded")
                    misses += 1
                else:
                    body = response.body()
                    output_path.write_bytes(body)
                    print(f"[ok] Downloaded page {page_number} -> {output_path.name}")
                    downloaded += 1
                    misses = 0
            except Exception as exc:
                print(f"[error] Page {page_number} failed in browser mode: {exc}")
                misses += 1

            if end is None and misses >= max_misses:
                print(f"[stop] Reached {misses} consecutive missing/failed pages at page {page_number}.")
                break

            page_number += 1
            if delay > 0:
                time.sleep(delay)

        browser.close()

    return downloaded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download ECI e-book page images into the local ebook folder."
    )
    parser.add_argument("--start", type=int, default=1, help="First page number to download")
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="Last page number to download. If omitted, auto-stop after consecutive missing pages.",
    )
    parser.add_argument(
        "--max-misses",
        type=int,
        default=3,
        help="When --end is omitted, stop after this many consecutive failed pages.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay in seconds between requests.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the page images should be saved.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite files that already exist.",
    )
    parser.add_argument(
        "--mode",
        choices=["http", "browser"],
        default="http",
        help="Download mode. Use 'browser' when the site blocks direct HTTP downloads.",
    )
    parser.add_argument(
        "--browser-channel",
        choices=["chrome", "msedge"],
        default="chrome",
        help="Installed browser to use for browser mode.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "browser":
        downloaded = download_with_browser(
            start=args.start,
            end=args.end,
            output_dir=output_dir,
            overwrite=args.overwrite,
            delay=args.delay,
            max_misses=args.max_misses,
            browser_channel=args.browser_channel,
        )
        print(f"[done] Downloaded {downloaded} page(s) into {output_dir}")
        return 0

    page = args.start
    misses = 0
    downloaded = 0

    while True:
        if args.end is not None and page > args.end:
            break

        ok = download_page(page, output_dir, overwrite=args.overwrite)
        if ok:
            downloaded += 1
            misses = 0
        else:
            misses += 1
            if args.end is None and misses >= args.max_misses:
                print(f"[stop] Reached {misses} consecutive missing/failed pages at page {page}.")
                break

        page += 1
        if args.delay > 0:
            time.sleep(args.delay)

    print(f"[done] Downloaded {downloaded} page(s) into {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
