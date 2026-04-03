import feedparser
import requests
import re
import urllib.parse
import os
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# ─── Palabras clave en ruso → tipo de contenido ───────────────────────────────
RUSSIAN_TYPE_MAP = {
    "фильм":          "pelicula",
    "фильмы":         "pelicula",
    "кино":           "pelicula",
    "кинофильм":      "pelicula",
    "сериал":         "serie",
    "сериалы":        "serie",
    "серия":          "serie",
    "эпизод":         "serie",
    "сезон":          "serie",
    "телесериал":     "novela",
    "мелодрама":      "novela",
    "новелла":        "novela",
    "аниме":          "anime",
    "мультфильм":     "anime",
    "мультсериал":    "anime",
    "документальный": "documental_ambiente",
    "документалка":   "documental_ambiente",
    "природа":        "documental_ambiente",
    "дикая природа":  "documental_ambiente",
    "история":        "documental_historia",
    "наука":          "documental_ciencia",
    "технологии":     "tecnologia",
    "гаджет":         "tecnologia",
    "обзор":          "tecnologia",
}

# ─── Canales de YouTube por categoría ─────────────────────────────────────────
CHANNEL_CATEGORIES = {
    "UCBJycsmduvYEL83R_U4JriQ": "tecnologia",
    "UCXuqSBlHAE6Xw-yeJA0Tunw": "tecnologia",
    "UC4QZ_LsYcvcq7qOsOhpAX4A": "tecnologia",
    "UCeeFfhMcJa1kjtfZAGskOCA": "tecnologia",
    "UCpVm7bg6pXKo1Pr6k5kxG9A": "documental_ambiente",
    "UCwmZiChSryoWQCZMIQezgTg": "documental_ambiente",
    "UCsXVk37bltHxD1rDPwtNM8Q": "documental_ciencia",
    "UCWi7N4G6lYWrh7i4yXCOiUQ": "documental_ambiente",
}

# ─── RSS Feeds YouTube ────────────────────────────────────────────────────────
RSS_FEEDS = [
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCRwA1NUcUnwsly35ikGhp0A", ""),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC4JX40jDee_tINbkjycV4Sg", ""),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCp0hYYBW6IMayGgR-WeoCvQ", ""),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC7ZkWBYAAMKgcl1eMjCt3jQ", ""),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCi8e0iOVk1fEOogdfu4YgfA", ""),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCjmJDM5pRKbUlVIzDYYWb6g", ""),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCq0OueAsdxH6b8nyAspwViw", ""),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCVtL1edhT8qqY-j2JIndMzg", ""),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC3gNmTGu-TTbFPpfSs5kNkg", ""),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCx-KWLTKlB83hDI6UKECtJQ", ""),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC2-BeLxzUBSs0uSrmzWhJuQ", ""),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCY30JRSgfhYXA6i6xX1erWg", ""),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCV6KDgJskWaEckne5aPA0aQ", ""),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCBJycsmduvYEL83R_U4JriQ", "tecnologia"),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCXuqSBlHAE6Xw-yeJA0Tunw", "tecnologia"),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC4QZ_LsYcvcq7qOsOhpAX4A", "tecnologia"),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCeeFfhMcJa1kjtfZAGskOCA", "tecnologia"),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCpVm7bg6pXKo1Pr6k5kxG9A", "documental_ambiente"),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCwmZiChSryoWQCZMIQezgTg", "documental_ambiente"),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCsXVk37bltHxD1rDPwtNM8Q", "documental_ciencia"),
]

# ─── Canales de Telegram públicos (t.me/s/) ───────────────────────────────────
# Canales fijos con su tipo de contenido
TELEGRAM_CHANNELS_BUILTIN: list[tuple[str, str]] = [
    # Medio ambiente / Ecología
    ("ecologia_medioambiente",          "documental_ambiente"),
    ("medioambiente_info",              "documental_ambiente"),
    ("Meteorologia_Desde_Cuba",         "documental_ambiente"),
    # Noticias generales (el clasificador filtra política/muertes)
    ("teleSUR_tv",                      ""),
    ("cubadebate",                      ""),
    # Tecnología
    ("ingenieriaengeneral",             "tecnologia"),
    ("techgeniusjvc",                   "tecnologia"),
    ("Wired_Noticias",                  "tecnologia"),
    ("NoticiasTecnologia",              "tecnologia"),
    # Series / Doramas / Novelas
    ("novelas_series_coreanas_doramas", "serie"),
    ("DoramasDeserieenseriecl",         "serie"),
    ("DoramasVipOst",                   "serie"),
    ("series",                          "serie"),
]

