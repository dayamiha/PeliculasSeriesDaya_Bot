import asyncio
import os
import random
from collections import defaultdict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application, MessageHandler, TypeHandler, filters, ContextTypes
from rss_reader import fetch_all
from classifier import classify_all
from publisher import publish_all, CANAL_RECOPILACION
from organizer import reenviar_mensaje
from news_router import route_news_message

TELEGRAM_BOT_TOKEN     = os.environ["TELEGRAM_BOT_TOKEN"]
PUBLISH_INTERVAL_HOURS = int(os.environ.get("PUBLISH_INTERVAL_HOURS", "4"))
ITEMS_PER_RUN          = int(os.environ.get("ITEMS_PER_RUN", "8"))
DELAY_BETWEEN_POSTS    = int(os.environ.get("DELAY_BETWEEN_POSTS", "30"))

CANAL_NOTICIAS         = os.environ.get("CANAL_NOTICIAS", "")
CANAL_ORGANIZADOR      = os.environ.get("CANAL_ORGANIZADOR", "")
CANAL_FINAL            = os.environ.get("CANAL_FINAL", "")

seen_urls: set = set()

TYPE_PRIORITY = [
    "novela",
    "serie",
    "anime",
    "pelicula",
    "tecnologia",
    "documental_ambiente",
    "documental_ciencia",
    "documental_historia",
]


def select_diverse(items: list, total: int) -> list:
    by_type = defaultdict(list)
    for item in items:
        by_type[item.get("content_type", "serie")].append(item)

    for t in by_type:
        random.shuffle(by_type[t])

    selected = []
    for t in TYPE_PRIORITY:
        if by_type[t] and len(selected) < total:
            selected.append(by_type[t].pop(0))

    remaining = []
    for t in TYPE_PRIORITY:
        remaining.extend(by_type[t])
    random.shuffle(remaining)

    for item in remaining:
        if len(selected) >= total:
            break
        selected.append(item)

    random.shuffle(selected)
    return selected


async def run_cycle():
    global seen_urls
    print("\n" + "═" * 55)
    print("[Bot] ▶ Iniciando ciclo de publicación...")

    raw = fetch_all(seen_urls)
    if not raw:
        print("[Bot] Sin contenido nuevo.")
        return

    items = classify_all(raw)
    if not items:
        print("[Bot] Todo fue filtrado.")
        return

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

    print(f"[Bot] ✅ Ciclo completo: {count}/{len(selected)} publicados")
    print("═" * 55)


async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja mensajes de canales monitoreados.
    - CANAL_RECOPILACION → organizar contenido de entretenimiento
    - CANAL_NOTICIAS     → enrutar al canal correcto con formato premium
    """
    message = update.channel_post or update.message
    if not message:
        return

    chat        = message.chat
    raw_id      = chat.id                          # ej: -1003862300011
    chat_id_str = str(raw_id)                      # "-1003862300011"
    # Telegram a veces reporta el ID sin el prefijo -100
    alt_id      = "-100" + str(raw_id).lstrip("-") if not str(raw_id).startswith("-100") else chat_id_str
    chat_username = f"@{chat.username}" if chat.username else ""

    print(f"[Bot] 📨 Mensaje de chat: {chat_id_str} ({chat_username}) — {(message.text or message.caption or '')[:60]}")

    # Canal de recopilación de entretenimiento
    recopila_ids = {CANAL_RECOPILACION, alt_id} if CANAL_RECOPILACION else set()
    if CANAL_RECOPILACION and (CANAL_RECOPILACION in (chat_id_str, alt_id, chat_username)):
        await reenviar_mensaje(message)
        return

    # Canal de noticias → enrutar automáticamente al canal público correcto
    if CANAL_NOTICIAS and (CANAL_NOTICIAS in (chat_id_str, alt_id, chat_username)):
        await route_news_message(message)
        return

    print(f"[Bot] ⚠️  Canal no reconocido: {chat_id_str}")


async def main():
    import os as _os
    canal_tech    = _os.environ.get("CANAL_NOTICIAS_TECH", "")
    canal_entret  = _os.environ.get("CANAL_FINAL", "")
    canal_monet   = _os.environ.get("CANAL_MONETIZADOR", "")
    has_monet     = bool(_os.environ.get("MONETIZATION_DOMAIN", "").strip())

    print("═" * 55)
    print("🤖  peliculas_series_novelas_daya  BOT")
    print("═" * 55)
    print(f"  📥 Recopilación  : {CANAL_RECOPILACION}")
    if CANAL_ORGANIZADOR:
        print(f"  🗂️  Organizador   : {CANAL_ORGANIZADOR}")
    if canal_monet:
        print(f"  💰 Monetizador   : {canal_monet} (revisión manual)")
    if canal_tech:
        print(f"  📱 Tech/Ambiente : {canal_tech}")
    if canal_entret:
        print(f"  🎬 Entretenimiento: {canal_entret}")
    if canal_tech or canal_entret:
        print(f"  ↑ Se publican cuando tú envías el link a CANAL_NOTICIAS")
    if CANAL_NOTICIAS:
        print(f"  📰 Noticias src  : {CANAL_NOTICIAS}")
    print(f"  ⏱️  Ciclo         : cada {PUBLISH_INTERVAL_HOURS}h  ·  {ITEMS_PER_RUN} posts")
    print(f"  ⏳ Delay         : {DELAY_BETWEEN_POSTS}s entre posts")
    print("═" * 55)

    await run_cycle()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_cycle, "interval", hours=PUBLISH_INTERVAL_HOURS, id="main_cycle")
    scheduler.start()
    print(f"[Bot] Scheduler activo → próximo ciclo en {PUBLISH_INTERVAL_HOURS}h.")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(TypeHandler(Update, handle_channel_post))
    print("[Bot] Escuchando mensajes en canales configurados...")

    async with app:
        await app.start()
        await app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "channel_post", "edited_channel_post"],
        )
        try:
            while True:
                await asyncio.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            print("[Bot] Deteniendo...")
            scheduler.shutdown()
            await app.updater.stop()
            await app.stop()
