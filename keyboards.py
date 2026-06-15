from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from data import BRANCHES, CATEGORY_ORDER, MENU_BY_CATEGORY, SOCIAL_LINKS, category_label


MAIN_BUTTONS = [
    ["☕ Заказать заранее", "📋 Меню"],
    ["🎁 Моя карта гостя", "⭐ Отзывы"],
    ["📍 Филиалы", "🔥 Новинки недели"],
    ["ℹ️ О кофейне", "☎️ Контакты"],
    ["❓ Справка"],
    ["🛒 Корзина"],
]


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=button) for button in row]
            for row in MAIN_BUTTONS
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел",
    )


def main_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="☕ Заказать заранее", callback_data="order_start"),
                InlineKeyboardButton(text="📋 Меню", callback_data="menu_categories"),
            ],
            [
                InlineKeyboardButton(text="🎁 Моя карта гостя", callback_data="loyalty"),
                InlineKeyboardButton(text="⭐ Отзывы", callback_data="reviews"),
            ],
            [
                InlineKeyboardButton(text="📍 Филиалы", callback_data="branches"),
                InlineKeyboardButton(text="🔥 Новинки недели", callback_data="weekly"),
            ],
            [
                InlineKeyboardButton(text="ℹ️ О кофейне", callback_data="about"),
                InlineKeyboardButton(text="☎️ Контакты", callback_data="contacts"),
            ],
            [InlineKeyboardButton(text="❓ Справка", callback_data="help")],
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
        ]
    )


def categories_keyboard(prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in CATEGORY_ORDER:
        builder.button(
            text=category_label(category),
            callback_data=f"{prefix}_cat:{category}",
        )
    builder.button(text="В главное меню", callback_data="main")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def items_keyboard(category: str, prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in MENU_BY_CATEGORY[category]:
        builder.button(text=item["title"], callback_data=f"{prefix}_item:{item['id']}")
    builder.button(text="Назад к категориям", callback_data=f"{prefix}_categories")
    builder.button(text="В главное меню", callback_data="main")
    builder.adjust(1)
    return builder.as_markup()


def item_card_keyboard(item_id: str, category: str, prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить в корзину", callback_data=f"add:{item_id}")],
            [InlineKeyboardButton(text="Назад в категорию", callback_data=f"{prefix}_cat:{category}")],
            [InlineKeyboardButton(text="В главное меню", callback_data="main")],
        ]
    )


def branches_keyboard(prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for branch_id, branch in BRANCHES.items():
        builder.button(text=branch["title"], callback_data=f"{prefix}:{branch_id}")
    builder.button(text="В главное меню", callback_data="main")
    builder.adjust(1)
    return builder.as_markup()


def branch_actions_keyboard(branch_id: str) -> InlineKeyboardMarkup:
    branch = BRANCHES[branch_id]
    rows = []
    if branch.get("yandex_url"):
        rows.append([InlineKeyboardButton(text="Открыть в Яндекс Картах", url=branch["yandex_url"])])
    if branch.get("dgis_url"):
        rows.append([InlineKeyboardButton(text="Открыть в 2ГИС", url=branch["dgis_url"])])
    rows.append([InlineKeyboardButton(text="Отзывы филиала", callback_data=f"reviews_branch:{branch_id}")])
    rows.append([InlineKeyboardButton(text="Все филиалы", callback_data="branches")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def review_links_keyboard(branch_id: str) -> InlineKeyboardMarkup:
    branch = BRANCHES[branch_id]
    rows = []
    if branch.get("yandex_reviews_url"):
        rows.append([InlineKeyboardButton(text="Отзывы на Яндекс Картах", url=branch["yandex_reviews_url"])])
    if branch.get("dgis_reviews_url"):
        rows.append([InlineKeyboardButton(text="Отзывы в 2ГИС", url=branch["dgis_reviews_url"])])
    rows.append([InlineKeyboardButton(text="Назад к филиалам", callback_data="reviews")])
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data="main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def simple_back_keyboard(back_callback: str = "main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data=back_callback)],
            [InlineKeyboardButton(text="В главное меню", callback_data="main")],
        ]
    )


def options_keyboard(group: str, selected: list[str] | None = None) -> InlineKeyboardMarkup:
    from data import OPTION_GROUPS

    builder = InlineKeyboardBuilder()
    selected = selected or []
    for option in OPTION_GROUPS[group]:
        marker = "✓ " if option["key"] in selected else ""
        delta = option["price_delta"]
        price_tail = f" +{delta} ₽" if delta else ""
        builder.button(
            text=f'{marker}{option["title"]}{price_tail}',
            callback_data=f"opt:{group}:{option['key']}",
        )
    if group == "additives":
        builder.button(text="Дальше", callback_data="opt_done:additives")
    builder.button(text="Отмена", callback_data="cart")
    builder.adjust(1)
    return builder.as_markup()


def coffee_options_keyboard(group: str) -> InlineKeyboardMarkup:
    normalized = "volume" if group == "volumes" else group
    return options_keyboard(normalized)


def additives_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    return options_keyboard("additives", selected)


def quantity_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for number in range(1, 6):
        builder.button(text=str(number), callback_data=f"qty:{number}")
    builder.button(text="Отмена", callback_data="cart")
    builder.adjust(5, 1)
    return builder.as_markup()


def cart_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="Продолжить выбирать", callback_data="menu_categories")],
            [InlineKeyboardButton(text="Очистить корзину", callback_data="cart_clear")],
            [InlineKeyboardButton(text="В главное меню", callback_data="main")],
        ]
    )


def about_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Меню", callback_data="menu_categories")],
            [InlineKeyboardButton(text="📍 Филиалы", callback_data="branches")],
            [InlineKeyboardButton(text="В главное меню", callback_data="main")],
        ]
    )


def help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Меню", callback_data="menu_categories")],
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
            [InlineKeyboardButton(text="В главное меню", callback_data="main")],
        ]
    )


def contacts_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for branch_id, branch in BRANCHES.items():
        if branch.get("yandex_url"):
            rows.append([InlineKeyboardButton(text=f"Яндекс: {branch['title']}", url=branch["yandex_url"])])
        if branch.get("dgis_url"):
            rows.append([InlineKeyboardButton(text=f"2ГИС: {branch['title']}", url=branch["dgis_url"])])
    for title, url in SOCIAL_LINKS.items():
        if url:
            rows.append([InlineKeyboardButton(text=title, url=url)])
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data="main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def weekly_specials_keyboard(item_ids: list[str]) -> InlineKeyboardMarkup:
    from data import MENU_BY_ID

    builder = InlineKeyboardBuilder()
    for item_id in item_ids:
        item = MENU_BY_ID[item_id]
        builder.button(text=f"Добавить: {item['title']}", callback_data=f"add:{item_id}")
    builder.button(text="В главное меню", callback_data="main")
    builder.adjust(1)
    return builder.as_markup()


def pickup_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for minutes in (15, 20, 30, 45, 60):
        builder.button(text=f"Через {minutes} мин", callback_data=f"pickup:{minutes}")
    builder.button(text="Назад в корзину", callback_data="cart")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def confirm_order_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить заказ", callback_data="confirm_order")],
            [InlineKeyboardButton(text="Назад в корзину", callback_data="cart")],
        ]
    )
