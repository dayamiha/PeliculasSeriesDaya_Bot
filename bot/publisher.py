import asyncio
import os
import random
from telegram import Bot
from telegram.error import TelegramError
from hashtags import generate_hashtags

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# Las tres etapas
CANAL_RECOPILACION = os.environ["TELEGRAM_CHANNEL_ID"]
CANAL_ORGANIZADOR  = os.environ.get("CANAL_ORGANIZADOR") or os.environ["GRUPO_DESTINO"]
CANAL_PUBLICAR     = os.environ["CANAL_FINAL"]

MONETIZATION_DOMAIN = os.environ.get("MONETIZATION_DOMAIN", "")

TYPE_EMOJI = {
    "novela":              "📺",
    "serie":               "🎬",
    "pelicula":            "🎥",
    "documental_ambiente": "🌿",
    "documental_ciencia":  "🔬",
    "documental_historia": "🏛️",
    "tecnologia":          "📱",
}

TYPE_LABEL = {
    "novela":              "NOVELA",
    "serie":               "SERIE",
    "pelicula":            "PELÍCULA",
    "documental_ambiente": "DOCUMENTAL · NATURALEZA",
    "documental_ciencia":  "DOCUMENTAL · CIENCIA",
    "documental_historia": "DOCUMENTAL · HISTORIA",
    "tecnologia":          "TECNOLOGÍA",
}

COPY_TEMPLATES = {
    "novela": [
        "🔥 ¡Este capítulo está rompiendo internet! 🔥\n\n📺 *{title}*\n\n¿Ya lo viste? ¡No te lo puedes perder! 😱",
        "💥 ¡El capítulo del que todos hablan! 💥\n\n📺 *{title}*\n\n¡Corre antes de los spoilers! 🎬",
        "😭 ¡Este capítulo me dejó sin palabras! 😭\n\n📺 *{title}*\n\n¡100% recomendado! 🌟",
        "🚨 CAPÍTULO VIRAL 🚨\n\n📺 *{title}*\n\n¡Todo el mundo lo está viendo! 👀🔥",
    ],
    "serie": [
        "🎬 ¡El episodio que todos esperaban llegó! 🎬\n\n📺 *{title}*\n\n¡No te lo pierdas! 🔥",
        "⚡ NUEVO EPISODIO DISPONIBLE ⚡\n\n📺 *{title}*\n\n¡Corre a verlo! 🍿",
        "🌟 ¡Lo más viral de la semana! 🌟\n\n📺 *{title}*\n\n¡La serie que no puedes dejar! 😍",
        "🏆 ¡Episodio TOP del momento! 🏆\n\n📺 *{title}*\n\n¡Dale play ahora! ▶️",
    ],
    "pelicula": [
        "🎥 ¡La película que está arrasando en internet! 🎥\n\n🎬 *{title}*\n\n¡Palomitas y a disfrutar! 🍿",
        "🌟 CINE EN CASA 🌟\n\n🎬 *{title}*\n\n¡Imperdible! Gratis 🆓",
        "🔥 ¡Esta película está en tendencia! 🔥\n\n🎬 *{title}*\n\n¡Ponla ahora! 🎭",
        "😱 ¡No puedo creer lo buena que está! 😱\n\n🎬 *{title}*\n\n¡Descúbrela! 👇🔥",
    ],
    "documental_ambiente": [
        "🌿 ¡Documental imperdible del planeta! 🌿\n\n🌍 *{title}*\n\n¡La naturaleza en su máxima expresión! 🐾",
        "🌊 ¡Este documental te dejará sin aliento! 🌊\n\n🦁 *{title}*\n\n¡Nuestro planeta es increíble! 🌱",
        "🌎 ¡Para los amantes de la naturaleza! 🌎\n\n🌿 *{title}*\n\n¡Un viaje visual espectacular! ✨",
    ],
    "documental_ciencia": [
        "🔬 ¡Descubrimiento que cambia todo! 🔬\n\n🧬 *{title}*\n\n¡La ciencia más fascinante! 🚀",
        "🌌 ¡El universo tiene secretos increíbles! 🌌\n\n🔭 *{title}*\n\n¡Amplía tu mente! 🧠✨",
        "⚗️ ¡Ciencia que no te enseñan en la escuela! ⚗️\n\n🔬 *{title}*\n\n¡Fascinante! 💡",
    ],
    "documental_historia": [
        "🏛️ ¡La historia que nadie te contó! 🏛️\n\n📜 *{title}*\n\n¡El pasado más increíble! ⚔️",
        "🗿 ¡Civilizaciones que marcaron el mundo! 🗿\n\n🏺 *{title}*\n\n¡Historia pura! 📖✨",
        "⚔️ ¡El documental histórico del momento! ⚔️\n\n🏰 *{title}*\n\n¡No te lo pierdas! 🌍",
    ],
    "tecnologia": [
        "📱 ¡El review que todos esperaban! 📱\n\n🔧 *{title}*\n\n¡Imprescindible antes de comprar! 👀🔥",
        "⚡ TECH ALERT ⚡ ¡Lo más viral en tecnología!\n\n📲 *{title}*\n\n¡No te quedes atrás! 🚀",
        "🤖 ¡Gadget del momento! 🤖\n\n📱 *{title}*\n\n¡Dale play y entérate! 💡",
        "💥 TOP TECH de la semana 💥\n\n🖥️ *{title}*\n\n¡La tecnología que necesitas conocer! 🌐",
    ],
}


