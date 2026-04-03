CONTENT_PATTERNS = {
    "novela": [
        "novela", "telenovela", "soap opera", "novelas", "capitulo", "capítulo",
        "мелодрама", "новелла", "телесериал",
    ],
    "serie": [
        "serie", "series", "episodio", "episode", "temporada", "season",
        "kdrama", "k-drama", "dorama", "сериал", "серия", "эпизод", "сезон",
    ],
    "anime": [
        "anime", "manga", "shonen", "shojo", "isekai", "аниме", "мультсериал",
        "naruto", "dragon ball", "one piece", "attack on titan", "demon slayer",
        "my hero academia", "jujutsu", "bleach", "boruto",
    ],
    "pelicula": [
        "pelicula", "película", "movie", "film", "cine", "largometraje",
        "фильм", "кино", "кинофильм",
    ],
    "documental_ambiente": [
        "naturaleza", "nature", "ecosistema", "ecosystem", "fauna", "flora",
        "medio ambiente", "medioambiente", "environment", "wildlife", "ocean",
        "oceano", "planeta", "planet", "conservacion", "conservation",
        "national geographic", "bbc earth", "our planet", "clima", "climate",
        "selva", "jungle", "desierto", "desert", "arctic", "antarctic",
        "природа", "дикая природа", "документальный природа",
    ],
    "documental_ciencia": [
        "ciencia", "science", "scishow", "fisica", "physics", "quimica",
        "chemistry", "biologia", "biology", "espacio", "space", "cosmos",
        "universo", "universe", "nasa", "experimento", "experiment",
        "investigacion", "discovery", "descubrimiento",
        "наука", "физика", "химия", "биология", "космос",
    ],
    "documental_historia": [
        "historia", "history", "historico", "histórico", "ancient", "antiguo",
        "guerra", "war", "civilizacion", "civilization", "imperio", "empire",
        "arqueologia", "archaeology", "medieval", "viking", "egipto", "egypt",
        "история", "древний", "война", "цивилизация",
    ],
    "tecnologia": [
        "tech", "tecnologia", "tecnología", "gadget", "smartphone", "celular",
        "iphone", "android", "review", "unboxing", "hardware", "software",
        "inteligencia artificial", "ai", "robot", "innovacion", "innovation",
        "mkbhd", "linus", "cpu", "gpu", "laptop", "pc build", "app",
        "технологии", "гаджет", "обзор",
    ],
}

GENRE_PATTERNS = {
    "accion": ["accion", "acción", "action", "aventura", "adventure", "fight"],
    "romance": ["romance", "amor", "love", "romantica", "romántica", "pareja"],
    "drama": ["drama", "dramatico", "dramático", "emotional"],
    "comedia": ["comedia", "comedy", "comico", "cómico", "humor", "funny"],
    "suspenso": ["suspenso", "thriller", "suspense", "misterio", "mystery", "crimen", "crime"],
    "terror": ["terror", "horror", "miedo", "scary", "supernatural"],
    "familiar": ["familiar", "family", "infantil", "kids", "animacion", "animación"],
    "historico": ["historico", "histórico", "historia", "historical", "epoca", "period"],
    "ciencia_ficcion": ["ciencia ficcion", "sci-fi", "scifi", "futuro", "future", "space opera"],
}

SKIP_KEYWORDS = [
    "trailer", "tráiler", "teaser", "clip", "promo", "avance",
    "resumen", "recap", "sneak peek", "behind the scenes",
    "making of", "entrevista", "interview", "reaccion", "reaction",
    "shorts", "short", "#shorts",
    "трейлер", "тизер", "нарезка", "сцена", "момент",
]

FULL_KEYWORDS = [
    "capitulo completo", "capítulo completo", "episodio completo",
    "pelicula completa", "película completa", "serie completa",
    "full episode", "full movie", "temporada completa",
    "documental completo", "full documentary",
    "полный фильм", "полная серия", "полностью",
]

# ─── Filtros de noticias / política / muertes ─────────────────────────────────
# Solo para contenido que NO tiene una categoría válida detectada (tipo genérico)
NEWS_KEYWORDS = [
    "breaking news", "última hora", "hoy en las noticias", "en vivo", "en directo",
    "noticiero", "telediario", "informativo", "reportaje", "corresponsal",
    "periodico", "diario ", " cnn", " telemundo", "univisión",
    "новости", "срочно",
]

# Palabras fuertes de política — se aplican a TODOS los tipos
HARD_POLITICAL_KEYWORDS = [
    "elecciones", "congreso", "senado", "parlamento", "candidato", "votacion",
    "oposicion", "decreto", "ministerio", "gobernador", "alcalde", "diputado",
    "senador", "legislacion", "ley aprobada", "golpe de estado", "embajada",
    "политика", "правительство", "выборы", "президент",
]

# Palabras de política suave — solo filtran cuando el tipo no está bien definido
SOFT_POLITICAL_KEYWORDS = [
    "política", "politica", "gobierno", "presidente", "partido", "democracia",
    "reforma", "ministro",
]

