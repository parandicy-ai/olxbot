"""
Один проход проверки OLX (для запуска по расписанию в GitHub Actions).
Использует функции из bot.py.
"""
import time

from bot import SEARCH_URLS, fetch_ads, load_seen, save_seen, send_to_telegram


def main() -> None:
    seen = load_seen()
    first_run = not seen

    ads = []
    for url in SEARCH_URLS:
        try:
            ads.extend(fetch_ads(url))
        except Exception as e:
            print("Ошибка загрузки", url, "->", e)
        time.sleep(2)

    ads = list({a["id"]: a for a in ads}.values())
    new_ads = [a for a in ads if a["id"] not in seen]

    if first_run:
        print(f"Первый запуск: запомнил {len(ads)} объявлений, ничего не отправляю")
    else:
        for ad in reversed(new_ads):  # от старых к новым
            send_to_telegram(ad)
            print("Отправлено:", ad["title"])
            time.sleep(1)
        print(f"Новых объявлений: {len(new_ads)}")

    seen.update(a["id"] for a in ads)
    save_seen(seen)


if __name__ == "__main__":
    main()
