import feedparser
import requests
import re
import urllib.parse
import os
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# ─── Categorías por canal ID ──────────────────────────────────────────────────
CHANNEL_CATEGORIES = {
    "UCBJycsmduvYEL83R_U4JriQ": "tecnologia",       # MKBHD
    "UCXuqSBlHAE6Xw-yeJA0Tunw": "tecnologia",       # Linus Tech Tips
    "UC4QZ_LsYcvcq7qOsOhpAX4A": "tecnologia",       # ColdFusion
    "UCeeFfhMcJa1kjtfZAGskOCA": "tecnologia",       # TechLinked
    "UCpVm7bg6pXKo1Pr6k5kxG9A": "documental_ambiente",  # National Geographic
    "UCwmZiChSryoWQCZMIQezgTg": "documental_ambiente",  # BBC Earth
    "UCsXVk37bltHxD1rDPwtNM8Q": "documental_ciencia",   # SciShow
    "UCWi7N4G6lYWrh7i4yXCOiUQ": "documental_ambiente",  # Our Planet
}

# ─── RSS Feeds (feeds que funcionan) ──────────────────────────────────────────
RSS_FEEDS = [
    # Entretenimiento general
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
    # Tecnología
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCBJycsmduvYEL83R_U4JriQ", "tecnologia"),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCXuqSBlHAE6Xw-yeJA0Tunw", "tecnologia"),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC4QZ_LsYcvcq7qOsOhpAX4A", "tecnologia"),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCeeFfhMcJa1kjtfZAGskOCA", "tecnologia"),
    # Naturaleza / Medio ambiente
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCpVm7bg6pXKo1Pr6k5kxG9A", "documental_ambiente"),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCwmZiChSryoWQCZMIQezgTg", "documental_ambiente"),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCsXVk37bltHxD1rDPwtNM8Q", "documental_ciencia"),
]

# ─── Búsquedas OK.ru por categoría ───────────────────────────────────────────
OKRU_QUERIES = [
    ("novela completa capitulo",     "novela"),
    ("telenovela episodio completo",  "novela"),
    ("novela turca capitulo completo","novela"),
    ("serie capitulo completo español","serie"),
    ("serie coreana episodio completo","serie"),
    ("pelicula completa español",    "pelicula"),
    ("película acción completa",     "pelicula"),
    ("documental naturaleza completo","documental_ambiente"),
    ("documental medio ambiente",    "documental_ambiente"),
    ("documental ciencia español",   "documental_ciencia"),
    ("documental historia completo", "documental_historia"),
    ("tecnologia review gadget",     "tecnologia"),
    ("review celular smartphone",    "tecnologia"),
]

HOURS_LOOKBACK = int(os.environ.get("RSS_HOURS_LOOKBACK", "72"))
OKRU_MAX_PER_QUERY = 4

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
}


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
            description = entry.get("summary", "")[:300]

            items.append({
                "title": title,
                "url": url,
                "description": description,
                "channel": channel_name,
                "channel_id": channel_id,
                "hint_type": hint_type or CHANNEL_CATEGORIES.get(channel_id, ""),
                "source": "YouTube",
                "published": entry.get("published", ""),
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
    SKIP = ["trailer", "tráiler", "teaser", "clip", "promo", "avance",
            "resumen", "recap", "shorts", "short", "entrevista"]
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://ok.ru/video?query={encoded}"
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        # Intenta con data-type="video"
        cards = soup.find_all("a", {"data-type": "video"}, limit=max_results * 4)
        if not cards:
            cards = soup.find_all("a", href=re.compile(r"/video/\d+"), limit=max_results * 4)

        GENERIC = {"смотреть", "watch", "ver", "video", "видео", "онлайн", "online"}
        for card in cards:
            href = card.get("href", "")
            title = card.get("aria-label") or card.get("title", "")
            if not title:
                span = card.find("span")
                title = span.get_text(strip=True) if span else ""
            if not title or not href:
                continue
            if len(title.strip()) < 8:
                continue
            if title.strip().lower() in GENERIC:
                continue
            if not href.startswith("http"):
                href = "https://ok.ru" + href
            if href in seen_urls:
                continue
            if any(k in title.lower() for k in SKIP):
                continue

            results.append({
                "title": title,
                "url": href,
                "description": "",
                "channel": "OK.ru",
                "channel_id": "",
                "hint_type": hint_type,
                "source": "OK.ru",
                "published": "",
            })
            seen_urls.add(href)
            if len(results) >= max_results:
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

    all_items = rss_items + okru_items
    print(f"[Fetch] TOTAL combinado: {len(all_items)}")
    return all_items
