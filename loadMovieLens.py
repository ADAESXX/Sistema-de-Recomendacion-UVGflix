#Nombre del aechivo: loafMovieLens
#Autores:
    #Abigail Escobar
    #Alejandro Rustrian
    #Antony Portillo
#Fecha: 25/05/2026

from neo4j import GraphDatabase
import pandas as pd

#configuracion de Neo4j
print("Iniciando...")
url = "bolt://127.0.0.1:7687"
user = "neo4j"
password = "uvgflixproyecto"

driver = GraphDatabase.driver(url, auth=(user, password))
print("Conectado a Neo4j")

# leer csvs
movies = pd.read_csv("movies.csv")
ratings = pd.read_csv("ratings.csv")

# funiciones importantes
def create_movie(tx, movie_id, title, genres):
    tx.run("""
        MERGE (m:Contenido {movieId: $movie_id})
        SET m.titulo = $title
    """, movie_id=movie_id, title=title)

    genre_list = genres.split("|")

    for genre in genre_list:
        tx.run("""
            MERGE (g:Genero {nombre: $genre})

            WITH g

            MATCH (m:Contenido {movieId: $movie_id})

            MERGE (m)-[:ES_DE_GENERO]->(g)
        """, genre=genre, movie_id=movie_id)

def create_user_rating(tx, user_id, movie_id, rating):
    tx.run("""
        MERGE (u:Usuario {userId: $user_id})

        WITH u

        MATCH (m:Contenido {movieId: $movie_id})

        MERGE (u)-[r:VIO]->(m)

        SET r.calificacion = $rating
    """, user_id=user_id, movie_id=movie_id, rating=rating)

# cargar peliculas
with driver.session() as session:
    for _, row in movies.iterrows():

        create_movie(
            session,
            int(row["movieId"]),
            row["title"],
            row["genres"]
        )

print("Peliculas cargadas")


# cargar ratings
with driver.session() as session:

    for _, row in ratings.iterrows():

        create_user_rating(
            session,
            int(row["userId"]),
            int(row["movieId"]),
            float(row["rating"])
        )

print("Ratings cargados")

driver.close()

print("Base de datos lista")