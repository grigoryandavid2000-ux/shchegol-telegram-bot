from __future__ import annotations

import asyncio
import html
import logging
import os
from pathlib import Path
from typing import Any

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest
from aiohttp import web
from dotenv import load_dotenv

from data import (
    ABOUT_TEXT,
    BRANCHES,
    CATEGORY_ORDER,
    MENU_BY_ID,
    SITE_URL,
    SOCIAL_LINKS,
    STEP_TITLES,
    WEEKLY_SPECIAL_IDS,
    category_label,
    format_price,
    menu_image_url,
    option_by_key,
    validate_menu_counts,
)
from database import (
    clear_cart,
    create_order,
    get_cart,
    get_loyalty,
    increment_loyalty,
    init_db,
    upsert_cart_item,
    upsert_user,
)
from keyboards import (
    about_keyboard,
    additives_keyboard,
    branch_actions_keyboard,
    branches_keyboard,
    cart_keyboard,
    categories_keyboard,
    confirm_order_keyboard,
    contacts_keyboard,
    help_keyboard,
    item_card_keyboard,
    items_keyboard,
    main_inline_keyboard,
    options_keyboard,
    pickup_keyboard,
    quantity_keyboard,
    review_links_keyboard,
    weekly_specials_keyboard,
)


dp = Dispatcher()
BASE_DIR = Path(__file__).resolve().parent
LOG_PATH = BASE_DIR / "bot.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("shchegol_bot")

user_state: dict[int, dict[str, Any]] = {}
last_bot_messages: dict[int, int] = {}


def state(user_id: int) -> dict[str, Any]:
    return user_state.setdefault(user_id, {})


async def send_clean(message: Message, text: str, **kwargs: Any) -> Message:
    chat_id = message.chat.id
    previous_message_id = last_bot_messages.get(chat_id)

    if previous_message_id:
        try:
            await message.bot.delete_message(chat_id=chat_id, message_id=previous_message_id)
        except TelegramBadRequest:
            pass

    if message.from_user and not message.from_user.is_bot:
        try:
            await message.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        except TelegramBadRequest:
            pass

    sent = await message.answer(text, **kwargs)
    last_bot_messages[chat_id] = sent.message_id
    return sent


async def call_clean(call: CallbackQuery, text: str, **kwargs: Any) -> Message:
    chat_id = call.message.chat.id
    previous_message_id = last_bot_messages.get(chat_id)

    if previous_message_id and previous_message_id != call.message.message_id:
        try:
            await call.message.bot.delete_message(chat_id=chat_id, message_id=previous_message_id)
        except TelegramBadRequest:
            pass

    try:
        await call.message.edit_text(text, **kwargs)
        last_bot_messages[chat_id] = call.message.message_id
        return call.message
    except TelegramBadRequest:
        for message_id in {previous_message_id, call.message.message_id}:
            if message_id:
                try:
                    await call.message.bot.delete_message(chat_id=chat_id, message_id=message_id)
                except TelegramBadRequest:
                    pass

        sent = await call.message.answer(text, **kwargs)
        last_bot_messages[chat_id] = sent.message_id
        return sent


async def stale_callback(call: CallbackQuery) -> None:
    await call_clean(
        call,
        "Эта кнопка уже устарела. Открою меню заново.",
        reply_markup=main_inline_keyboard(),
    )
    await answer_callback(call)


async def delete_webhook_if_any(bot: Bot) -> None:
    await bot.delete_webhook(drop_pending_updates=True)


async def stop_callback_loading(call: CallbackQuery) -> None:
    try:
        await answer_callback(call)
    except TelegramBadRequest:
        pass


async def answer_callback(call: CallbackQuery, text: str | None = None, show_alert: bool = False) -> None:
    try:
        await call.answer(text=text, show_alert=show_alert)
    except TelegramBadRequest:
        logger.warning("Callback answer skipped: query is too old or invalid")


async def clear_current_button_message(call: CallbackQuery) -> None:
    chat_id = call.message.chat.id
    try:
        await call.message.bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
    except TelegramBadRequest:
        pass


