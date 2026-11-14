
import hashlib
import requests

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright



def extract_content(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    for element in soup([
        "script",
        "style",
        "noscript",
        "header",
        "footer"
    ]):
        element.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""

    content = soup.get_text(separator=" ", strip=True)

    # Normalize whitespace
    import re
    content = re.sub(r"\s+", " ", content).strip()

    content_hash = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    return {
        "title": title,
        "content": content,
        "content_hash": content_hash
    }


def fetch_with_requests(url: str):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()
    return response.text


def fetch_with_playwright(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        try:
            page = browser.new_page()
            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            if response and response.status >= 400:
                raise RuntimeError(
                    f"Browser request returned HTTP {response.status}"
                )

            return page.content()

        finally:
            browser.close()



def fetch_website_content(url: str) -> dict:

    try:
        html = fetch_with_requests(url)
        method = "requests"

    except requests.RequestException:
        try:
            html = fetch_with_playwright(url)
            method = "playwright"

        except Exception as exc:
            raise WebsiteAccessError(
                f"Website is not accessible through our crawler: {exc}"
            ) from exc

    result = extract_content(html)

    return {
        "url": url,
        "title": result["title"],
        "content": result["content"],
        "content_hash": result["content_hash"],
        "method": method
    }

class WebsiteAccessError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        self.message = message
        self.status_code = status_code
        super().__init__(message)