# Canales extra via variable de entorno: username:tipo,username2:tipo2
TELEGRAM_CHANNELS_RAW = os.environ.get("TELEGRAM_CHANNELS", "")
TELEGRAM_CHANNELS_EXTRA: list[tuple[str, str]] = []
for _entry in TELEGRAM_CHANNELS_RAW.split(","):
    _entry = _entry.strip()
    if ":" in _entry:
        _u, _h = _entry.split(":", 1)
        TELEGRAM_CHANNELS_EXTRA.append((_u.strip().lstrip("@"), _h.strip()))
    elif _entry:
        TELEGRAM_CHANNELS_EXTRA.append((_entry.lstrip("@"), ""))

TELEGRAM_CHANNELS = TELEGRAM_CHANNELS_BUILTIN + TELEGRAM_CHANNELS_EXTRA

# ─── Búsquedas OK.ru (español + ruso) ────────────────────────────────────────
OKRU_QUERIES = [
    ("novela completa capitulo",            "novela"),
    ("telenovela episodio completo",         "novela"),
    ("novela turca capitulo completo",       "novela"),
    ("novela brasileña capitulo completo",   "novela"),
    ("serie capitulo completo español",      "serie"),
    ("serie coreana episodio completo",      "serie"),
    ("kdrama episodio completo subtitulos",  "serie"),
    ("anime capitulo completo español",      "anime"),
    ("anime episodio subtitulado",           "anime"),
    ("pelicula completa español",            "pelicula"),
    ("película acción completa",             "pelicula"),
    ("pelicula comedia completa",            "pelicula"),
    ("documental naturaleza completo",       "documental_ambiente"),
    ("documental medio ambiente",            "documental_ambiente"),
    ("documental ciencia español",           "documental_ciencia"),
    ("documental historia completo",         "documental_historia"),
    ("tecnologia review gadget",             "tecnologia"),
    ("review celular smartphone",            "tecnologia"),
    # Búsquedas en ruso
    ("фильм полный",                         "pelicula"),
    ("сериал серия полностью",               "serie"),
    ("мелодрама полный фильм",               "novela"),
    ("аниме серия на русском",               "anime"),
    ("документальный фильм природа",         "documental_ambiente"),
    ("документальный история",               "documental_historia"),
]

HOURS_LOOKBACK = int(os.environ.get("RSS_HOURS_LOOKBACK", "72"))
OKRU_MAX_PER_QUERY = 4
MIN_DURATION_SECONDS = 1800  # 30 minutos

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,ru;q=0.8",
}

SKIP_WORDS = [
    "trailer", "tráiler", "teaser", "clip", "promo", "avance",
    "resumen", "recap", "shorts", "short", "entrevista",
    "трейлер", "тизер", "нарезка", "момент", "сцена",
]


# ─── Duración ─────────────────────────────────────────────────────────────────
def parse_duration_text(text: str) -> int:
    """Convierte texto de duración (1:23:45 o 23:45) a segundos."""
    if not text:
        return 0
    text = text.strip()
    parts = text.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    except ValueError:
        pass
    return 0


def is_long_enough(duration_sec: int, content_type: str) -> bool:
    """Filtra videos cortos para tipos que requieren contenido completo."""
    needs_filter = {"pelicula", "novela", "serie", "documental_ambiente",
                    "documental_ciencia", "documental_historia", "anime"}
    if content_type not in needs_filter:
        return True
    if duration_sec == 0:
        return True  # Si no sabemos la duración, lo dejamos pasar
    return duration_sec >= MIN_DURATION_SECONDS


def detect_russian_type(text: str) -> str:
    """Detecta tipo de contenido en texto ruso."""
    t = text.lower()
    for keyword, ctype in RUSSIAN_TYPE_MAP.items():
        if keyword in t:
            return ctype
    return ""


