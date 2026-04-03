"""
Generador de contenido premium para Telegram.
- Entretenimiento (series/novela/anime/pelicula): formato A (descriptivo) o B (hook)
- Tech/ambiente/documentales: siempre formato A (síntesis inteligente, sin viral)
- Siempre muestra DOS enlaces: el que irá monetizado + el original de acceso directo
"""
import os
import re
import random
import html

MONETIZATION_DOMAIN = os.environ.get("MONETIZATION_DOMAIN", "").strip()
MONETIZATION_NAME   = os.environ.get("MONETIZATION_NAME", "").strip()

# Todos los tipos soportan hooks virales
# Los filtros de muertes/política/guerra/crypto se aplican en el classifier, no aquí
ENTERTAINMENT_TYPES = {"novela", "serie", "anime", "pelicula"}  # solo para referencia interna

# ── Encabezados ───────────────────────────────────────────────────────────────
TYPE_HEADERS = {
    "novela":              ("📺", "Novela Completa"),
    "serie":               ("🎬", "Serie Completa"),
    "anime":               ("🌸", "Anime Completo"),
    "pelicula":            ("🎬", "Estreno de Película"),
    "documental_ambiente": ("🌿", "Documental · Naturaleza"),
    "documental_ciencia":  ("🔬", "Documental · Ciencia"),
    "documental_historia": ("🏛️", "Documental · Historia"),
    "tecnologia":          ("📱", "Tech & Gadgets"),
}

# ── Hooks virales para TODAS las categorías ──────────────────────────────────
HOOKS = {
    "novela": [
        ("🤯", "Este capítulo lo cambia TODO…"),
        ("😱", "Nadie esperaba este giro en la trama…"),
        ("💔", "Imposible no llorar con lo que pasa aquí…"),
        ("🔥", "El capítulo más viral del año llegó…"),
        ("😭", "La escena más emotiva de toda la serie…"),
        ("💥", "Este capítulo explota en redes…"),
    ],
    "serie": [
        ("⚡", "El episodio que nadie puede dejar de ver…"),
        ("🔥", "Esta serie está en lo más alto del ranking…"),
        ("🎭", "Una actuación que te dejará sin palabras…"),
        ("💡", "El episodio que lo explica todo…"),
        ("🏆", "Ganadora de premios por una razón…"),
    ],
    "anime": [
        ("⚔️", "El capítulo que el fandom esperaba…"),
        ("🌸", "Animación que te deja sin aliento…"),
        ("💥", "La batalla más épica de la temporada…"),
        ("🔥", "¡El hype era real! Este capítulo lo confirma…"),
        ("✨", "Magia, acción y drama en un solo episodio…"),
    ],
    "pelicula": [
        ("🤯", "Esta película está rompiendo Internet…"),
        ("🎬", "La producción que todos están viendo ahora…"),
        ("😱", "No puedo creer que sea gratis…"),
        ("🏆", "Premios merecidos — tú decides…"),
        ("🎭", "Actuaciones que te ponen la piel de gallina…"),
        ("🔥", "El final te dejará con la boca abierta…"),
    ],
    "documental_ambiente": [
        ("🌍", "Esto le está pasando a nuestro planeta ahora mismo…"),
        ("🦁", "Imágenes que nunca antes habías visto de la naturaleza…"),
        ("🌊", "El planeta muestra su cara más impresionante aquí…"),
        ("🌱", "Lo que le estamos haciendo al medio ambiente es urgente…"),
        ("🔥", "El documental que todo el mundo debería ver…"),
        ("😱", "No imaginas lo que están descubriendo en la naturaleza…"),
    ],
    "documental_ciencia": [
        ("🔬", "Un descubrimiento que cambia la ciencia para siempre…"),
        ("🌌", "El universo guarda secretos que te dejarán sin palabras…"),
        ("🧠", "Esto expande la mente de cualquiera que lo ve…"),
        ("🚀", "La ciencia más fascinante explicada de forma increíble…"),
        ("💡", "Lo que la escuela nunca te enseñó está aquí…"),
        ("🤯", "Los científicos confirmaron algo que cambia todo…"),
    ],
    "documental_historia": [
        ("🏛️", "La historia real que nadie te contó en la escuela…"),
        ("⚔️", "El secreto histórico que cambia cómo entendemos el pasado…"),
        ("🗿", "Esta civilización dominó el mundo y casi nadie lo sabe…"),
        ("📜", "Lo que realmente ocurrió está documentado aquí…"),
        ("🌍", "El evento que cambió el curso de la historia para siempre…"),
        ("😱", "La verdad histórica que los libros no muestran…"),
    ],
    "tecnologia": [
        ("📱", "El review que todos estaban esperando llegó…"),
        ("⚡", "Este gadget está cambiando las reglas del juego…"),
        ("🤖", "La tecnología del futuro ya está disponible hoy…"),
        ("💡", "Antes de comprarlo necesitas ver esto…"),
        ("🔥", "Lo más viral en tech esta semana está aquí…"),
        ("🚀", "Esta innovación nadie puede ignorar…"),
        ("😱", "No puedo creer lo que acaban de lanzar…"),
        ("🤯", "Esto va a cambiar la forma en que usas la tecnología…"),
    ],
}

