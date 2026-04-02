def generate_hashtags(content_type: str, genres: list, origins: list = None, title: str = "") -> str:
    if origins is None:
        origins = []

    tags = set()

    base_tags = {
        "novela": ["#Novela", "#Novelas", "#NovelaCompleta", "#Telenovela", "#NovelaOnline"],
        "serie": ["#Serie", "#Series", "#SerieCompleta", "#Episodio", "#SeriesOnline"],
        "pelicula": ["#Pelicula", "#Peliculas", "#PeliculaCompleta", "#Cine", "#PeliculaOnline"],
        "documental_ambiente": ["#Documental", "#MedioAmbiente", "#Naturaleza", "#Fauna", "#Planeta"],
        "documental_ciencia": ["#Documental", "#Ciencia", "#Descubrimiento", "#Universo", "#Educacion"],
        "documental_historia": ["#Documental", "#Historia", "#Historico", "#Civilizacion", "#Cultura"],
        "tecnologia": ["#Tecnologia", "#Tech", "#Gadgets", "#Celulares", "#Innovacion", "#Android", "#iPhone"],
    }
    tags.update(base_tags.get(content_type, ["#Video", "#Entretenimiento"]))

    genre_tags = {
        "accion": ["#Accion", "#Aventura"],
        "romance": ["#Romance", "#Amor"],
        "drama": ["#Drama"],
        "comedia": ["#Comedia", "#Humor"],
        "suspenso": ["#Suspenso", "#Thriller", "#Misterio"],
        "terror": ["#Terror", "#Horror"],
        "familiar": ["#Familiar", "#Entretenimiento"],
        "historico": ["#Historico", "#Epoca"],
        "ciencia_ficcion": ["#CienciaFiccion", "#SciFi"],
    }
    for genre in genres:
        tags.update(genre_tags.get(genre, []))

    origin_tags = {
        "turca": ["#NovelasTurcas", "#TurcaCompleta"],
        "coreana": ["#KDrama", "#SeriesCoreanas"],
        "brasileña": ["#NovelasBrasileñas", "#Brasil"],
        "colombiana": ["#NovelasColombianas", "#Colombia"],
        "mexicana": ["#NovelasMexicanas", "#Mexico"],
        "india": ["#SeriesIndias", "#Bollywood"],
    }
    for origin in origins:
        tags.update(origin_tags.get(origin, []))

    tags.update(["#Viral", "#Tendencia"])
    tags.update(["#Online", "#Gratis"])

    return " ".join(sorted(tags)[:20])