# ─── OK.ru: detalles de video (descripción + duración + thumbnail) ────────────
def get_okru_video_details(video_url: str) -> dict:
    """Visita la página del video en OK.ru y extrae descripción, duración y thumbnail."""
    details = {"description": "", "duration_seconds": 0, "thumbnail": ""}
    try:
        resp = requests.get(video_url, headers=HEADERS, timeout=12)
        if not resp.ok:
            return details
        soup = BeautifulSoup(resp.text, "lxml")

        # Descripción
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            details["description"] = og_desc.get("content", "")[:400]

        # Thumbnail
        og_img = soup.find("meta", property="og:image")
        if og_img:
            details["thumbnail"] = og_img.get("content", "")

        # Duración (og:video:duration en segundos)
        dur_meta = soup.find("meta", property="og:video:duration")
        if dur_meta:
            try:
                details["duration_seconds"] = int(dur_meta.get("content", "0"))
            except ValueError:
                pass

        # Fallback: buscar texto de duración en la página
        if details["duration_seconds"] == 0:
            dur_text = soup.find(class_=re.compile(r"duration|time|вр[еЕ][мМ]я", re.I))
            if dur_text:
                details["duration_seconds"] = parse_duration_text(dur_text.get_text())

    except Exception as e:
        print(f"[OK.ru Details] Error en {video_url[:50]}: {e}")

    return details


# ─── YouTube: thumbnail ───────────────────────────────────────────────────────
def get_youtube_thumbnail(video_url: str) -> str:
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", video_url)
    if match:
        vid_id = match.group(1)
        return f"https://img.youtube.com/vi/{vid_id}/maxresdefault.jpg"
    return ""


# ─── YouTube RSS ──────────────────────────────────────────────────────────────
def fetch_feed(feed_url: str, hint_type: str, seen_urls: set, cutoff: datetime) -> list:
    items = []
    channel_id = feed_url.split("channel_id=")[-1] if "channel_id=" in feed_url else ""

    try:
        feed = feedparser.parse(feed_url)
        if feed.bozo and not feed.entries:
            return items

        channel_name = feed.feed.get("title", "YouTube")

        for entry in feed.entries[:15]:
            url = entry.get("link", "")
            if not url or url in seen_urls:
                continue

            published = entry.get("published_parsed")
            if published:
                pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                if pub_dt < cutoff:
                    continue

            title = entry.get("title", "")
            description = entry.get("summary", "")[:400]
            thumbnail = get_youtube_thumbnail(url)

            items.append({
                "title": title,
                "url": url,
                "description": description,
                "thumbnail": thumbnail,
                "channel": channel_name,
                "channel_id": channel_id,
                "hint_type": hint_type or CHANNEL_CATEGORIES.get(channel_id, ""),
                "source": "YouTube",
                "published": entry.get("published", ""),
                "duration_seconds": 0,
            })
            seen_urls.add(url)

    except Exception as e:
        print(f"[RSS] Error en feed {channel_id[:12]}: {e}")

    return items


def fetch_all_rss(seen_urls: set, cutoff: datetime) -> list:
    results = []
    for feed_url, hint_type in RSS_FEEDS:
        items = fetch_feed(feed_url, hint_type, seen_urls, cutoff)
        if items:
            ch = feed_url.split("channel_id=")[-1][:14]
            print(f"[RSS] {len(items):2d} de {ch}  ({hint_type or 'general'})")
        results.extend(items)
    return results


# ─── OK.ru scraper ────────────────────────────────────────────────────────────
def search_okru(query: str, hint_type: str, seen_urls: set, max_results: int = OKRU_MAX_PER_QUERY) -> list:
    results = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://ok.ru/video?query={encoded}"
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.find_all("a", {"data-type": "video"}, limit=max_results * 5)
        if not cards:
            cards = soup.find_all("a", href=re.compile(r"/video/\d+"), limit=max_results * 5)

        GENERIC = {"смотреть", "watch", "ver", "video", "видео", "онлайн", "online"}
        found = 0

        for card in cards:
            href = card.get("href", "")
            title = card.get("aria-label") or card.get("title", "")
            if not title:
                span = card.find("span")
                title = span.get_text(strip=True) if span else ""
            if not title or not href:
                continue
            if len(title.strip()) < 6:
                continue
            if title.strip().lower() in GENERIC:
                continue
            if not href.startswith("http"):
                href = "https://ok.ru" + href
            if href in seen_urls:
                continue
            if any(k in title.lower() for k in SKIP_WORDS):
                continue

            # Detectar tipo por palabras clave rusas si no hay hint
            effective_hint = hint_type or detect_russian_type(title)

            # Obtener detalles del video (descripción, duración, thumbnail)
            details = get_okru_video_details(href)
            description = details["description"]
            duration_sec = details["duration_seconds"]
            thumbnail = details["thumbnail"]

            # Si no se detectó tipo en el título, intentar con la descripción
            if not effective_hint and description:
                effective_hint = detect_russian_type(description)

            # Filtrar por duración (solo contenido que requiere >30 min)
            if not is_long_enough(duration_sec, effective_hint or "serie"):
                print(f"[OK.ru] ⏱ Muy corto ({duration_sec}s): {title[:40]}")
                continue

            results.append({
                "title": title,
                "url": href,
                "description": description,
                "thumbnail": thumbnail,
                "channel": "OK.ru",
                "channel_id": "",
                "hint_type": effective_hint,
                "source": "OK.ru",
                "published": "",
                "duration_seconds": duration_sec,
            })
            seen_urls.add(href)
            found += 1
            if found >= max_results:
                break

    except Exception as e:
        print(f"[OK.ru] Error '{query[:30]}': {e}")

    return results


