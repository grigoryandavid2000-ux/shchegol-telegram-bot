from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
LOCAL_MENU_JSON_PATH = BASE_DIR / "assets" / "menu-items-full.json"
SITE_MENU_JSON_PATH = PROJECT_DIR / "assets" / "menu-items-full.json"
MENU_JSON_PATH = LOCAL_MENU_JSON_PATH if LOCAL_MENU_JSON_PATH.exists() else SITE_MENU_JSON_PATH
APP_VERSION = "2026-06-15-cart-site"


CATEGORY_ORDER = ["coffee", "dessert", "food", "seasonal", "cold", "noncoffee"]

CATEGORY_META = {
    "coffee": {"title": "Кофе", "emoji": "☕"},
    "dessert": {"title": "Десерты", "emoji": "🍰"},
    "food": {"title": "Еда", "emoji": "🍽"},
    "seasonal": {"title": "Сезонное", "emoji": "🍂"},
    "cold": {"title": "Холодные напитки", "emoji": "🧊"},
    "noncoffee": {"title": "Не кофе", "emoji": "🍵"},
}

EXPECTED_COUNTS = {
    "coffee": 9,
    "dessert": 13,
    "food": 3,
    "seasonal": 6,
    "cold": 5,
    "noncoffee": 5,
}


BRANCHES = {
    "krasno": {
        "title": "6-я Красноармейская",
        "address": "6-я Красноармейская ул., 1, Санкт-Петербург",
        "hours": "ежедневно 10:00-20:00",
        "phone": "+7 (911) 741-22-48",
        "yandex_url": "https://yandex.ru/maps/org/shchegol/66748634725/",
        "yandex_reviews_url": "https://yandex.ru/maps/org/shchegol/66748634725/reviews/",
        "dgis_url": "https://2gis.ru/spb/branches/70000001032493385/firm/70000001092837189/",
        "dgis_reviews_url": "https://2gis.ru/spb/branches/70000001032493385/firm/70000001092837189/",
    },
    "nevsky": {
        "title": "Невский проспект",
        "address": "Невский просп., 46, Санкт-Петербург, 2 этаж",
        "hours": "ежедневно 10:00-22:00",
        "phone": "+7 (911) 741-22-48",
        "yandex_url": "https://yandex.ru/maps/org/shchegol/149799678053/",
        "yandex_reviews_url": "https://yandex.ru/maps/org/shchegol/149799678053/reviews/?indoorLevel=1",
        "dgis_url": "https://2gis.ru/spb/firm/70000001063218096",
        "dgis_reviews_url": "https://2gis.ru/spb/firm/70000001063218096",
    },
    "radish": {
        "title": "Улица Радищева",
        "address": "ул. Радищева, 38, Санкт-Петербург",
        "hours": "пн-пт 09:00-21:00, сб-вс 10:00-21:00",
        "phone": "+7 (911) 157-21-87",
        "yandex_url": "",
        "yandex_reviews_url": "",
        "dgis_url": "https://2gis.ru/spb/branches/70000001032493385/firm/70000001032493386/",
        "dgis_reviews_url": "https://2gis.ru/spb/branches/70000001032493385/firm/70000001032493386/",
    },
}

SOCIAL_LINKS = {
    "Instagram": "https://www.instagram.com/schegolcoffee/",
}

SITE_URL = "https://grigoryandavid2000-ux.github.io/shchegol-coffee-site/"

ABOUT_TEXT = (
    "<b>ℹ️ О кофейне «Щегол»</b>\n\n"
    "«Щегол» — городская кофейня в Санкт-Петербурге с тремя филиалами: "
    "у Технологического института, на Невском проспекте и на улице Радищева.\n\n"
    "В меню собраны кофе, десерты, завтраки, холодные и сезонные напитки. "
    "Через бота можно спокойно посмотреть позиции, собрать предзаказ и выбрать филиал для самовывоза.\n\n"
    "По фотографиям и карточкам заведений видно узнаваемую атмосферу бренда: зелёный цвет, "
    "журналы, спокойный интерьер, витрина и формат кофейни, куда можно забежать за кофе "
    "или остаться за столиком.\n\n"
    "<b>☕ Почему гости выбирают «Щегол»</b>\n\n"
    "• кофе с собой и напитки в зале\n"
    "• сезонные напитки\n"
    "• десерты и простая еда\n"
    "• спокойная городская атмосфера\n"
    "• несколько удобных филиалов в Петербурге\n"
    "• возможность собрать предзаказ через бота"
)