async def remove_known_messages(call: CallbackQuery) -> None:
    chat_id = call.message.chat.id
    previous_message_id = last_bot_messages.get(chat_id)
    for message_id in {previous_message_id, call.message.message_id}:
        if message_id:
            try:
                await call.message.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except TelegramBadRequest:
                pass


def item_needs_coffee_options(item: dict[str, Any]) -> bool:
    return bool(item.get("option_steps"))


def build_item_text(item: dict[str, Any]) -> str:
    parts = [
        f"<b>{html.escape(item['title'])}</b>",
        f"Категория: {html.escape(category_label(item['category']))}",
    ]
    if item["description"]:
        parts.append(html.escape(item["description"]))
    if item["volume"]:
        parts.append(f"Объём: {html.escape(item['volume'])}")
    if item["weight"]:
        parts.append(f"Вес: {html.escape(item['weight'])}")
    if item.get("option_steps"):
        steps = ", ".join(STEP_TITLES[step].lower() for step in item["option_steps"] if step in STEP_TITLES)
        parts.append(f"<i>При добавлении можно выбрать: {html.escape(steps)}.</i>")
    parts.append(f"<b>Цена:</b> {html.escape(item['price'])}")
    return "\n\n".join(parts)


async def show_item_card(call: CallbackQuery, item: dict[str, Any], mode: str) -> None:
    text = build_item_text(item)
    markup = item_card_keyboard(item["id"], item["category"], mode)
    image_url = menu_image_url(item)

    if not image_url:
        await call_clean(call, text, reply_markup=markup)
        return

    await remove_known_messages(call)
    try:
        sent = await call.message.answer_photo(
            photo=image_url,
            caption=text,
            reply_markup=markup,
        )
    except TelegramBadRequest:
        sent = await call.message.answer(text, reply_markup=markup)
    last_bot_messages[call.message.chat.id] = sent.message_id


def pending_unit_price(pending: dict[str, Any]) -> int | None:
    item = MENU_BY_ID[pending["item_id"]]
    base = item["price_value"]
    if base is None:
        return None

    total = base
    selected = pending.get("options", {})
    volume = selected.get("volume")
    price_by_volume = item.get("price_by_volume") or {}
    if volume and price_by_volume.get(volume) is not None:
        total = int(price_by_volume[volume])
    elif volume:
        try:
            total += option_by_key("volume", volume)["price_delta"]
        except KeyError:
            logger.warning("Unknown volume option: %s", volume)

    for group in ("milk", "sugar"):
        key = selected.get(group)
        if key:
            try:
                total += option_by_key(group, key)["price_delta"]
            except KeyError:
                logger.warning("Unknown option price: %s=%s", group, key)

    for additive_key in selected.get("additives", []):
        try:
            total += option_by_key("additives", additive_key)["price_delta"]
        except KeyError:
            logger.warning("Unknown additive price: %s", additive_key)
    return total


async def show_next_pending_step(call: CallbackQuery, pending: dict[str, Any]) -> None:
    item = MENU_BY_ID[pending["item_id"]]
    steps = item.get("option_steps") or []
    step_index = pending.get("step_index", 0)

    if step_index >= len(steps):
        await call_clean(call, "<b>Сколько добавить?</b>", reply_markup=quantity_keyboard())
        return

    step = steps[step_index]
    title = STEP_TITLES.get(step, "Выберите параметр")
    selected = pending.get("options", {}).get(step, [])
    if isinstance(selected, str):
        selected = [selected]
    await call_clean(call, f"<b>{html.escape(title)}</b>", reply_markup=options_keyboard(step, selected))


def advance_pending_step(pending: dict[str, Any]) -> None:
    pending["step_index"] = pending.get("step_index", 0) + 1


def safe_option_title(group: str, key: str) -> str:
    try:
        return option_by_key(group, key)["title"]
    except KeyError:
        logger.warning("Unknown option in cart: %s=%s", group, key)
        return key


def cart_total(items: list[dict[str, Any]]) -> int | None:
    total = 0
    for entry in items:
        if entry["unit_price"] is None:
            return None
        total += entry["unit_price"] * entry["quantity"]
    return total


