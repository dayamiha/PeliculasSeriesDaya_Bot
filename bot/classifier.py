CONTENT_PATTERNS = {
    "novela": [
        "novela", "telenovela", "soap opera", "novelas", "capitulo", "capítulo",
    ],
    "serie": [
        "serie", "series", "episodio", "episode", "temporada", "season",
        "kdrama", "k-drama", "dorama", "anime",
    ],
    "pelicula": [
        "pelicula", "película", "movie", "film", "cine", "largometraje",
    ],
    "documental_ambiente": [
        "naturaleza", "nature", "ecosistema", "ecosystem", "fauna", "flora",
        "medio ambiente", "medioambiente", "environment", "wildlife", "ocean",
        "oceano", "planeta", "planet", "conservacion", "conservation",
        "national geographic", "bbc earth", "our planet", "clima", "climate",
        "selva", "jungle", "desierto", "desert", "arctic", "antarctic",
    ],
    "documental_ciencia": [
        "ciencia", "science", "scishow", "fisica", "physics", "quimica",
        "chemistry", "biologia", "biology", "espacio", "space", "cosmos",
        "universo", "universe", "nasa", "experimento", "experiment",
        "investigacion", "discovery", "descubrimiento",
    ],
    "documental_historia": [
        "historia", "history", "historico", "histórico", "ancient", "antiguo",
        "guerra", "war", "civilizacion", "civilization", "imperio", "empire",
        "arqueologia", "archaeology", "medieval", "viking", "egipto", "egypt",
    ],
    "tecnologia": [
        "tech", "tecnologia", "tecnología", "gadget", "smartphone", "celular",
        "iphone", "android", "review", "unboxing", "hardware", "software",
        "inteligencia artificial", "ai", "robot", "innovacion", "innovation",
        "mkbhd", "linus", "cpu", "gpu", "laptop", "pc build", "app",
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
]

FULL_KEYWORDS = [
    "capitulo completo", "capítulo completo", "episodio completo",
    "pelicula completa", "película completa", "serie completa",
    "full episode", "full movie", "temporada completa",
    "documental completo", "full documentary",
]


def is_skip(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in SKIP_KEYWORDS)


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
    return origins


def classify(item: dict) -> dict:
    title = item.get("title", "")
    description = item.get("description", "")
    hint_type = item.get("hint_type", "")

    item["skip"] = is_skip(title)
    item["content_type"] = detect_type(title, description, hint_type)
    item["genres"] = detect_genres(title, description)
    item["origins"] = detect_origin(title, description)
    return item


def classify_all(items: list) -> list:
    classified = []
    for item in items:
        c = classify(item)
        if not c["skip"]:
            classified.append(c)
    skipped = len(items) - len(classified)
    if skipped:
        print(f"[Classifier] Filtrados {skipped} trailers/clips. Válidos: {len(classified)}")
    return classified