COFFEE_OPTIONS = {
    "volumes": [
        {"key": "200", "title": "200 мл", "price_delta": 0},
        {"key": "300", "title": "300 мл", "price_delta": 50},
        {"key": "400", "title": "400 мл", "price_delta": 90},
    ],
    "milk": [
        {"key": "whole", "title": "цельное молоко", "price_delta": 0},
        {"key": "lactose_free", "title": "безлактозное молоко", "price_delta": 0},
        {"key": "oat", "title": "овсяное молоко", "price_delta": 80},
        {"key": "coconut", "title": "кокосовое молоко", "price_delta": 80},
        {"key": "banana", "title": "банановое молоко", "price_delta": 80},
    ],
    "sugar": [
        {"key": "none", "title": "без сахара", "price_delta": 0},
        {"key": "sugar", "title": "с сахаром", "price_delta": 0},
        {"key": "less", "title": "поменьше сахара", "price_delta": 0},
    ],
    "additives": [
        {"key": "vanilla", "title": "ванильный сироп", "price_delta": 50},
        {"key": "caramel", "title": "карамельный сироп", "price_delta": 50},
        {"key": "nut", "title": "ореховый сироп", "price_delta": 50},
        {"key": "espresso", "title": "дополнительный эспрессо", "price_delta": 90},
    ],
}

OPTION_GROUPS = {
    "volume": [
        {"key": "200", "title": "200 мл", "price_delta": 0},
        {"key": "300", "title": "300 мл", "price_delta": 50},
        {"key": "400", "title": "400 мл", "price_delta": 90},
    ],
    "milk": COFFEE_OPTIONS["milk"],
    "sugar": [
        {"key": "none", "title": "без сахара", "price_delta": 0},
        {"key": "sugar", "title": "с сахаром", "price_delta": 0},
        {"key": "less", "title": "поменьше сахара", "price_delta": 0},
        {"key": "one", "title": "1 стик сахара", "price_delta": 0},
        {"key": "two", "title": "2 стика сахара", "price_delta": 0},
        {"key": "three", "title": "3 стика сахара", "price_delta": 0},
    ],
    "additives": COFFEE_OPTIONS["additives"],
}

STEP_TITLES = {
    "volume": "Выберите объём",
    "milk": "Какое молоко?",
    "sugar": "Сколько сахара?",
    "additives": "Добавки нужны? Можно выбрать несколько.",
    "quantity": "Сколько добавить?",
}

FOOD_WEIGHTS = {
    "Сырники": "220 г",
    "Сэндвич с курицей": "180 г",
    "Сэндвич с тунцом": "180 г",
}

