import os
import re
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from classifier import detect_type, detect_genres, detect_origin

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CANAL_ORGANIZADOR  = os.environ.get("CANAL_ORGANIZADOR") or os.environ["GRUPO_DESTINO"]
CANAL_PUBLICAR     = os.environ["CANAL_FINAL"]
MONETIZATION_DOMAIN = os.environ.get("MONETIZATION_DOMAIN", "")

TYPE_LABEL = {
    "novela":              "NOVELA 📺",
    "serie":               "SERIE 🎬",
    "pelicula":            "PELÍCULA 🎥",
    "documental_ambiente": "DOCUMENTAL · NATURALEZA 🌿",
    "documental_ciencia":  "DOCUMENTAL · CIENCIA 🔬",
    "documental_historia": "DOCUMENTAL · HISTORIA 🏛️",
    "tecnologia":          "TECNOLOGÍA 📱",
    "otros":               "CONTENIDO 🔗",
}


def escape_md(text: str) -> str:
    return re.sub(r'([_*[\]()~`>#+\-=|{}.!])', r'\\\1', text)


def build_hashtags(tipo: str) -> str:
    base = {
        "novela":              "#Novela #NovelaCompleta #Telenovela #Streaming",
        "serie":               "#Serie #Episodio #SerieCompleta #Streaming",
        "pelicula":            "#Pelicula #PeliculaCompleta #Cine #Online",
        "documental_ambiente": "#Documental #Naturaleza #MedioAmbiente #Fauna",
        "documental_ciencia":  "#Documental #Ciencia #Descubrimiento #Educacion",
        "documental_historia": "#Documental #Historia #Civilizacion #Historico",
        "tecnologia":          "#Tech #Tecnologia #Gadgets #Review #Innovacion",
        "otros":               "#Viral #Tendencia #Online",
    }
    return base.get(tipo, "#Entretenimiento #Online")


def build_organizer_msg(texto: str, link: str, tipo: str) -> str:
    label = TYPE_LABEL.get(tipo, "CONTENIDO 🔗")
    link_final = f"https://{MONETIZATION_DOMAIN}/?redirect={link}" if MONETIZATION_DOMAIN else link
    texto_corto = escape_md(texto[:250])
    hashtags = build_hashtags(tipo)
    return (
        f"*{label}*\n\n"
        f"{texto_corto}\n\n"
        f"🔗 {link_final}\n\n"
        f"{hashtags}"
    )


async def reenviar_mensaje(message) -> bool:
    texto = message.text or message.caption or ""
    if not texto:
        return False

    entities = message.entities or message.caption_entities or []
    urls = [
        texto[e.offset: e.offset + e.length]
        for e in entities if e.type == "url"
    ]
    if not urls:
        return False

    tipo = detect_type(texto)
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    for link in urls:
        msg = build_organizer_msg(texto, link, tipo)
        try:
            await bot.send_message(
                chat_id=CANAL_ORGANIZADOR,
                text=msg,
                parse_mode="Markdown",
                disable_web_page_preview=False,
            )
            print(f"[Organizer] ✅ [{tipo}] → {CANAL_ORGANIZADOR}: {link[:55]}")
            return True
        except TelegramError as e:
            print(f"[Organizer] Error: {e}")

    return False
