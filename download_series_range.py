import yt_dlp
import re
import os
import sys

LINKS_FILE = "links.txt"
DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

SERIES_REGEX = re.compile(r"(\d+)\s*серия", re.IGNORECASE)


def load_links():
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]


def extract_series_number(title: str):
    match = SERIES_REGEX.search(title)
    if match:
        return int(match.group(1))
    return None


def preload_metadata(links):
    series_map = {}

    ydl_opts = {
        "skip_download": True,
        "quiet": False,
        "socket_timeout": 15,
        "retries": 3,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for idx, url in enumerate(links, start=1):
            print(f"[{idx}/{len(links)}] Метаданные: {url}")

            try:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "").strip()

                if not title:
                    print("  ⚠ пустой title — пропуск")
                    continue

                series_number = extract_series_number(title)

                if series_number is None:
                    print(f"  ⚠ номер серии не найден: {title}")
                    continue

                if series_number not in series_map:
                    series_map[series_number] = {
                        "url": url,
                        "title": title
                    }
                    print(f"  ✔ серия {series_number}: {title}")
                else:
                    print(f"  ⚠ дубликат серии {series_number}, пропуск")

            except Exception as e:
                print(f"  ❌ ошибка: {e}")

    return series_map


def download_selected(series_map, start, end):
    # Создаём временный подкласс, чтобы подменить outtmpl-переменную
    class SeriesNumberPP:
        def __init__(self, series_num):
            self.series_num = series_num

        def __call__(self, info_dict):
            info_dict['series_number'] = self.series_num
            return info_dict
   
    ydl_opts = {
        'format': 'best[height<=480]',
        'outtmpl': os.path.join(DOWNLOAD_DIR, "%(series_number)03d.%(ext)s"),
        'quiet': True
    }

    for series in sorted(series_map):
        if start <= series <= end:
            entry = series_map[series]
            url = entry["url"]
            print(f"\n⬇ Скачиваем серию {series}: {entry['title']} (480p)")

            # Извлекаем info_dict
            with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as tmp_ydl:
                info = tmp_ydl.extract_info(url, download=False)

            # Добавляем series_number
            info['series_number'] = series

            # Скачиваем с обогащённым info_dict
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.process_info(info)


if __name__ == "__main__":
    links = load_links()
    print(f"Найдено ссылок: {len(links)}")

    series_map = preload_metadata(links)

    if not series_map:
        print("\n❌ Ни одной серии определить не удалось.")
        sys.exit(1)

    print("\nНайденные серии:")
    for s in sorted(series_map):
        print(f"{s}: {series_map[s]['title']}")

    rng = input("\nВведите диапазон серий (например 93-133): ").strip()
    start, end = map(int, rng.split("-"))

    download_selected(series_map, start, end)