def describe_entry(entry: dict[str, Any]) -> str:
    text = f"• <b>{html.escape(entry['title'])}</b> x {entry['quantity']}"
    options = entry.get("options") or {}
    details: list[str] = []
    if options:
        for group in ("volume", "milk", "sugar"):
            key = options.get(group)
            if key:
                details.append(safe_option_title(group, key))
        if options.get("additives"):
            additives = ", ".join(
                safe_option_title("additives", key) for key in options["additives"]
            )
            details.append(f"добавки: {additives}")
    if details:
        text += f"\n  <i>{html.escape(', '.join(details))}</i>"
    text += f"\n   {format_price(entry['unit_price'])}"
    return text


def cart_text(user_id: int) -> str:
    items = get_cart(user_id)
    if not items:
        return "<b>🛒 Корзина</b>\n\nКорзина пока пустая. Можно спокойно выбрать кофе, десерт или завтрак."

    lines = ["<b>🛒 Ваша корзина</b>"]
    lines.extend(describe_entry(entry) for entry in items)
    total = cart_total(items)
    lines.append(f"\nИтого: {format_price(total)}")
    return "\n\n".join(lines)


def contacts_text() -> str:
    lines = ["<b>☎️ Контакты «Щегла»</b>"]
    for branch in BRANCHES.values():
        lines.append(
            "\n"
            f"<b>{html.escape(branch['title'])}</b>\n"
            f"📍 {html.escape(branch['address'])}\n"
            f"🕘 {html.escape(branch['hours'])}\n"
            f"☎️ {html.escape(branch.get('phone', 'телефон уточняется'))}"
        )
    if SITE_URL:
        lines.append(f"\nСайт: {html.escape(SITE_URL)}")
    if SOCIAL_LINKS:
        lines.append("\nСоцсети доступны кнопками ниже.")
    return "\n".join(lines)


HELP_TEXT = (
    "<b>❓ Как пользоваться ботом</b>\n\n"
    "1. Откройте меню.\n"
    "2. Выберите категорию.\n"
    "3. Откройте карточку позиции.\n"
    "4. Для кофе выберите объём, молоко, сахар и добавки.\n"
    "5. Добавьте позицию в корзину.\n"
    "6. Откройте корзину и оформите предзаказ.\n\n"
    "Если что-то не работает — вернитесь в главное меню и попробуйте ещё раз "
    "или свяжитесь с нами."
)


def order_summary(user_id: int) -> str:
    data = state(user_id)
    branch = BRANCHES.get(data.get("branch_id", ""), {})
    pickup = data.get("pickup_time", "не выбрано")
    total = cart_total(get_cart(user_id))

    lines = [
        "<b>Проверьте заказ</b>",
        f"📍 Филиал: {html.escape(branch.get('address', 'не выбран'))}",
        f"⏱ Самовывоз: {html.escape(pickup)}",
        "",
        cart_text(user_id),
        "",
        f"Сумма: {format_price(total)}",
    ]
    return "\n".join(lines)


async def show_main(message_or_call: Message | CallbackQuery) -> None:
    text = (
        "<b>Здравствуйте! Это бот кофейни «Щегол» ☕</b>\n\n"
        "Здесь можно посмотреть меню, собрать предзаказ, узнать о новинках, "
        "найти ближайшую кофейню и открыть карту гостя.\n\n"
        "Выберите нужный раздел ниже — мы всё подскажем."
    )
    if isinstance(message_or_call, CallbackQuery):
        await call_clean(message_or_call, text, reply_markup=main_inline_keyboard())
        await message_or_call.answer()
    else:
        await send_clean(message_or_call, text, reply_markup=main_inline_keyboard())