# ── Acciones por tipo ─────────────────────────────────────────────────────────
ACTIONS = {
    "novela":              ["📺 Mira el capítulo completo aquí", "📺 Dale play y no pares de ver"],
    "serie":               ["🎬 Mira el episodio completo ahora", "🎬 ¡Dale play y disfrútalo ya!"],
    "anime":               ["🌸 Capítulo completo disponible ahora", "⚔️ ¡Dale play y vívelo!"],
    "pelicula":            ["🎬 Disfruta la película completa", "🎬 La película completa disponible aquí"],
    "documental_ambiente": ["🌿 Mira el documental completo ahora", "🌍 El documental completo aquí"],
    "documental_ciencia":  ["🔬 Mira el documental completo", "🚀 El documental completo disponible"],
    "documental_historia": ["🏛️ Descubre la historia completa aquí", "📜 El documental histórico completo"],
    "tecnologia":          ["📱 Mira el video completo ahora", "⚡ El análisis completo disponible aquí"],
}

# ── Síntesis por tipo ─────────────────────────────────────────────────────────
SYNTHESIS_TEMPLATES = {
    "novela": [
        "Capítulo cargado de emociones que no puedes dejar pasar. La trama avanza y los personajes enfrentan su momento más crítico.",
        "Giros inesperados y emociones a flor de piel en este episodio que engancha desde el primer segundo.",
        "La historia continúa con fuerza. Nuevos conflictos, revelaciones y un final que lo cambia todo.",
    ],
    "serie": [
        "Un episodio que sube el nivel de toda la temporada. Actuaciones brillantes y una trama que mantiene al espectador en tensión constante.",
        "Todo lo que esperabas y más. La narrativa se profundiza y los personajes alcanzan nuevas dimensiones.",
        "La serie que arrasa llega con un nuevo episodio imperdible. Calidad cinematográfica en cada escena.",
    ],
    "anime": [
        "Animación de alto nivel, historia profunda y acción que no para. Un capítulo que el fandom no olvidará.",
        "Cada frame es una obra de arte. Este capítulo combina drama, acción y momentos que dejan sin aliento.",
        "La serie continúa con un episodio lleno de revelaciones y batallas épicamente ejecutadas.",
    ],
    "pelicula": [
        "Una producción que combina historia poderosa con ejecución técnica impecable. De esas que se quedan contigo.",
        "Cine de calidad: guión sólido, actuaciones memorables y una dirección que no falla en ningún momento.",
        "Una película que justifica cada minuto de su duración. Historia bien contada, emocionalmente honesta.",
    ],
    "documental_ambiente": [
        "Imágenes impresionantes de nuestro planeta que documentan la belleza y fragilidad de los ecosistemas naturales.",
        "Un recorrido visual por la fauna y los paisajes más extraordinarios del mundo, con narración científica rigurosa.",
        "La naturaleza en su estado más puro: fauna salvaje, ecosistemas amenazados y la urgencia de protegerlos.",
        "Documental que combina fotografía de alto nivel con datos contrastados sobre el estado actual del planeta.",
    ],
    "documental_ciencia": [
        "Un viaje por los últimos descubrimientos científicos explicados con claridad y rigor. Ideal para mentes curiosas.",
        "Ciencia accesible y apasionante: desde partículas subatómicas hasta los confines del universo observable.",
        "Investigaciones de vanguardia que están cambiando la comprensión humana del mundo natural y el cosmos.",
        "El documental presenta evidencia actualizada sobre fenómenos que definen nuestra era científica.",
    ],
    "documental_historia": [
        "Historia documentada con fuentes primarias y análisis experto. Civilizaciones, conflictos y personajes que moldearon el mundo.",
        "Un recorrido riguroso por eventos históricos que siguen siendo relevantes para entender el presente.",
        "Arqueología, archivos y testimonios convergen en un relato histórico que sorprende por su profundidad.",
        "La historia real, sin simplificaciones: complejidad política, social y cultural de las grandes civilizaciones.",
    ],
    "tecnologia": [
        "Análisis técnico detallado con pruebas reales. Información objetiva antes de tomar cualquier decisión de compra o uso.",
        "Cobertura exhaustiva de las novedades tecnológicas: especificaciones, rendimiento y contexto de mercado.",
        "Review honesto con benchmarks y comparativas. Todo lo que necesitas saber sobre este producto o innovación.",
        "Las tendencias tecnológicas del momento explicadas con rigor: impacto, adopción y perspectivas a futuro.",
    ],
}


