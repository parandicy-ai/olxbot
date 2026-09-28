"""
OLX -> Telegram бот.
Следит за страницей поиска OLX и отправляет новые объявления в чат.

Настройка через переменные окружения:
  BOT_TOKEN   - токен бота от @BotFather
  CHAT_ID     - ID чата/группы/канала, куда слать объявления
  SEARCH_URL  - ссылка на поиск OLX (со всеми фильтрами)
  INTERVAL    - как часто проверять, в секундах (по умолчанию 60)
"""
import html
import json
import os
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
# Можно несколько ссылок через запятую (например, Ташкент и область)
SEARCH_URLS = [u.strip() for u in os.environ["SEARCH_URL"].split(",") if u.strip()]
INTERVAL = int(os.environ.get("INTERVAL", "60"))
SEEN_FILE = "seen.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
}


def with_newest_first(url: str) -> str:
    """Добавляем сортировку «сначала новые»."""
    if "order" in url:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}search%5Border%5D=created_at%3Adesc"


def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set) -> None:
    # храним последние 2000 id, чтобы файл не рос бесконечно
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen)[-2000:], f)


def fetch_ads(search_url: str) -> list[dict]:
    resp = requests.get(with_newest_first(search_url), headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    p = urlparse(search_url)
    base = f"{p.scheme}://{p.netloc}"

    ads = []
    for card in soup.select('div[data-cy="l-card"]'):
        a = card.find("a", href=True)
        if not a:
            continue
        url = urljoin(base, a["href"]).split("#")[0]
        title_el = card.find(["h4", "h6"])
        price_el = card.select_one('[data-testid="ad-price"]')
        loc_el = card.select_one('[data-testid="location-date"]')
        ads.append(
            {
                "id": card.get("id") or url,
                "url": url,
                "title": title_el.get_text(" ", strip=True) if title_el else "Без названия",
                "price": price_el.get_text(" ", strip=True) if price_el else "цена не указана",
                "location": loc_el.get_text(" ", strip=True) if loc_el else "",
            }
        )
    return ads


def send_to_telegram(ad: dict) -> None:
    text = (
        f"🆕 <b>{html.escape(ad['title'])}</b>\n"
        f"💰 {html.escape(ad['price'])}\n"
        f"📍 {html.escape(ad['location'])}\n"
        f"🔗 {ad['url']}"
    )
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=30,
    )
    r.raise_for_status()


def main() -> None:
    seen = load_seen()
    first_run = not seen
    print("Бот запущен. Слежу за:", *SEARCH_URLS, sep="\n  ")

    while True:
        try:
            ads = []
            for url in SEARCH_URLS:
                try:
                    ads.extend(fetch_ads(url))
                except Exception as e:
                    print("Ошибка загрузки", url, "->", e)
                time.sleep(2)
            # убираем дубли, если объявление попало в обе выдачи
            ads = list({a["id"]: a for a in ads}.values())
            new_ads = [a for a in ads if a["id"] not in seen]

            if first_run:
                # при первом запуске просто запоминаем текущие объявления
                print(f"Первый запуск: запомнил {len(ads)} объявлений")
                first_run = False
            else:
                for ad in reversed(new_ads):  # от старых к новым
                    send_to_telegram(ad)
                    print("Отправлено:", ad["title"])
                    time.sleep(1)

            seen.update(a["id"] for a in ads)
            save_seen(seen)
        except Exception as e:
            print("Ошибка:", e)

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
