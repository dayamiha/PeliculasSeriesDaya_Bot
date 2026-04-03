"""
Genera hashtags inteligentes según tipo, género, origen y título.
Formato: minúsculas, agrupados por relevancia.
"""


def generate_hashtags(content_type: str, genres: list, origins: list = None, title: str = "") -> str:
    if origins is None:
        origins = []

    tags = []

    base_tags = {
        "novela": [
            "#novela", "#novelas", "#telenovela", "#novelacompleta",
            "#capitulodehoy", "#novelalatina",
        ],
        "serie": [
            "#serie", "#series", "#seriescompletas", "#episodiodehoy",
            "#seriesonline", "#streaminggratis",
        ],
        "anime": [
            "#anime", "#animeespanol", "#animefan", "#manga",
            "#animeonline", "#animedublado",
        ],
        "pelicula": [
            "#pelicula", "#peliculas", "#peliculacompleta", "#cine",
            "#peliculaonline", "#estreno",
        ],
        "documental_ambiente": [
            "#documental", "#medioambiente", "#naturaleza", "#fauna",
            "#planeta", "#ecologia",
        ],
        "documental_ciencia": [
            "#documental", "#ciencia", "#descubrimiento", "#universo",
            "#educacion", "#curiosidades",
        ],
        "documental_historia": [
            "#documental", "#historia", "#historico", "#civilizacion",
            "#cultura", "#antiguedad",
        ],
        "tecnologia": [
            "#tecnologia", "#tech", "#gadgets", "#innovacion",
            "#android", "#iphone", "#review",
        ],
    }
    tags.extend(base_tags.get(content_type, ["#video", "#entretenimiento"]))

    genre_map = {
        "accion":          ["#accion", "#aventura"],
        "romance":         ["#romance", "#amor"],
        "drama":           ["#drama"],
        "comedia":         ["#comedia", "#humor"],
        "suspenso":        ["#suspenso", "#thriller", "#misterio"],
        "terror":          ["#terror", "#horror"],
        "familiar":        ["#familiar", "#paratodalafamilia"],
        "historico":       ["#historico", "#epoca"],
        "ciencia_ficcion": ["#cienciaficcion", "#scifi"],
    }
    for genre in genres:
        tags.extend(genre_map.get(genre, []))

    origin_map = {
        "turca":     ["#novelasturcas", "#turcacompleta"],
        "coreana":   ["#kdrama", "#seriescoreanas"],
        "brasileña": ["#novelasbrasilenas", "#brasil"],
        "colombiana": ["#novelascolombianas", "#colombia"],
        "mexicana":  ["#novelasmexicanas", "#mexico"],
        "india":     ["#seriesindias", "#bollywood"],
        "japonesa":  ["#animejapones", "#japon"],
        "china":     ["#dramachino", "#chinadrama"],
    }
    for origin in origins:
        tags.extend(origin_map.get(origin, []))

    # Tags por anime específico
    if content_type == "anime":
        anime_map = {
            "naruto":       "#naruto",
            "dragon ball":  "#dragonball",
            "one piece":    "#onepiece",
            "bleach":       "#bleach",
            "boruto":       "#boruto",
            "attack on titan": "#attackontitan",
            "demon slayer": "#demonslayer",
            "jujutsu":      "#jujutsukaisen",
            "my hero":      "#myheroacademia",
            "sword art":    "#swordartonline",
            "fairy tail":   "#fairytail",
            "black clover": "#blackclover",
        }
        title_lower = title.lower()
        for key, tag in anime_map.items():
            if key in title_lower:
                tags.insert(0, tag)
                break

    # Tags globales finales
    tags.extend(["#gratis", "#online", "#viral"])

    # Deduplicar manteniendo orden
    seen = set()
    unique = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return " ".join(unique[:18])