def clean_text(text: str, max_len: int = 220) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > max_len:
        text = text[:max_len].rsplit(' ', 1)[0] + '…'
    return text


def generate_synthesis(title: str, description: str, content_type: str) -> str:
    """Síntesis inteligente: usa la descripción si es útil, si no usa plantilla."""
    cleaned = clean_text(description, max_len=220)
    if cleaned and len(cleaned) > 50:
        if not cleaned.endswith(('…', '.', '!', '?')):
            cleaned += '.'
        return cleaned
    templates = SYNTHESIS_TEMPLATES.get(content_type, SYNTHESIS_TEMPLATES["serie"])
    return random.choice(templates)


def monetize(url: str) -> str:
    if MONETIZATION_DOMAIN:
        clean = url.replace("https://", "").replace("http://", "")
        return f"https://{MONETIZATION_DOMAIN}/?redirect={clean}"
    return url


def build_premium_post(item: dict) -> str:
    """
    Genera el post premium con SIEMPRE dos enlaces.

    Para entretenimiento: alterna formato A (descriptivo) y B (hook viral).
    Para tech/ambiente/docs: siempre formato A (síntesis inteligente, sin viral).

    Formato A:
        {emoji} {Tipo} {emoji}
        {síntesis}
        👀 Ver ahora 👇
        👉 {link_monetizado} (Nombre)
        ⚡ Si no carga, acceso directo:
        👉 {url_original}
        {hashtags}

    Formato B (solo entretenimiento):
        {hook_emoji} {Hook}
        {action}
        👀 Ver ahora 👇
        👉 {link_monetizado} (Nombre)
        ⚡ Si no carga, acceso directo:
        👉 {url_original}
        {hashtags}
    """
    from hashtags import generate_hashtags

    ct           = item.get("content_type", "serie")
    title        = item.get("title", "")
    description  = item.get("description", "")
    url          = item.get("url", "")
    url_is_final = item.get("url_is_final", False)

    emoji, label = TYPE_HEADERS.get(ct, ("🎬", ct.upper()))
    synthesis    = generate_synthesis(title, description, ct)
    hashtags     = generate_hashtags(ct, item.get("genres", []), item.get("origins", []), title)

    # ── Construcción de los dos enlaces ──────────────────────────────────────
    if url_is_final:
        # El usuario ya monetizó el link manualmente
        main_link    = url
        fallback_url = url
        brand_suffix = ""
    else:
        monetized    = monetize(url)
        main_link    = monetized
        fallback_url = url
        brand_suffix = f" ({MONETIZATION_NAME})" if MONETIZATION_NAME else ""

    link_line = f"👉 {main_link}{brand_suffix}"
    fallback  = f"\n⚡ Si no carga, acceso directo:\n👉 {fallback_url}\n"

    # ── Hooks para TODAS las categorías (50% de probabilidad) ────────────────
    use_hook = random.random() < 0.5

    if use_hook:
        hook_emoji, hook_text = random.choice(HOOKS.get(ct, HOOKS["serie"]))
        action_text = random.choice(ACTIONS.get(ct, ACTIONS["novela"]))
        body = (
            f"{hook_emoji} {hook_text}\n\n"
            f"{action_text}\n\n"
        )
    else:
        body = (
            f"{emoji} {label} {emoji}\n\n"
            f"{synthesis}\n\n"
        )

    post = (
        f"{body}"
        f"👀 Ver ahora 👇\n"
        f"{link_line}\n"
        f"{fallback}\n"
        f"{hashtags}"
    )
    return post.strip()


def build_news_post(texto: str, url: str, content_type: str = "tecnologia") -> str:
    """Post para noticias enrutadas — siempre formato descriptivo."""
    from hashtags import generate_hashtags

    emoji, label = TYPE_HEADERS.get(content_type, ("📰", "Noticia"))
    synthesis    = clean_text(texto, max_len=220) or texto[:220]
    if not synthesis.endswith(('.', '!', '?', '…')):
        synthesis += '.'

    monetized    = monetize(url)
    brand_suffix = f" ({MONETIZATION_NAME})" if MONETIZATION_NAME else ""
    link_line    = f"👉 {monetized}{brand_suffix}"
    fallback     = f"\n⚡ Si no carga, acceso directo:\n👉 {url}\n" if monetized != url else ""
    hashtags     = generate_hashtags(content_type, [], [], "")

    return (
        f"{emoji} {label} {emoji}\n\n"
        f"{synthesis}\n\n"
        f"👀 Leer ahora 👇\n"
        f"{link_line}\n"
        f"{fallback}\n"
        f"{hashtags}"
    ).strip()
