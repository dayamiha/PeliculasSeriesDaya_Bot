import os
import re
import asyncio
from telegram import Bot, Message
from telegram.error import TelegramError
from classifier import detect_type, should_filter
from content_generator import build_premium_post
from publisher import (
    TYPE_LABELS, MAX_CAPTION, CANAL_ORGANIZADOR, CANAL_MONETIZADOR,
    CANAL_TECH_AMBIENTE, CANAL_ENTRETENIMIENTO,
    TECH_ENV_TYPES, ENTERTAINMENT_TYPES,
    get_auto_dest, _send_photo, _send_text,
)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]


def extract_urls_from_message(message: Message) -> list:
    texto = message.text or message.caption or ""
    urls = []
    entities = message.entities or message.caption_entities or []
    for e in entities:
        if e.type == "url":
            urls.append(texto[e.offset: e.offset + e.length])
        elif e.type == "text_link" and e.url:
            urls.append(e.url)
    if not urls:
        urls = re.findall(r'https?://\S+', texto)
    return urls


def build_org_text(tipo: str, url: str, texto: str) -> str:
    label   = TYPE_LABELS.get(tipo, tipo.upper())
    resumen = (texto[:200].strip() if texto else url)
    return f"{label}\n\n{resumen}\n\n🔗 {url}"


async def reenviar_mensaje(message: Message) -> bool:
    """
    Procesa mensajes del canal de recopilación:
    1. Filtra noticias/política/muertes
    2. Link simple → CANAL_ORGANIZADOR
    3. Formato premium → CANAL_MONETIZADOR
    4. Publica automáticamente en el canal correcto si aplica
    """
    texto = message.text or message.caption or ""
    if not texto.strip():
        return False

    urls = extract_urls_from_message(message)
    if not urls:
        return False

    tipo = detect_type(texto)
    if should_filter(texto, content_type=tipo):
        print(f"[Organizer] 🚫 Filtrado: {texto[:60]}")
        return False
    url  = urls[0]
    bot  = Bot(token=TELEGRAM_BOT_TOKEN)

    # Construir ítem para el generador
    item = {
        "title":        texto[:120],
        "url":          url,
        "description":  texto,
        "content_type": tipo,
        "genres":       [],
        "origins":      [],
        "source":       "Canal",
        "thumbnail":    "",
    }
    premium = build_premium_post(item)

    # Foto original del mensaje (si existe)
    photo_file_id = message.photo[-1].file_id if message.photo else ""

    # 1) Canal organizador — texto simple
    if CANAL_ORGANIZADOR:
        org_text = build_org_text(tipo, url, texto)
        await _send_text(bot, CANAL_ORGANIZADOR, org_text)
        await asyncio.sleep(3)

    # 2) Canal monetizador — formato premium para revisión
    if CANAL_MONETIZADOR:
        if photo_file_id:
            try:
                await bot.send_photo(
                    chat_id=CANAL_MONETIZADOR,
                    photo=photo_file_id,
                    caption=premium[:MAX_CAPTION],
                    parse_mode=None,
                )
            except TelegramError:
                await _send_text(bot, CANAL_MONETIZADOR, premium)
        else:
            await _send_text(bot, CANAL_MONETIZADOR, premium)
        await asyncio.sleep(3)

    # 3) Canal automático por tipo
    dest = get_auto_dest(tipo)
    if dest:
        if photo_file_id:
            try:
                await bot.send_photo(
                    chat_id=dest,
                    photo=photo_file_id,
                    caption=premium[:MAX_CAPTION],
                    parse_mode=None,
                )
            except TelegramError:
                await _send_text(bot, dest, premium)
        else:
            await _send_text(bot, dest, premium)
        tag = "Tech/Ambiente" if tipo in TECH_ENV_TYPES else "Entretenimiento"
        print(f"[Organizer] ✅ [{tag}] → {dest}: {url[:55]}")
    else:
        if tipo in ENTERTAINMENT_TYPES:
            print(f"[Organizer] ⏸️  [{tipo}] sin monetización → solo monetizador: {url[:55]}")

    return True
