#Nombre del archivo: database.py
#Autores:
    #Abigail Escobar
    #Alejandro Rustrian
    #Antony Portillo
#Fecha: 27/05/2026

#Descripcion: Permite la conexión y acceso a Neo4j

from contextlib import contextmanager
from neo4j import GraphDatabase

from config import url, user, password, databaseNeo4j
#"puente" entre Python y la base de datos
_driver = None


def getDriver():
    global _driver
    #crear el driver si no existe
    if _driver is None:
        _driver = GraphDatabase.driver(url, auth=(user, password))
    return _driver


def closeDriver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


@contextmanager
def session():
    driver = getDriver()
    #Sesión en Neo4j donde se ejecutaran los queries
    with driver.session(database=databaseNeo4j) as s:
        yield s


def crearConstraints():
    statements = [
        "CREATE CONSTRAINT usuario_id IF NOT EXISTS FOR (u:Usuario) REQUIRE u.userId IS UNIQUE",
        "CREATE CONSTRAINT contenido_id IF NOT EXISTS FOR (c:Contenido) REQUIRE c.movieId IS UNIQUE",
        "CREATE CONSTRAINT genero_nombre IF NOT EXISTS FOR (g:Genero) REQUIRE g.nombre IS UNIQUE",
        "CREATE CONSTRAINT plataforma_nombre IF NOT EXISTS FOR (p:Plataforma) REQUIRE p.nombre IS UNIQUE",
        "CREATE CONSTRAINT animo_nombre IF NOT EXISTS FOR (e:EstadoAnimo) REQUIRE e.nombre IS UNIQUE",
        "CREATE INDEX contenido_titulo IF NOT EXISTS FOR (c:Contenido) ON (c.titulo)",
        "CREATE INDEX usuario_nombre IF NOT EXISTS FOR (u:Usuario) ON (u.nombre)",
    ]
    with session() as s:
        for stmt in statements:
            s.run(stmt)


def comprobarConexion():
    #verifica que la base de datos este accesible
    try:
        with session() as s:
            s.run("RETURN 1").single()
        return True
    except Exception as e:
        print(f"Error conectando a Neo4j: {e}")
        return False