PUBLIC_IMAGE_BY_TITLE = {
    "Эспрессо": "https://images.unsplash.com/photo-1510707577719-ae7c14805e3a?auto=format&fit=crop&w=1200&q=85",
    "Американо": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=1200&q=85",
    "Фильтр": "https://commons.wikimedia.org/wiki/Special:FilePath/Pour-over_coffee_at_Mood_Coffee_Roastery.jpg",
    "v-60": "https://commons.wikimedia.org/wiki/Special:FilePath/Pour-over_coffee_at_Mood_Coffee_Roastery.jpg",
    "Флэт Уайт": "https://commons.wikimedia.org/wiki/Special:FilePath/Flat_white_coffee_with_pretty_feather_pattern.jpg",
    "Капучино": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=1200&q=85",
    "Латте": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=1200&q=85",
    "Раф": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=1200&q=85",
    "Любимый напиток Щегла": "https://images.unsplash.com/photo-1511920170033-f8396924c348?auto=format&fit=crop&w=1200&q=85",
    "Айс-латте": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=1200&q=85",
    "Айс маття": "https://commons.wikimedia.org/wiki/Special:FilePath/Matcha_latte.jpg",
    "Маття": "https://commons.wikimedia.org/wiki/Special:FilePath/Matcha_latte.jpg",
    "Чай": "https://commons.wikimedia.org/wiki/Special:FilePath/Cup_of_tea.jpg",
    "Какао": "https://commons.wikimedia.org/wiki/Special:FilePath/Hot_chocolate.jpg",
    "Круассан": "https://commons.wikimedia.org/wiki/Special:FilePath/Croissant-Petr_Kratochvil.jpg",
    "Брауни": "https://commons.wikimedia.org/wiki/Special:FilePath/Chocolate_Brownie.jpg",
    "Сырники": "https://commons.wikimedia.org/wiki/Special:FilePath/Syrniki.jpg",
    "Сэндвич с курицей": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=1200&q=85",
    "Сэндвич с тунцом": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=1200&q=85",
    "Апельсиновый фреш": "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?auto=format&fit=crop&w=1200&q=85",
    "Эспрессо-тоник": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=1200&q=85",
    "Клюквенный эспрессо-тоник": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=1200&q=85",
    "Бамбл": "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?auto=format&fit=crop&w=1200&q=85",
    "Клубничный айс-латте": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=1200&q=85",
    "Жасминовая айс-матча": "https://commons.wikimedia.org/wiki/Special:FilePath/Matcha_latte.jpg",
    "Гранатовый бамбл": "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?auto=format&fit=crop&w=1200&q=85",
    "Холодный чай груша-жасмин": "https://commons.wikimedia.org/wiki/Special:FilePath/Iced_tea_with_lemon.jpg",
    "Лимонад таро-клюква": "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?auto=format&fit=crop&w=1200&q=85",
    "Лимонад клубника - ревень": "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?auto=format&fit=crop&w=1200&q=85",
    "Баноффи": "https://images.unsplash.com/photo-1551024601-bec78aea704b?auto=format&fit=crop&w=1200&q=85",
    "Лимонный тарт": "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=1200&q=85",
    "Баскский чизкейк с черникой": "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?auto=format&fit=crop&w=1200&q=85",
}

CATEGORY_IMAGE_FALLBACK = {
    "coffee": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=1200&q=85",
    "dessert": "https://images.unsplash.com/photo-1551024601-bec78aea704b?auto=format&fit=crop&w=1200&q=85",
    "food": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=1200&q=85",
    "noncoffee": "https://images.unsplash.com/photo-1523906630133-f6934a1ab2b9?auto=format&fit=crop&w=1200&q=85",
    "cold": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=1200&q=85",
    "seasonal": "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?auto=format&fit=crop&w=1200&q=85",
}

PRICE_BY_VOLUME = {
    "Фильтр": {"200": 230, "300": 260, "400": 300},
    "Капучино": {"200": 280, "300": 330, "400": 380},
}


def _price_to_int(value: Any) -> int | None:
    if value is None:
        return None
    match = re.search(r"\d+", str(value).replace(" ", ""))
    return int(match.group()) if match else None


def _format_source_price(value: Any) -> str:
    if value in (None, ""):
        return "уточнить"
    text = str(value).strip()
    return text if "₽" in text or text == "уточнить" else f"{text} ₽"


def _extract_volume(title: str) -> str:
    lowered = title.lower()
    if "0.2" in lowered or "0,2" in lowered:
        return "200 мл"
    if "0.3" in lowered or "0,3" in lowered:
        return "300 мл"
    if "0.4" in lowered or "0,4" in lowered:
        return "400 мл"
    return ""


def normalize_menu_title(title: str) -> str:
    title = title.strip()
    if re.fullmatch(r"Фильтр\s*0[,.][23]", title, flags=re.IGNORECASE):
        return "Фильтр"
    if re.fullmatch(r"Капучино\s*0[,.][23]", title, flags=re.IGNORECASE):
        return "Капучино"
    return title


