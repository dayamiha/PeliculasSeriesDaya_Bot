import asyncio
import os
import requests
from telegram import Bot
from telegram.error import TelegramError
from content_generator import build_premium_post

TELEGRAM_BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
CANAL_RECOPILACION  = os.environ["TELEGRAM_CHANNEL_ID"]

# Canal donde el bot monitorea noticias entrantes
CANAL_NOTICIAS      = os.environ.get("CANAL_NOTICIAS", "")

# Destinos de publicación automática (con formato premium)
CANAL_TECH_AMBIENTE = os.environ.get("CANAL_NOTICIAS_TECH", "")     # -1003577192760
CANAL_ENTRETENIMIENTO = os.environ.get("CANAL_FINAL", "")           # -1003889304272

# Canal organizador (clasificados simples, sin formato)
CANAL_ORGANIZADOR   = os.environ.get("CANAL_ORGANIZADOR", "")       # -1003792049532

# Canal monetizador (formato premium para revisión manual)
CANAL_MONETIZADOR   = os.environ.get("CANAL_MONETIZADOR", "")       # -1003645936496

MAX_CAPTION = 1020

# Tipos que van al canal de entretenimiento
ENTERTAINMENT_TYPES = {"novela", "serie", "anime", "pelicula", "documental_historia"}

# Tipos que van al canal tech/ambiente  
TECH_ENV_TYPES = {"tecnologia", "documental_ambiente", "documental_ciencia"}

TYPE_LABELS = {
    "novela":              "📺 NOVELA",
    "serie":               "🎬 SERIE",
    "anime":               "🌸 ANIME",
    "pelicula":            "🎬 PELÍCULA",
    "documental_ambiente": "🌿 DOCUMENTAL · Naturaleza",
    "documental_ciencia":  "🔬 DOCUMENTAL · Ciencia",
    "documental_historia": "🏛️ DOCUMENTAL · Historia",
    "tecnologia":          "📱 TECNOLOGÍA",
}


def thumbnail_ok(url: str) -> bool:
    if not url:
        return False
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        ct = r.headers.get("content-type", "")
        return r.status_code == 200 and "image" in ct
    except Exception:
        return False


def get_best_thumbnail(item: dict) -> str:
    import re
    thumb = item.get("thumbnail", "")
    if thumb and thumbnail_ok(thumb):
        return thumb
    if item.get("source") == "YouTube":
        match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", item.get("url", ""))
        if match:
            vid_id = match.group(1)
            for quality in ("maxresdefault", "hqdefault", "mqdefault"):
                url = f"https://img.youtube.com/vi/{vid_id}/{quality}.jpg"
                if thumbnail_ok(url):
                    return url
    return ""


def build_organizer_text(item: dict) -> str:
    """Texto simple para el canal organizador: tipo + título + link directo."""
    ct    = item.get("content_type", "serie")
    label = TYPE_LABELS.get(ct, ct.upper())
    title = item.get("title", "Sin título")
    url   = item.get("url", "")
    src   = item.get("source", "")
    return f"{label}\n\n{title}\n\n🔗 {url}\n📡 {src}"


def get_auto_dest(content_type: str) -> str:
    """
    Devuelve el canal de publicación automática según tipo de contenido.
    Tech/ambiente → CANAL_TECH_AMBIENTE
    Entretenimiento → CANAL_ENTRETENIMIENTO (solo si está configurado con monetización)
    """
    import os
    has_monetization = bool(os.environ.get("MONETIZATION_DOMAIN", "").strip())

    if content_type in TECH_ENV_TYPES:
        return CANAL_TECH_AMBIENTE

    if content_type in ENTERTAINMENT_TYPES and has_monetization:
        return CANAL_ENTRETENIMIENTO

    # Sin monetización: el entretenimiento solo va al canal monetizador para revisión
    return ""


async def _send_photo(bot: Bot, chat_id: str, text: str, thumb: str) -> bool:
    if not chat_id:
        return False
    if thumb:
        try:
            await bot.send_photo(
                chat_id=chat_id,
                photo=thumb,
                caption=text[:MAX_CAPTION],
                parse_mode=None,
            )
            return True
        except TelegramError as e:
            print(f"[Publisher] ⚠️ Foto falló ({e}), enviando sin imagen...")
    return await _send_text(bot, chat_id, text)


async def _send_text(bot: Bot, chat_id: str, text: str) -> bool:
    if not chat_id:
        return False
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=None,
            disable_web_page_preview=False,
        )
        return True
    except TelegramError as e:
        print(f"[Publisher] ❌ Error → {chat_id}: {e}")
        return False


async def publish_item(item: dict, bot: Bot, delay: int = 4) -> bool:
    """
    El ciclo RSS solo envía a Organizador + Monetizador.
    Los canales públicos (Tech/Ambiente y Entretenimiento) solo se publican
    cuando el usuario dispara manualmente desde CANAL_NOTICIAS.
    """
    title_short = item["title"][:55]
    thumbnail   = get_best_thumbnail(item)
    premium     = build_premium_post(item)

    # 1) Canal organizador — texto simple con clasificación
    if CANAL_ORGANIZADOR:
        org_text = build_organizer_text(item)
        await _send_text(bot, CANAL_ORGANIZADOR, org_text)
        await asyncio.sleep(delay)

    # 2) Canal monetizador — formato premium para revisión manual
    if CANAL_MONETIZADOR:
        await _send_photo(bot, CANAL_MONETIZADOR, premium, thumbnail)
        await asyncio.sleep(delay)

    print(f"[Publisher] ✅ → Monetizador: {title_short}")
    return True


async def publish_all(items: list, delay_between_posts: int = 30) -> int:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    published = 0
    for i, item in enumerate(items):
        ok = await publish_item(item, bot)
        if ok:
            published += 1
        if i < len(items) - 1:
            await asyncio.sleep(delay_between_posts)
    return published
