import requests
import re
import urllib.parse
from bs4 import BeautifulSoup

YOUTUBE_SEARCH_URL = "https://www.youtube.com/results?search_query={query}"
OKRU_SEARCH_URL = "https://ok.ru/video?query={query}"

SKIP_KEYWORDS = [
    "trailer", "tráiler", "teaser", "clip", "preview", "avance",
    "resumen", "recap", "promo", "sneak peek", "behind the scenes",
    "making of", "entrevista", "interview", "reaccion", "reaction",
    "minutos", "shorts", "short", "escena", "scene"
]

FULL_KEYWORDS = [
    "capitulo completo", "capítulo completo", "episodio completo",
    "pelicula completa", "película completa", "serie completa",
    "full episode", "full movie", "temporada completa", "season complete"
]

CONTENT_PATTERNS = {
    "novela": ["novela", "telenovela", "novelas", "soap opera"],
    "serie": ["serie", "series", "temporada", "season", "episodio", "episode", "capitulo", "capítulo"],
    "pelicula": ["pelicula", "película", "movie", "film", "cine"],
    "tecnologia": ["tecnologia", "tecnología", "tech", "gadget", "celular", "smartphone", "iphone", "android", "review", "unboxing", "tutorial tech", "aplicacion", "app review"],
}

GENRE_PATTERNS = {
    "romance": ["romance", "amor", "love", "romantica", "romántica"],
    "accion": ["accion", "acción", "action", "aventura", "adventure"],
    "drama": ["drama", "dramatico", "dramático"],
    "comedia": ["comedia", "comedy", "comico", "cómico"],
    "suspenso": ["suspenso", "thriller", "suspense", "misterio", "mystery"],
    "terror": ["terror", "horror", "miedo", "scary"],
    "familiar": ["familiar", "family", "infantil", "kids"],
    "historico": ["historico", "histórico", "historia", "historical", "epoca"],
}


def is_full_content(title: str) -> bool:
    title_lower = title.lower()
    for kw in SKIP_KEYWORDS:
        if kw in title_lower:
            return False
    for kw in FULL_KEYWORDS:
        if kw in title_lower:
            return True
    return True


def detect_content_type(title: str) -> str:
    title_lower = title.lower()
    for content_type, keywords in CONTENT_PATTERNS.items():
        for kw in keywords:
            if kw in title_lower:
                return content_type
    return "serie"


def detect_genres(title: str) -> list:
    title_lower = title.lower()
    found = []
    for genre, keywords in GENRE_PATTERNS.items():
        for kw in keywords:
            if kw in title_lower:
                found.append(genre)
                break
    return found


def search_youtube(query: str, max_results: int = 5) -> list:
    results = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
        titles_raw = re.findall(r'"title":\{"runs":\[\{"text":"([^"]+)"', resp.text)

        seen_ids = set()
        for vid_id, title in zip(video_ids, titles_raw):
            if vid_id in seen_ids:
                continue
            seen_ids.add(vid_id)
            if not is_full_content(title):
                continue
            results.append({
                "title": title,
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "source": "YouTube",
                "content_type": detect_content_type(title),
                "genres": detect_genres(title),
            })
            if len(results) >= max_results:
                break
    except Exception as e:
        print(f"[YouTube] Error buscando '{query}': {e}")
    return results


def search_okru(query: str, max_results: int = 5) -> list:
    results = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://ok.ru/video?query={encoded}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.find_all("a", {"data-type": "video"}, limit=max_results * 3)

        for card in cards:
            href = card.get("href", "")
            title = card.get("aria-label") or card.get("title", "")
            if not title:
                span = card.find("span")
                title = span.get_text(strip=True) if span else ""
            if not title or not href:
                continue
            if not href.startswith("http"):
                href = "https://ok.ru" + href
            if not is_full_content(title):
                continue
            results.append({
                "title": title,
                "url": href,
                "source": "OK.ru",
                "content_type": detect_content_type(title),
                "genres": detect_genres(title),
            })
            if len(results) >= max_results:
                break
    except Exception as e:
        print(f"[OK.ru] Error buscando '{query}': {e}")
    return results


SEARCH_QUERIES = [
    ("novela completa capitulo", "novela"),
    ("telenovela episodio completo", "novela"),
    ("serie capitulo completo español", "serie"),
    ("pelicula completa en español", "pelicula"),
    ("novela turca capitulo completo", "novela"),
    ("serie coreana episodio completo subtitulado", "serie"),
    ("película romantica completa", "pelicula"),
    ("novela brasileña capitulo completo", "novela"),
    ("serie drama completo español", "serie"),
    ("película acción completa", "pelicula"),
    ("review celular 2024 español", "tecnologia"),
    ("unboxing smartphone top", "tecnologia"),
    ("mejores apps android iphone", "tecnologia"),
    ("tecnología gadgets novedades", "tecnologia"),
]


def fetch_all_content(max_per_query: int = 3) -> list:
    all_results = []
    seen_urls = set()

    for query, _ in SEARCH_QUERIES:
        yt_results = search_youtube(query, max_results=max_per_query)
        ok_results = search_okru(query, max_results=max_per_query)

        for item in yt_results + ok_results:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_results.append(item)

    return all_results