def option_profile_for(title: str, category: str) -> dict[str, Any]:
    lower = title.lower()

    if category in {"dessert", "food"}:
        return {"steps": [], "price_by_volume": {}}

    if title in {"Эспрессо"}:
        return {"steps": ["sugar"], "price_by_volume": {}}

    if title in {"Фильтр", "v-60", "Американо"}:
        return {"steps": ["volume", "sugar"], "price_by_volume": PRICE_BY_VOLUME.get(title, {})}

    if title in {"Капучино", "Флэт Уайт", "Латте", "Раф", "Любимый напиток Щегла"}:
        return {"steps": ["volume", "milk", "sugar", "additives"], "price_by_volume": PRICE_BY_VOLUME.get(title, {})}

    if title in {"Какао", "Таро", "Маття", "Айс-латте", "Айс маття", "Клубничный айс-латте", "Жасминовая айс-матча"}:
        return {"steps": ["volume", "milk", "sugar"], "price_by_volume": {}}

    if title == "Чай":
        return {"steps": ["volume", "sugar"], "price_by_volume": {}}

    if "лимонад" in lower or "бамбл" in lower or "тоник" in lower or "фреш" in lower or "холодный чай" in lower:
        return {"steps": ["volume", "sugar"], "price_by_volume": {}}

    return {"steps": ["volume"], "price_by_volume": {}}


def load_menu() -> list[dict[str, Any]]:
    if not MENU_JSON_PATH.exists():
        raise FileNotFoundError(f"Не найден файл меню: {MENU_JSON_PATH}")

    raw_items = json.loads(MENU_JSON_PATH.read_text(encoding="utf-8-sig"))
    counters: dict[str, int] = {}
    items: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()

    for raw in raw_items:
        category = raw.get("category")
        if category not in CATEGORY_META:
            continue

        price = raw.get("price")
        source_title = str(raw.get("title", "")).strip()
        title = normalize_menu_title(source_title)
        dedupe_key = (category, title.lower())
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)

        counters[category] = counters.get(category, 0) + 1
        item_id = f"{category}_{counters[category]}"
        raw_image_url = str(raw.get("image_url", "")).strip()
        image_url = raw_image_url if raw_image_url.startswith(("http://", "https://")) else ""
        if not image_url:
            image_url = PUBLIC_IMAGE_BY_TITLE.get(title, "")
        if not image_url:
            image_url = CATEGORY_IMAGE_FALLBACK.get(category, "")
        profile = option_profile_for(title, category)

        items.append(
            {
                "id": item_id,
                "title": title,
                "category": category,
                "description": str(raw.get("desc", "")).strip(),
                "price": _format_source_price(price),
                "price_value": _price_to_int(price),
                "image": raw.get("image", ""),
                "image_url": image_url,
                "kind": raw.get("kind", ""),
                "volume": "",
                "weight": FOOD_WEIGHTS.get(title, ""),
                "option_steps": profile["steps"],
                "price_by_volume": profile["price_by_volume"],
            }
        )

    return items


MENU_ITEMS = load_menu()
MENU_BY_ID = {item["id"]: item for item in MENU_ITEMS}
MENU_BY_CATEGORY = {
    category: [item for item in MENU_ITEMS if item["category"] == category]
    for category in CATEGORY_ORDER
}


def validate_menu_counts() -> dict[str, tuple[int, int]]:
    result: dict[str, tuple[int, int]] = {}
    for category, expected in EXPECTED_COUNTS.items():
        result[category] = (len(MENU_BY_CATEGORY.get(category, [])), expected)
    return result


def category_label(category: str) -> str:
    meta = CATEGORY_META[category]
    return f'{meta["emoji"]} {meta["title"]}'


def format_price(value: int | None) -> str:
    return f"{value} ₽" if value is not None else "уточнить"


def option_by_key(group: str, key: str) -> dict[str, Any]:
    if group == "volumes":
        group = "volume"
    for option in OPTION_GROUPS[group]:
        if option["key"] == key:
            return option
    raise KeyError(key)


def default_coffee_options() -> dict[str, Any]:
    return {
        "volume": COFFEE_OPTIONS["volumes"][0]["key"],
        "milk": COFFEE_OPTIONS["milk"][0]["key"],
        "sugar": COFFEE_OPTIONS["sugar"][0]["key"],
        "additives": [],
        "quantity": 1,
    }


WEEKLY_SPECIAL_IDS = [
    item["id"]
    for item in MENU_ITEMS
    if item["category"] == "seasonal"
][:4]


def menu_image_url(item: dict[str, Any]) -> str:
    return str(item.get("image_url", "")).strip()