def escape_md(text: str) -> str:
    """Escapa caracteres especiales para Telegram Markdown v1."""
    for ch in ("*", "_", "`", "[", "]"):
        text = text.replace(ch, f"\\{ch}")
    return text


def monetize(url: str) -> str:
    if MONETIZATION_DOMAIN:
        clean = url.replace("https://", "").replace("http://", "")
        return f"https://{MONETIZATION_DOMAIN}/?redirect={clean}"
    return url


# ─── ETAPA 1: Canal de recopilación ──────────────────────────────────────────
def build_stage1(item: dict) -> str:
    ct = item.get("content_type", "serie")
    emoji = TYPE_EMOJI.get(ct, "🎬")
    label = TYPE_LABEL.get(ct, ct.upper())
    title = escape_md(item["title"])
    url = monetize(item["url"])
    channel = escape_md(item.get("channel", ""))
    return (
        f"{emoji} *{label}*\n"
        f"📌 {title}\n"
        f"📡 Canal: {channel}\n"
        f"🔗 {url}"
    )


# ─── ETAPA 2: Canal organizador ───────────────────────────────────────────────
def build_stage2(item: dict) -> str:
    ct = item.get("content_type", "serie")
    emoji = TYPE_EMOJI.get(ct, "🎬")
    label = TYPE_LABEL.get(ct, ct.upper())
    title = escape_md(item["title"])
    description = escape_md(item.get("description", "")[:200])
    url = monetize(item["url"])
    hashtags = generate_hashtags(ct, item.get("genres", []), item.get("origins", []), item["title"])

    desc_line = f"\n📝 _{description}_\n" if description else "\n"
    return (
        f"{emoji} *{label}*\n\n"
        f"🎯 *{title}*"
        f"{desc_line}\n"
        f"🔗 {url}\n\n"
        f"{hashtags}"
    )


# ─── ETAPA 3: Canal publicación final ─────────────────────────────────────────
def build_stage3(item: dict) -> str:
    ct = item.get("content_type", "serie")
    templates = COPY_TEMPLATES.get(ct, COPY_TEMPLATES["serie"])
    title = escape_md(item["title"])
    copy = random.choice(templates).format(title=title)
    url = monetize(item["url"])
    hashtags = generate_hashtags(ct, item.get("genres", []), item.get("origins", []), item["title"])
    return (
        f"{copy}\n\n"
        f"🔗 {url}\n\n"
        f"{hashtags}"
    )


async def send(bot: Bot, chat_id: str, text: str) -> bool:
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            disable_web_page_preview=False,
        )
        return True
    except TelegramError as e:
        if "parse" in str(e).lower() or "entities" in str(e).lower():
            # Fallback: enviar sin formato si falla el Markdown
            try:
                plain = text.replace("*", "").replace("_", "").replace("`", "").replace("\\", "")
                await bot.send_message(
                    chat_id=chat_id,
                    text=plain,
                    parse_mode=None,
                    disable_web_page_preview=False,
                )
                return True
            except TelegramError as e2:
                print(f"[Publisher] Error fallback {chat_id}: {e2}")
                return False
        print(f"[Publisher] Error enviando a {chat_id}: {e}")
        return False


async def publish_item(item: dict, bot: Bot, delay: int = 5) -> dict:
    title_short = item["title"][:50]
    results = {"stage1": False, "stage2": False, "stage3": False}

    results["stage1"] = await send(bot, CANAL_RECOPILACION, build_stage1(item))
    if delay:
        await asyncio.sleep(delay)

    results["stage2"] = await send(bot, CANAL_ORGANIZADOR, build_stage2(item))
    if delay:
        await asyncio.sleep(delay)

    results["stage3"] = await send(bot, CANAL_PUBLICAR, build_stage3(item))

    ok = all(results.values())
    status = "✅" if ok else "⚠️"
    print(f"[Publisher] {status} {title_short} → {results}")
    return results


async def publish_all(items: list, delay_between_posts: int = 30) -> int:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    published = 0
    for i, item in enumerate(items):
        result = await publish_item(item, bot)
        if result["stage3"]:
            published += 1
        if i < len(items) - 1:
            await asyncio.sleep(delay_between_posts)
    return published
