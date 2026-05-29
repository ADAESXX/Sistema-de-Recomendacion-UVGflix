#Nombre del aechivo: loafMovieLens
#Autores:
    #Abigail Escobar
    #Alejandro Rustrian
    #Antony Portillo
#Fecha: 27/05/2026

import re
import random
import sys

import pandas as pd

from database import session, crearConstraints, closeDriver, comprobarConexion

# Datos ficticios

nombres = [
    "Sofía", "Diego", "Marcela", "Carlos", "Valeria", "Luis", "Ana", "Pedro",
    "Camila", "Andrés", "Lucía", "Javier", "Isabella", "Daniel", "María",
    "Jorge", "Paola", "Roberto", "Fernanda", "Sebastián", "Gabriela", "Miguel",
    "Renata", "Esteban", "Mónica", "Felipe", "Daniela", "Hugo", "Andrea",
    "Ricardo", "Ximena", "Carolina", "Alejandro", "Verónica", "Manuel",
    "Patricia", "Eduardo", "Adriana", "Tomás", "Beatriz", "Iván", "Natalia",
    "Rodrigo", "Cecilia", "Mauricio", "Lorena", "Óscar", "Silvia", "Raúl",
]

ubicaciones = [
    "Guatemala", "Ciudad de México", "Madrid", "Buenos Aires",
    "Bogotá", "Santiago", "Lima", "San José", "Quito", "La Paz",
]

plataformas = ["Netflix", "Disney+", "Prime Video", "HBO Max", "Apple TV+", "Paramount+"]

estadosAnimo = ["alegre", "relajado", "emocionado", "triste", "nostálgico", "curioso"]

# Mapeo género MovieLens(estados de ánimo compatibles)
generoAnimo = {
    "Comedy":      ["alegre", "relajado"],
    "Romance":     ["alegre", "nostálgico"],
    "Action":      ["emocionado"],
    "Adventure":   ["emocionado", "curioso"],
    "Thriller":    ["emocionado"],
    "Horror":      ["emocionado"],
    "Drama":       ["triste", "nostálgico"],
    "Mystery":     ["curioso"],
    "Sci-Fi":      ["curioso", "emocionado"],
    "Fantasy":     ["curioso", "alegre"],
    "Documentary": ["curioso"],
    "Animation":   ["alegre"],
    "Children":    ["alegre", "relajado"],
    "Crime":       ["emocionado"],
    "War":         ["triste"],
    "Western":     ["emocionado"],
    "Film-Noir":   ["nostálgico"],
    "Musical":     ["alegre"],
    "IMAX":        ["emocionado"],
}

# Duraciones plausibles por género (MovieLens no las incluye)
duracionGenero = {
    "Animation":   (75, 100),
    "Children":    (75, 100),
    "Comedy":      (85, 110),
    "Documentary": (60, 110),
    "Action":      (100, 140),
    "Adventure":   (100, 140),
    "Drama":       (95, 135),
    "Thriller":    (90, 125),
    "Horror":      (85, 105),
    "Romance":     (95, 120),
    "Sci-Fi":      (100, 145),
    "Fantasy":     (100, 150),
    "Mystery":     (90, 120),
    "Crime":       (100, 130),
    "War":         (110, 160),
    "Western":     (100, 130),
    "Film-Noir":   (90, 120),
    "Musical":     (95, 130),
}

### Utilidades ###
def obtenerYear(title):
    m = re.search(r"\((\d{4})\)", title)
    return int(m.group(1)) if m else None

#Quita el year del final del titulo
def clean_title(title):
    return re.sub(r"\s*\(\d{4}\)\s*$", "", title).strip()


def duracionEstimada(generos_str):
    #Estima el tiempo segun el genero
    generos = generos_str.split("|")
    rangos = [duracionGenero[g] for g in generos if g in duracionGenero]
    if not rangos:
        return random.randint(90, 120)
    lo = min(r[0] for r in rangos)
    hi = max(r[1] for r in rangos)
    return random.randint(lo, hi)