def fetch_all_okru(seen_urls: set) -> list:
    results = []
    for query, hint_type in OKRU_QUERIES:
        items = search_okru(query, hint_type, seen_urls)
        if items:
            print(f"[OK.ru] {len(items):2d} de '{query[:35]}'")
        results.extend(items)
    return results


# ─── Telegram canales públicos (t.me/s/) ─────────────────────────────────────
def fetch_telegram_channel(username: str, hint_type: str, seen_urls: set) -> list:
    """Scrape mensajes de un canal público de Telegram via t.me/s/."""
    results = []
    try:
        url = f"https://t.me/s/{username}"
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if not resp.ok:
            return results

        soup = BeautifulSoup(resp.text, "lxml")
        messages = soup.find_all("div", class_="tgme_widget_message_bubble")

        for msg in messages[:20]:
            # Buscar links en el mensaje
            links = msg.find_all("a", href=True)
            text_el = msg.find(class_="tgme_widget_message_text")
            text = text_el.get_text(" ", strip=True) if text_el else ""

            for link in links:
                href = link.get("href", "")
                if not href or href.startswith("https://t.me"):
                    continue
                if href in seen_urls:
                    continue
                if any(k in text.lower() for k in SKIP_WORDS):
                    continue

                # Thumbnail del preview si hay imagen
                thumb_el = msg.find("img")
                thumbnail = thumb_el.get("src", "") if thumb_el else ""

                results.append({
                    "title": text[:120] or href,
                    "url": href,
                    "description": text[:400],
                    "thumbnail": thumbnail,
                    "channel": f"@{username}",
                    "channel_id": "",
                    "hint_type": hint_type,
                    "source": "Telegram",
                    "published": "",
                    "duration_seconds": 0,
                })
                seen_urls.add(href)

    except Exception as e:
        print(f"[Telegram] Error en @{username}: {e}")

    return results


def fetch_all_telegram(seen_urls: set) -> list:
    results = []
    for username, hint_type in TELEGRAM_CHANNELS:
        items = fetch_telegram_channel(username, hint_type, seen_urls)
        if items:
            print(f"[Telegram] {len(items):2d} de @{username}  ({hint_type or 'general'})")
        results.extend(items)
    return results


# ─── Combinado ────────────────────────────────────────────────────────────────
def fetch_all(seen_urls: set = None) -> list:
    if seen_urls is None:
        seen_urls = set()

    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_LOOKBACK)

    print("[Fetch] Leyendo feeds YouTube RSS...")
    rss_items = fetch_all_rss(seen_urls, cutoff)
    print(f"[Fetch] RSS total: {len(rss_items)}")

    print("[Fetch] Buscando en OK.ru...")
    okru_items = fetch_all_okru(seen_urls)
    print(f"[Fetch] OK.ru total: {len(okru_items)}")

    tg_items = []
    if TELEGRAM_CHANNELS:
        print("[Fetch] Leyendo canales de Telegram...")
        tg_items = fetch_all_telegram(seen_urls)
        print(f"[Fetch] Telegram total: {len(tg_items)}")

    all_items = rss_items + okru_items + tg_items
    print(f"[Fetch] TOTAL combinado: {len(all_items)}")
    return all_items