@dp.message(CommandStart())
async def start(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    counts = validate_menu_counts()
    wrong = [key for key, pair in counts.items() if pair[0] != pair[1]]
    if wrong:
        await send_clean(
            message,
            "Меню загружено, но количество позиций отличается от заданной структуры. "
            "Проверьте assets/menu-items-full.json перед запуском."
        )
    await show_main(message)


@dp.message(F.text == "📋 Меню")
async def menu(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await send_clean(
        message,
        "<b>📋 Меню Щегла</b>\n\n"
        "Выберите категорию. В карточке позиции можно посмотреть описание, цену "
        "и добавить товар в корзину.",
        reply_markup=categories_keyboard("menu"),
    )


@dp.message(F.text == "☕ Заказать заранее")
async def preorder(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await send_clean(
        message,
        "<b>☕ Заказать заранее</b>\n\nС какого филиала приготовить заказ?",
        reply_markup=branches_keyboard("order_branch"),
    )


@dp.message(F.text == "🛒 Корзина")
async def show_cart_message(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await send_clean(message, cart_text(message.from_user.id), reply_markup=cart_keyboard())


@dp.message(F.text == "📍 Филиалы")
async def branches_message(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await send_clean(
        message,
        "<b>📍 Филиалы</b>\n\nВыберите, куда удобнее заглянуть.",
        reply_markup=branches_keyboard("branch_info"),
    )


@dp.message(F.text == "⭐ Отзывы")
async def reviews_message(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await send_clean(
        message,
        "Отзывы лучше смотреть на площадках, где гости их оставляют. Выберите филиал.",
        reply_markup=branches_keyboard("reviews_branch"),
    )


@dp.message(F.text == "🎁 Моя карта гостя")
async def loyalty_message(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    count = get_loyalty(message.from_user.id)
    await send_clean(
        message,
        f"Ваша карта гостя: {count} / 7 кофе.\n\n"
        "Копите напитки и получайте каждый 8-й кофе в подарок.\n"
        "Сейчас прогресс хранится временно, позже сюда можно подключить SQLite.",
        reply_markup=main_inline_keyboard(),
    )


@dp.message(F.text == "🔥 Новинки недели")
async def weekly_message(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    if not WEEKLY_SPECIAL_IDS:
        await send_clean(message, "Новинки недели скоро появятся.", reply_markup=main_inline_keyboard())
        return

    lines = ["На этой неделе можно обратить внимание на сезонные позиции:"]
    for number, item_id in enumerate(WEEKLY_SPECIAL_IDS, start=1):
        item = MENU_BY_ID[item_id]
        lines.append(f"\n{number}. {item['title']} — {item['price']}")
        if item["description"]:
            lines.append(item["description"])

    await send_clean(message, "\n".join(lines), reply_markup=weekly_specials_keyboard(WEEKLY_SPECIAL_IDS))


@dp.message(F.text == "ℹ️ О кофейне")
async def about_message(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await send_clean(message, ABOUT_TEXT, reply_markup=about_keyboard())


@dp.message(F.text == "☎️ Контакты")
async def contacts_message(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await send_clean(message, contacts_text(), reply_markup=contacts_keyboard())


@dp.message(F.text == "❓ Справка")
async def help_message(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await send_clean(message, HELP_TEXT, reply_markup=help_keyboard())


@dp.message(F.text == "🌐 Сайт")
async def site_message(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await send_clean(
        message,
        f"<b>Сайт кофейни «Щегол»</b>\n\nОткрыть сайт можно здесь:\n{SITE_URL}",
        reply_markup=main_inline_keyboard(),
    )


@dp.callback_query(F.data == "main")
async def main_callback(call: CallbackQuery) -> None:
    await show_main(call)


@dp.callback_query(F.data == "order_start")
async def order_start_callback(call: CallbackQuery) -> None:
    upsert_user(call.from_user.id, call.from_user.first_name, call.from_user.username)
    await call_clean(
        call,
        "<b>☕ Заказать заранее</b>\n\nС какого филиала приготовить заказ?",
        reply_markup=branches_keyboard("order_branch"),
    )
    await answer_callback(call)


@dp.callback_query(F.data == "loyalty")
async def loyalty_callback(call: CallbackQuery) -> None:
    upsert_user(call.from_user.id, call.from_user.first_name, call.from_user.username)
    count = get_loyalty(call.from_user.id)
    await call_clean(
        call,
        f"Ваша карта гостя: {count} / 7 кофе.\n\n"
        "Копите напитки и получайте каждый 8-й кофе в подарок.\n"
        "Сейчас прогресс хранится временно, позже сюда можно подключить SQLite.",
        reply_markup=main_inline_keyboard(),
    )
    await answer_callback(call)


@dp.callback_query(F.data == "weekly")
async def weekly_callback(call: CallbackQuery) -> None:
    if not WEEKLY_SPECIAL_IDS:
        await call_clean(call, "Новинки недели скоро появятся.", reply_markup=main_inline_keyboard())
        await answer_callback(call)
        return

    lines = ["На этой неделе можно обратить внимание на сезонные позиции:"]
    for number, item_id in enumerate(WEEKLY_SPECIAL_IDS, start=1):
        item = MENU_BY_ID[item_id]
        lines.append(f"\n{number}. {item['title']} — {item['price']}")
        if item["description"]:
            lines.append(item["description"])

    await call_clean(call, "\n".join(lines), reply_markup=weekly_specials_keyboard(WEEKLY_SPECIAL_IDS))
    await answer_callback(call)


@dp.callback_query(F.data == "about")
async def about_callback(call: CallbackQuery) -> None:
    await call_clean(call, ABOUT_TEXT, reply_markup=about_keyboard())
    await answer_callback(call)


@dp.callback_query(F.data == "contacts")
async def contacts_callback(call: CallbackQuery) -> None:
    await call_clean(call, contacts_text(), reply_markup=contacts_keyboard())
    await answer_callback(call)


@dp.callback_query(F.data == "help")
async def help_callback(call: CallbackQuery) -> None:
    await call_clean(call, HELP_TEXT, reply_markup=help_keyboard())
    await answer_callback(call)


@dp.callback_query(F.data == "menu_categories")
async def menu_categories_callback(call: CallbackQuery) -> None:
    await call_clean(
        call,
        "<b>📋 Меню Щегла</b>\n\nВыберите категорию.",
        reply_markup=categories_keyboard("menu"),
    )
    await answer_callback(call)


@dp.callback_query(F.data == "order_categories")
async def order_categories_callback(call: CallbackQuery) -> None:
    await call_clean(call, "<b>Что приготовить заранее?</b>", reply_markup=categories_keyboard("order"))
    await answer_callback(call)


@dp.callback_query(F.data.startswith("menu_cat:"))
async def menu_category_callback(call: CallbackQuery) -> None:
    category = call.data.split(":", 1)[1]
    if category not in CATEGORY_ORDER:
        await stale_callback(call)
        return
    await call_clean(call, category_label(category), reply_markup=items_keyboard(category, "menu"))
    await answer_callback(call)


@dp.callback_query(F.data.startswith("order_cat:"))
async def order_category_callback(call: CallbackQuery) -> None:
    category = call.data.split(":", 1)[1]
    if category not in CATEGORY_ORDER:
        await stale_callback(call)
        return
    await call_clean(call, category_label(category), reply_markup=items_keyboard(category, "order"))
    await answer_callback(call)


@dp.callback_query(F.data.startswith("menu_item:"))
@dp.callback_query(F.data.startswith("order_item:"))
async def item_callback(call: CallbackQuery) -> None:
    prefix, item_id = call.data.split(":", 1)
    mode = "order" if prefix == "order_item" else "menu"
    item = MENU_BY_ID.get(item_id)
    if not item:
        await stale_callback(call)
        return
    await show_item_card(call, item, mode)
    await answer_callback(call)


@dp.callback_query(F.data.startswith("order_branch:"))
async def order_branch_callback(call: CallbackQuery) -> None:
    branch_id = call.data.split(":", 1)[1]
    if branch_id not in BRANCHES:
        await stale_callback(call)
        return
    state(call.from_user.id)["branch_id"] = branch_id
    await call_clean(
        call,
        f"Выбран филиал:\n{BRANCHES[branch_id]['address']}\n\nТеперь выберите раздел меню.",
        reply_markup=categories_keyboard("order"),
    )
    await answer_callback(call)


@dp.callback_query(F.data == "branches")
async def branches_callback(call: CallbackQuery) -> None:
    await call_clean(
        call,
        "Выберите филиал.",
        reply_markup=branches_keyboard("branch_info"),
    )
    await answer_callback(call)


@dp.callback_query(F.data.startswith("branch_info:"))
async def branch_info_callback(call: CallbackQuery) -> None:
    branch_id = call.data.split(":", 1)[1]
    if branch_id not in BRANCHES:
        await stale_callback(call)
        return
    branch = BRANCHES[branch_id]
    await call_clean(
        call,
        f"{branch['title']}\n\n"
        f"Адрес: {branch['address']}\n"
        f"Режим работы: {branch['hours']}",
        reply_markup=branch_actions_keyboard(branch_id),
    )
    await answer_callback(call)


@dp.callback_query(F.data == "reviews")
async def reviews_callback(call: CallbackQuery) -> None:
    await call_clean(
        call,
        "Выберите филиал, отзывы которого хотите открыть.",
        reply_markup=branches_keyboard("reviews_branch"),
    )
    await answer_callback(call)


@dp.callback_query(F.data.startswith("reviews_branch:"))
async def reviews_branch_callback(call: CallbackQuery) -> None:
    branch_id = call.data.split(":", 1)[1]
    if branch_id not in BRANCHES:
        await stale_callback(call)
        return
    branch = BRANCHES[branch_id]
    await call_clean(
        call,
        f"Отзывы филиала:\n{branch['address']}",
        reply_markup=review_links_keyboard(branch_id),
    )
    await answer_callback(call)


@dp.callback_query(F.data.startswith("add:"))
async def add_callback(call: CallbackQuery) -> None:
    item_id = call.data.split(":", 1)[1]
    item = MENU_BY_ID.get(item_id)
    if not item:
        await stale_callback(call)
        return
    current = state(call.from_user.id)
    current["pending"] = {"item_id": item_id, "options": {}, "step_index": 0}

    if item_needs_coffee_options(item):
        await show_next_pending_step(call, current["pending"])
    else:
        await call_clean(call, "<b>Сколько добавить?</b>", reply_markup=quantity_keyboard())
    await answer_callback(call)


@dp.callback_query(F.data.startswith("opt:"))
async def option_callback(call: CallbackQuery) -> None:
    parts = call.data.split(":", 2)
    if len(parts) != 3:
        await stale_callback(call)
        return
    _, group, key = parts
    pending = state(call.from_user.id).get("pending")
    if not pending:
        await stale_callback(call)
        return

    item = MENU_BY_ID.get(pending["item_id"])
    if not item or group not in item.get("option_steps", []):
        await stale_callback(call)
        return

    if group == "additives":
        additives = pending["options"].setdefault("additives", [])
        if key in additives:
            additives.remove(key)
        else:
            additives.append(key)
        await call.message.edit_reply_markup(reply_markup=additives_keyboard(additives))
    else:
        pending["options"][group] = key
        advance_pending_step(pending)
        await show_next_pending_step(call, pending)
    await answer_callback(call)


@dp.callback_query(F.data == "opt_done:additives")
async def option_additives_done_callback(call: CallbackQuery) -> None:
    pending = state(call.from_user.id).get("pending")
    if not pending:
        await stale_callback(call)
        return
    advance_pending_step(pending)
    await show_next_pending_step(call, pending)
    await answer_callback(call)


@dp.callback_query(F.data.startswith("qty:"))
async def quantity_callback(call: CallbackQuery) -> None:
    quantity = int(call.data.split(":", 1)[1])
    current = state(call.from_user.id)
    pending = current.get("pending")
    if not pending:
        await answer_callback(call, "Выберите позицию заново", show_alert=True)
        return

    item = MENU_BY_ID[pending["item_id"]]
    pending["quantity"] = quantity

    if item_needs_coffee_options(item):
        unit_price = pending_unit_price(pending)
        options = pending.get("options", {})
    else:
        unit_price = item["price_value"]
        options = {}

    upsert_cart_item(
        user_id=call.from_user.id,
        item_id=item["id"],
        title=item["title"],
        quantity=quantity,
        unit_price=unit_price,
        options=options,
    )
    current.pop("pending", None)

    if item["category"] == "coffee":
        increment_loyalty(call.from_user.id, quantity)

    await call_clean(
        call,
        f"{item['title']} добавлен в корзину.\n\n{cart_text(call.from_user.id)}",
        reply_markup=cart_keyboard(),
    )
    await answer_callback(call)


@dp.callback_query(F.data == "cart")
async def cart_callback(call: CallbackQuery) -> None:
    await call_clean(call, cart_text(call.from_user.id), reply_markup=cart_keyboard())
    await answer_callback(call)


@dp.callback_query(F.data == "cart_clear")
async def cart_clear_callback(call: CallbackQuery) -> None:
    clear_cart(call.from_user.id)
    await call_clean(call, "Корзина очищена.", reply_markup=cart_keyboard())
    await answer_callback(call)


@dp.callback_query(F.data == "checkout")
async def checkout_callback(call: CallbackQuery) -> None:
    if not get_cart(call.from_user.id):
        await call_clean(call, "Корзина пустая. Сначала выберите позиции.", reply_markup=categories_keyboard("menu"))
        await answer_callback(call)
        return

    if not state(call.from_user.id).get("branch_id"):
        await call_clean(
            call,
            "Выберите филиал для самовывоза.",
            reply_markup=branches_keyboard("checkout_branch"),
        )
        await answer_callback(call)
        return

    await call_clean(call, "Когда заберёте заказ?", reply_markup=pickup_keyboard())
    await answer_callback(call)


@dp.callback_query(F.data.startswith("checkout_branch:"))
async def checkout_branch_callback(call: CallbackQuery) -> None:
    branch_id = call.data.split(":", 1)[1]
    state(call.from_user.id)["branch_id"] = branch_id
    await call_clean(call, "Когда заберёте заказ?", reply_markup=pickup_keyboard())
    await answer_callback(call)


@dp.callback_query(F.data.startswith("pickup:"))
async def pickup_callback(call: CallbackQuery) -> None:
    minutes = call.data.split(":", 1)[1]
    state(call.from_user.id)["pickup_time"] = f"через {minutes} мин"
    await call_clean(call, order_summary(call.from_user.id), reply_markup=confirm_order_keyboard())
    await answer_callback(call)


@dp.callback_query(F.data == "confirm_order")
async def confirm_order_callback(call: CallbackQuery) -> None:
    items = get_cart(call.from_user.id)
    data = state(call.from_user.id)
    create_order(
        user_id=call.from_user.id,
        branch_id=data.get("branch_id", ""),
        pickup_time=data.get("pickup_time", ""),
        total=cart_total(items),
        items=items,
    )
    await call_clean(
        call,
        order_summary(call.from_user.id)
        + "\n\nЗаказ сформирован. Для реального запуска нужно подключить уведомления бариста или оплату.",
        reply_markup=main_inline_keyboard(),
    )
    clear_cart(call.from_user.id)
    state(call.from_user.id).pop("pickup_time", None)
    await answer_callback(call)


@dp.callback_query()
async def unknown_callback(call: CallbackQuery) -> None:
    await stale_callback(call)


@dp.message()
async def fallback(message: Message) -> None:
    await send_clean(
        message,
        "Я рядом. Выберите раздел в меню ниже.",
        reply_markup=main_inline_keyboard(),
    )


async def healthcheck(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "shchegol-telegram-bot"})


async def start_health_server() -> web.AppRunner | None:
    port = os.getenv("PORT")
    if not port:
        return None

    app = web.Application()
    app.router.add_get("/", healthcheck)
    app.router.add_get("/health", healthcheck)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(port))
    await site.start()
    logger.info("Health server started on port %s", port)
    return runner


async def main() -> None:
    load_dotenv(BASE_DIR / ".env")
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Добавьте BOT_TOKEN в файл .env рядом с bot.py")

    init_db()
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode="HTML"))
    health_runner = await start_health_server()
    await delete_webhook_if_any(bot)
    me = await bot.get_me()
    logger.info("Bot started: @%s id=%s", me.username, me.id)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        if health_runner:
            await health_runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