### Cargar los datos de MovieLens (reales) ###
def cargarPeliculas(movies_df, batch_size=500):
    print(f"Cargando {len(movies_df)} películas...")

    peliculas = []
    for _, row in movies_df.iterrows():
        title = row["title"]
        generos = row["genres"].split("|") if row["genres"] != "(no genres listed)" else []
        peliculas.append({
            "movieId": int(row["movieId"]),
            "titulo": clean_title(title),
            "year": obtenerYear(title),
            "duracion": duracionEstimada(row["genres"]),
            "generos": generos,
        })

    with session() as s:
        for i in range(0, len(peliculas), batch_size):
            batch = peliculas[i:i + batch_size]
            s.run("""
                UNWIND $batch AS pelicula
                MERGE (c:Contenido {movieId: pelicula.movieId})
                SET c.titulo = pelicula.titulo,
                    c.year = pelicula.year,
                    c.duracion = pelicula.duracion,
                    c.tipo = 'película'
                WITH c, pelicula
                UNWIND pelicula.generos AS gnombre
                MERGE (g:Genero {nombre: gnombre})
                MERGE (c)-[:ES_DE_GENERO]->(g)
            """, batch=batch)
            print(f"  {min(i + batch_size, len(peliculas))}/{len(peliculas)}")

    print("Películas cargadas.")


def cargarRatings(ratings_df, batch_size=2000):
    #Obtiene lo rating como relaciones VIO con propiedad calificacion
    print(f"Cargando {len(ratings_df)} calificaciones...")

    with session() as s:
        for i in range(0, len(ratings_df), batch_size):
            chunk = ratings_df.iloc[i:i + batch_size]
            batch = [{
                "userId": int(r["userId"]),
                "movieId": int(r["movieId"]),
                "calificacion": float(r["rating"]),
                "timestamp": int(r["timestamp"]) if "timestamp" in r else None,
            } for r in chunk.to_dict("records")]

            s.run("""
                UNWIND $batch AS row
                MERGE (u:Usuario {userId: row.userId})
                WITH u, row
                MATCH (c:Contenido {movieId: row.movieId})
                MERGE (u)-[r:VIO]->(c)
                SET r.calificacion = row.calificacion,
                    r.timestamp = row.timestamp
            """, batch=batch)
            print(f"  {min(i + batch_size, len(ratings_df))}/{len(ratings_df)}")

    print("Calificaciones cargadas.")



# Datos ficticios

def asignarPerfil():
    #Asigna nombre, edad y ubicaciuon a los usuarios ficticios
    print("Asignando perfiles a usuarios...")
    with session() as s:
        result = s.run("MATCH (u:Usuario) WHERE u.nombre IS NULL RETURN u.userId AS userId")
        user_ids = [r["userId"] for r in result]

        perfiles = [{
            "userId": uid,
            "nombre": f"{random.choice(nombres)}_{uid}",
            "edad": random.randint(16, 65),
            "ubicacion": random.choice(ubicaciones),
        } for uid in user_ids]

        BATCH = 500
        for i in range(0, len(perfiles), BATCH):
            batch = perfiles[i:i + BATCH]
            s.run("""
                UNWIND $batch AS p
                MATCH (u:Usuario {userId: p.userId})
                SET u.nombre = p.nombre,
                    u.edad = p.edad,
                    u.ubicacion = p.ubicacion
            """, batch=batch)
    print(f"  {len(perfiles)} usuarios actualizados.")


