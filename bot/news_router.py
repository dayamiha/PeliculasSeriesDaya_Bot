"""
Monitorea CANAL_NOTICIAS (-1003862300011).
Cuando el usuario publica manualmente un link monetizado allí,
el bot lo clasifica y lo publica con formato premium en el canal correcto:
  - Tech / Medio Ambiente → CANAL_NOTICIAS_TECH  (-1003577192760)
  - Entretenimiento       → CANAL_FINAL          (-1003889304272)
"""
import os
import re
import asyncio
from telegram import Bot, Message
from telegram.error import TelegramError
from classifier import detect_type
from content_generator import build_premium_post
from publisher import (
    CANAL_TECH_AMBIENTE, CANAL_ENTRETENIMIENTO,
    TECH_ENV_TYPES, ENTERTAINMENT_TYPES,
    thumbnail_ok, MAX_CAPTION, _send_text,
)

TELEGRAM_BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
CANAL_NOTICIAS      = os.environ.get("CANAL_NOTICIAS", "")

ALL_PUBLIC_TYPES = TECH_ENV_TYPES | ENTERTAINMENT_TYPES


def extract_urls(message: Message) -> list:
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


def dest_for_type(content_type: str) -> tuple[str, str]:
    """Devuelve (canal_destino, etiqueta)."""
    if content_type in TECH_ENV_TYPES:
        return CANAL_TECH_AMBIENTE, "Tech/Ambiente"
    if content_type in ENTERTAINMENT_TYPES:
        return CANAL_ENTRETENIMIENTO, "Entretenimiento"
    return "", "Desconocido"


async def route_news_message(message: Message) -> bool:
    """
    Se ejecuta cuando llega un post al CANAL_NOTICIAS.
    1. Extrae el URL (ya monetizado por el usuario)
    2. Clasifica el tipo de contenido
    3. Construye el post premium usando el link tal como llegó
    4. Envía al canal público correcto con thumbnail y hashtags
    """
    texto = message.text or message.caption or ""
    if not texto.strip():
        return False

    urls = extract_urls(message)
    if not urls:
        return False

    url  = urls[0]
    tipo = detect_type(texto)
    dest, label = dest_for_type(tipo)

    if not dest:
        print(f"[Router] ⚠️ Tipo '{tipo}' sin canal destino configurado.")
        return False

    # El URL ya viene monetizado por el usuario → se usa como enlace principal
    # "fallback" apunta a sí mismo (sin link alternativo ya que el usuario lo gestionó)
    item = {
        "title":        texto[:120],
        "url":          url,
        "description":  texto,
        "content_type": tipo,
        "genres":       [],
        "origins":      [],
        "source":       "Manual",
        "thumbnail":    "",
        # Señal para que el generador NO re-monetice (url ya es el link final del usuario)
        "url_is_final": True,
    }

    premium = build_premium_post(item)
    bot     = Bot(token=TELEGRAM_BOT_TOKEN)

    # Buscar miniatura: foto del mensaje o thumbnail de YouTube
    photo_file_id = ""
    thumb_url     = ""

    if message.photo:
        photo_file_id = message.photo[-1].file_id
    else:
        # Intentar extraer miniatura de YouTube
        yt = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
        if yt:
            vid_id = yt.group(1)
            for q in ("maxresdefault", "hqdefault", "mqdefault"):
                candidate = f"https://img.youtube.com/vi/{vid_id}/{q}.jpg"
                if thumbnail_ok(candidate):
                    thumb_url = candidate
                    break

    try:
        if photo_file_id:
            await bot.send_photo(
                chat_id=dest,
                photo=photo_file_id,
                caption=premium[:MAX_CAPTION],
                parse_mode=None,
            )
        elif thumb_url:
            await bot.send_photo(
                chat_id=dest,
                photo=thumb_url,
                caption=premium[:MAX_CAPTION],
                parse_mode=None,
            )
        else:
            await bot.send_message(
                chat_id=dest,
                text=premium,
                parse_mode=None,
                disable_web_page_preview=False,
            )
        print(f"[Router] ✅ [{label}] → {dest}: {url[:60]}")
        return True

    except TelegramError as e:
        print(f"[Router] ❌ Error enviando a {dest}: {e}")
        # Intentar sin foto como fallback
        try:
            await _send_text(bot, dest, premium)
            return True
        except Exception as e2:
            print(f"[Router] ❌ Fallback también falló: {e2}")
            return False
