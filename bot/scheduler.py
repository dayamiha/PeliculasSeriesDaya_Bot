import asyncio
import os
import random
from collections import defaultdict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from rss_reader import fetch_all
from classifier import classify_all
from publisher import publish_all, CANAL_RECOPILACION, CANAL_ORGANIZADOR, CANAL_PUBLICAR
from organizer import reenviar_mensaje

TELEGRAM_BOT_TOKEN     = os.environ["TELEGRAM_BOT_TOKEN"]
PUBLISH_INTERVAL_HOURS = int(os.environ.get("PUBLISH_INTERVAL_HOURS", "4"))
ITEMS_PER_RUN          = int(os.environ.get("ITEMS_PER_RUN", "8"))
DELAY_BETWEEN_POSTS    = int(os.environ.get("DELAY_BETWEEN_POSTS", "30"))

seen_urls: set = set()

TYPE_PRIORITY = [
    "novela",
    "serie",
    "pelicula",
    "tecnologia",
    "documental_ambiente",
    "documental_ciencia",
    "documental_historia",
]


def select_diverse(items: list, total: int) -> list:
    """
    Selecciona `total` ítems garantizando diversidad de categorías.
    Toma al menos 1 de cada categoría disponible, luego rellena con el resto.
    """
    by_type = defaultdict(list)
    for item in items:
        by_type[item.get("content_type", "serie")].append(item)

    # Mezcla cada grupo
    for t in by_type:
        random.shuffle(by_type[t])

    selected = []
    # Primero 1 de cada tipo disponible (en orden de prioridad)
    for t in TYPE_PRIORITY:
        if by_type[t] and len(selected) < total:
            selected.append(by_type[t].pop(0))

    # Rellena con los sobrantes hasta alcanzar `total`
    remaining = []
    for t in TYPE_PRIORITY:
        remaining.extend(by_type[t])
    random.shuffle(remaining)

    for item in remaining:
        if len(selected) >= total:
            break
        selected.append(item)

    random.shuffle(selected)  # mezcla final para no publicar siempre en el mismo orden
    return selected


async def run_cycle():
    global seen_urls
    print("\n" + "═" * 50)
    print("[Bot] ▶ Iniciando ciclo de publicación...")

    raw = fetch_all(seen_urls)
    if not raw:
        print("[Bot] Sin contenido nuevo.")
        return

    items = classify_all(raw)
    if not items:
        print("[Bot] Todo fue filtrado.")
        return

    # Resumen por tipo
    by_type = defaultdict(int)
    for i in items:
        by_type[i.get("content_type", "?")] += 1
    summary = "  ".join(f"{t}:{n}" for t, n in sorted(by_type.items()))
    print(f"[Bot] Disponibles: {len(items)}  |  {summary}")

    selected = select_diverse(items, ITEMS_PER_RUN)
    sel_summary = "  ".join(
        f"{t}:{sum(1 for x in selected if x.get('content_type') == t)}"
        for t in TYPE_PRIORITY
        if any(x.get('content_type') == t for x in selected)
    )
    print(f"[Bot] Seleccionados: {len(selected)}  |  {sel_summary}")

    count = await publish_all(selected, delay_between_posts=DELAY_BETWEEN_POSTS)

    for item in selected:
        seen_urls.add(item["url"])

    print(f"[Bot] ✅ Ciclo completo: {count}/{len(selected)} publicados en 3 canales")
    print("═" * 50)


async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.channel_post or update.message
    if not message:
        return
    chat = message.chat
    chat_id_str = str(chat.id)
    chat_username = f"@{chat.username}" if chat.username else ""
    if CANAL_RECOPILACION in (chat_id_str, chat_username):
        await reenviar_mensaje(message)


async def main():
    print("═" * 50)
    print("🤖  peliculas_series_novelas_daya  BOT")
    print("═" * 50)
    print(f"  📥 Recopilación : {CANAL_RECOPILACION}")
    print(f"  🗂️  Organización : {CANAL_ORGANIZADOR}")
    print(f"  📢 Publicación  : {CANAL_PUBLICAR}")
    print(f"  ⏱️  Ciclo        : cada {PUBLISH_INTERVAL_HOURS}h  ·  {ITEMS_PER_RUN} posts")
    print(f"  ⏳ Delay        : {DELAY_BETWEEN_POSTS}s entre posts")
    print("═" * 50)

    await run_cycle()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_cycle, "interval", hours=PUBLISH_INTERVAL_HOURS, id="main_cycle")
    scheduler.start()
    print(f"[Bot] Scheduler activo → próximo ciclo en {PUBLISH_INTERVAL_HOURS}h.")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(
        filters.ChatType.CHANNEL | filters.ChatType.GROUPS,
        handle_channel_post
    ))
    print("[Organizer] Escuchando mensajes del canal de recopilación...")

    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        try:
            while True:
                await asyncio.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            print("[Bot] Deteniendo...")
            scheduler.shutdown()
            await app.updater.stop()
            await app.stop()
