import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://rutube.ru"
SERIES_ID = "695548"
OUTPUT_FILE = "links.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def extract_title(a):
    # 1. title у <a>
    title = a.attrs.get("title", "").strip()
    if title:
        return title

    # 2. img alt / title
    img = a.find("img")
    if img:
        title = img.attrs.get("alt", "").strip()
        if title:
            return title
        title = img.attrs.get("title", "").strip()
        if title:
            return title

    # 3. aria-label у вложенных элементов
    for tag in a.find_all(True):
        title = tag.attrs.get("aria-label", "").strip()
        if title:
            return title

    return "Без названия"

def get_page_url(page: int) -> str:
    if page == 1:
        return f"{BASE_URL}/metainfo/tv/{SERIES_ID}/"
    return f"{BASE_URL}/metainfo/tv/{SERIES_ID}/page-{page}/"

def parse_page(page: int):
    url = get_page_url(page)
    print(f"Парсим страницу {page}: {url}")

    r = requests.get(url, headers=HEADERS)
    if r.status_code == 404:
        return None

    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    cards = soup.find_all(
        "a",
        class_="wdp-link-module__link wdp-card-poster-module__posterWrapper",
        href=True
    )

    results = []

    for a in cards:
        href = a["href"]
        if not href.startswith("/video/"):
            continue

        title = extract_title(a)


        results.append((title, BASE_URL + href))

    return results




def main():
    page = 1
    all_links = []
    seen = set()

    while True:
        data = parse_page(page)
        if not data:
            break

        added = 0
        for title, url in data:
            if url not in seen:
                seen.add(url)
                all_links.append((title, url))
                added += 1

        print(f"Добавлено: {added}")

        if added == 0:
            break

        page += 1
        time.sleep(1)

    print(f"\nИТОГО видео: {len(all_links)}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for i, (title, url) in enumerate(all_links, start=1):
            f.write(f"# {i}. {title}\n")
            f.write(url + "\n\n")

    print(f"Сохранено в {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