DEATH_KEYWORDS = [
    "fallecio", "falleció", "fallecidos", "asesinado", "asesinatos",
    "homicidio", "masacre", "bombardeo", "accidente fatal",
    "obituario", "luto", "duelo", "condolencias", "funeral",
    "убит", "смерть", "погиб", "жертвы",
]

CRYPTO_KEYWORDS = [
    "bitcoin", "ethereum", "crypto", "criptomoneda", "blockchain",
    "nft", "token", "altcoin", "defi", "trading", "forex",
]

ADULT_KEYWORDS = [
    "xxx", "porno", "pornografia", "adulto", "contenido adulto",
    "onlyfans", "escort", "sexy video",
]

# Tipos que tienen señal de contenido propia — aplicar filtros suavizados
STRONG_CONTENT_TYPES = {
    "tecnologia", "documental_ciencia", "documental_historia",
    "documental_ambiente", "novela", "serie", "anime", "pelicula",
}


def is_skip(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in SKIP_KEYWORDS)


def is_hard_filter(title: str, description: str = "") -> bool:
    """Filtros duros: siempre se aplican independientemente del tipo de contenido."""
    text = (title + " " + description).lower()
    return (
        any(k in text for k in HARD_POLITICAL_KEYWORDS)
        or any(k in text for k in DEATH_KEYWORDS)
        or any(k in text for k in CRYPTO_KEYWORDS)
        or any(k in text for k in ADULT_KEYWORDS)
    )


def is_soft_filter(title: str, description: str = "") -> bool:
    """Filtros suaves: solo para contenido sin categoría clara (tipo 'serie' por defecto)."""
    text = (title + " " + description).lower()
    return (
        any(k in text for k in NEWS_KEYWORDS)
        or any(k in text for k in SOFT_POLITICAL_KEYWORDS)
    )


def should_filter(title: str, description: str = "", content_type: str = "serie") -> bool:
    """
    Decide si filtrar un item.
    - Filtros duros (política fuerte, muertes, crypto, adultos): siempre.
    - Filtros suaves (noticias genéricas, política leve): solo si el tipo no es reconocido.
    """
    if is_hard_filter(title, description):
        return True
    # Si el tipo ya fue detectado claramente, no aplicar filtros suaves
    if content_type in STRONG_CONTENT_TYPES:
        return False
    return is_soft_filter(title, description)


def detect_type(title: str, description: str = "", hint_type: str = "") -> str:
    if hint_type:
        return hint_type

    text = (title + " " + description).lower()

    for content_type, keywords in CONTENT_PATTERNS.items():
        for kw in keywords:
            if kw in text:
                return content_type

    return "serie"


def detect_genres(title: str, description: str = "") -> list:
    text = (title + " " + description).lower()
    found = []
    for genre, keywords in GENRE_PATTERNS.items():
        for kw in keywords:
            if kw in text:
                found.append(genre)
                break
    return found


def detect_origin(title: str, description: str = "") -> list:
    text = (title + " " + description).lower()
    origins = []
    if any(x in text for x in ["turca", "turco", "turkey", "turkish"]):
        origins.append("turca")
    if any(x in text for x in ["coreana", "korea", "korean", "kdrama"]):
        origins.append("coreana")
    if any(x in text for x in ["brasileña", "brasil", "brazil", "brazilian"]):
        origins.append("brasileña")
    if any(x in text for x in ["colombiana", "colombia", "colombian"]):
        origins.append("colombiana")
    if any(x in text for x in ["mexicana", "mexico", "méxico", "mexican"]):
        origins.append("mexicana")
    if any(x in text for x in ["india", "indian", "bollywood", "hindi"]):
        origins.append("india")
    if any(x in text for x in ["japonesa", "japones", "japanese", "japon", "japan"]):
        origins.append("japonesa")
    if any(x in text for x in ["china", "chinese", "chino"]):
        origins.append("china")
    return origins


def classify(item: dict) -> dict:
    title = item.get("title", "")
    description = item.get("description", "")
    hint_type = item.get("hint_type", "")

    item["skip"] = is_skip(title)
    # Detectar tipo primero para poder aplicar filtros contextuales
    ct = detect_type(title, description, hint_type)
    item["content_type"] = ct
    item["filtered"] = should_filter(title, description, content_type=ct)
    item["genres"] = detect_genres(title, description)
    item["origins"] = detect_origin(title, description)
    return item


def classify_all(items: list) -> list:
    classified = []
    filtered_count = 0
    skipped_count = 0

    for item in items:
        c = classify(item)
        if c["skip"]:
            skipped_count += 1
        elif c.get("filtered"):
            filtered_count += 1
            print(f"[Classifier] 🚫 Filtrado (noticias/política): {c['title'][:50]}")
        else:
            classified.append(c)

    if skipped_count:
        print(f"[Classifier] Trailers/clips descartados: {skipped_count}")
    if filtered_count:
        print(f"[Classifier] Noticias/política descartados: {filtered_count}")
    print(f"[Classifier] Válidos para publicar: {len(classified)}")
    return classified