def crearPlataformas():
    #Crea las plataformas y asigna cada contenido y cada usuario a 1-3 plataformas
    with session() as s:
        for nombre in plataformas:
            s.run("MERGE (:Plataforma {nombre: $nombre})", nombre=nombre)

        # Contenidos -> plataformas
        print("  asignando contenidos a plataformas...")
        result = s.run("MATCH (c:Contenido) RETURN c.movieId AS id")
        movie_ids = [r["id"] for r in result]

        asignaciones = []
        for mid in movie_ids:
            n = random.randint(1, 2)
            for plat in random.sample(plataformas, n):
                asignaciones.append({"movieId": mid, "plat": plat})

        BATCH = 2000
        for i in range(0, len(asignaciones), BATCH):
            batch = asignaciones[i:i + BATCH]
            s.run("""
                UNWIND $batch AS row
                MATCH (c:Contenido {movieId: row.movieId})
                MATCH (p:Plataforma {nombre: row.plat})
                MERGE (c)-[:DISPONIBLE_EN]->(p)
            """, batch=batch)

        # Usuarios -> plataformas
        print("  asignando usuarios a plataformas...")
        result = s.run("MATCH (u:Usuario) RETURN u.userId AS id")
        user_ids = [r["id"] for r in result]

        asignaciones = []
        for uid in user_ids:
            n = random.randint(1, 3)
            for plat in random.sample(plataformas, n):
                asignaciones.append({"userId": uid, "plat": plat})

        for i in range(0, len(asignaciones), BATCH):
            batch = asignaciones[i:i + BATCH]
            s.run("""
                UNWIND $batch AS row
                MATCH (u:Usuario {userId: row.userId})
                MATCH (p:Plataforma {nombre: row.plat})
                MERGE (u)-[:USA]->(p)
            """, batch=batch)

    print("Plataformas listas.")


def crearEstadosAnimo():
    """Crea los estados de ánimo y los conecta con géneros compatibles."""
    print("Creando estados de ánimo y compatibilidades...")
    with session() as s:
        for nombre in estadosAnimo:
            s.run("MERGE (:EstadoAnimo {nombre: $nombre})", nombre=nombre)

        for genero, animos in generoAnimo.items():
            for animo in animos:
                s.run("""
                    MATCH (g:Genero {nombre: $genero})
                    MATCH (e:EstadoAnimo {nombre: $animo})
                    MERGE (g)-[:COMPATIBLE_CON]->(e)
                """, genero=genero, animo=animo)
    print("Estados de ánimo listos.")


def crearAmistades(densidad=0.015):
    """Crea relaciones AMIGO_DE entre usuarios (red social pequeña)."""
    print(f"Creando red de amistades (densidad ~{densidad})...")
    with session() as s:
        s.run("""
            MATCH (u1:Usuario), (u2:Usuario)
            WHERE u1.userId < u2.userId AND rand() < $densidad
            MERGE (u1)-[:AMIGO_DE]->(u2)
            MERGE (u2)-[:AMIGO_DE]->(u1)
        """, densidad=densidad)
        total = s.run("MATCH ()-[r:AMIGO_DE]->() RETURN count(r) AS t").single()["t"]
    print(f"  {total // 2} amistades creadas.")


### Función clave ###

def cargarTodo(movies_path="movies.csv", ratings_path="ratings.csv", limit_ratings=None):
    print("=" * 60)
    print("UVGflix - Carga de datos")
    print("=" * 60)

    if not comprobarConexion():
        print("No se pudo conectar a Neo4j. Revise config.py.")
        return

    print(f"Leyendo {movies_path} y {ratings_path}...")
    movies = pd.read_csv(movies_path)
    ratings = pd.read_csv(ratings_path)
    if limit_ratings:
        ratings = ratings.head(limit_ratings)
        print(f"  ratings limitados a {limit_ratings}")

    cargarPeliculas(movies)
    cargarRatings(ratings)
    asignarPerfil()
    crearPlataformas()
    crearEstadosAnimo()
    crearAmistades()

    print("=" * 60)
    print("Carga completa.")
    print("=" * 60)


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    try:
        cargarTodo(limit_ratings=limit)
    finally:
        closeDriver()
