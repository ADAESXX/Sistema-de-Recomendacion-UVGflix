#Nombre del archivo: config.py
#Autores:
    #Abigail Escobar
    #Alejandro Rustrian
    #Antony Portillo
#Fecha: 28/05/2026
#Descripcion: operaciones sobre el grafo, como agregar y eliminar usuarios, contenidos, calificaciones,etc.

from database import session

### Usuarios ###
def agregarUsuario(userId, nombre, edad=None, ubicacion=None):
    #Crea o actualiza el usuario
    with session() as s:
        s.run("""
            MERGE (u:Usuario {userId: $userId})
            SET u.nombre    = $nombre,
                u.edad      = $edad,
                u.ubicacion = $ubicacion
        """, userId=userId, nombre=nombre, edad=edad, ubicacion=ubicacion)
    return True


def eliminarUsuario(userId):
    #Elimina al usuario y a todas sus relaciones
    with session() as s:
        r = s.run("""
            MATCH (u:Usuario {userId: $userId})
            WITH u, u.nombre AS nombre
            DETACH DELETE u
            RETURN nombre
        """, userId=userId).single()
        return r["nombre"] if r else None


def listarUsuarios(limite=20):
    #usuarios más activos
    with session() as s:
        return [dict(r) for r in s.run("""
            MATCH (u:Usuario)
            OPTIONAL MATCH (u)-[r:VIO]->(:Contenido)
            RETURN u.userId AS userId,
                   u.nombre AS nombre,
                   u.edad   AS edad,
                   count(r) AS contenidosVistos
            ORDER BY contenidosVistos DESC
            LIMIT $limite
        """, limite=limite)]


### Contenido ###
def agregarContenido(movieId, titulo, year=None, duracion=None, tipo="película", generos=None):
    #Crea o actualiza un contenido y lo asocia con sus géneros
    with session() as s:
        s.run("""
            MERGE (c:Contenido {movieId: $movieId})
            SET c.titulo   = $titulo,
                c.year     = $year,
                c.duracion = $duracion,
                c.tipo     = $tipo
        """, movieId=movieId, titulo=titulo, year=year, duracion=duracion, tipo=tipo)

        if generos:
            s.run("""
                MATCH (c:Contenido {movieId: $movieId})
                UNWIND $generos AS gnombre
                MERGE (g:Genero {nombre: gnombre})
                MERGE (c)-[:ES_DE_GENERO]->(g)
            """, movieId=movieId, generos=generos)
    return True


def eliminarContenido(movieId):
    #Elimina un contenido y sus relaciones
    with session() as s:
        r = s.run("""
            MATCH (c:Contenido {movieId: $movieId})
            WITH c, c.titulo AS titulo
            DETACH DELETE c
            RETURN titulo
        """, movieId=movieId).single()
        return r["titulo"] if r else None


def buscarContenido(texto, limite=10):
    #Busca contenidos por texto en el título 
    with session() as s:
        return [dict(r) for r in s.run("""
            MATCH (c:Contenido)
            WHERE toLower(c.titulo) CONTAINS toLower($texto)
            OPTIONAL MATCH (c)-[:ES_DE_GENERO]->(g:Genero)
            RETURN c.movieId  AS movieId,
                   c.titulo   AS titulo,
                   c.year     AS year,
                   c.duracion AS duracion,
                   collect(DISTINCT g.nombre) AS generos
            LIMIT $limite
        """, texto=texto, limite=limite)]



### CALIFICACIONES ###


def agregarCalificacion(userId, movieId, calificacion):
    #Crea o actualiza la relación VIO con su calificación
    if not (0 <= calificacion <= 5):
        raise ValueError("La calificación debe estar entre 0 y 5.")
    with session() as s:
        r = s.run("""
            MATCH (u:Usuario {userId: $userId})
            MATCH (c:Contenido {movieId: $movieId})
            MERGE (u)-[rel:VIO]->(c)
            SET rel.calificacion = $cal,
                rel.timestamp = timestamp()
            RETURN c.titulo AS titulo
        """, userId=userId, movieId=movieId, cal=float(calificacion)).single()
        return r["titulo"] if r else None


def eliminarCalificacion(userId, movieId):
    #Borra la relación VIO entre usuario y contenido.
    with session() as s:
        r = s.run("""
            MATCH (u:Usuario {userId: $userId})-[r:VIO]->(c:Contenido {movieId: $movieId})
            DELETE r
            RETURN count(r) AS n
        """, userId=userId, movieId=movieId).single()
        return r["n"] > 0


def historialUsuario(userId, limite=20):
    #Devuelve el historial de contenidos calificados por un usuario
    with session() as s:
        return [dict(r) for r in s.run("""
            MATCH (u:Usuario {userId: $userId})-[r:VIO]->(c:Contenido)
            RETURN c.movieId AS movieId,
                   c.titulo  AS titulo,
                   r.calificacion AS calificacion
            ORDER BY r.calificacion DESC
            LIMIT $limite
        """, userId=userId, limite=limite)]



### Amistades ###

def agregarAmistad(u1, u2):
    #Crea relación AMIGO_DE bidireccional
    if u1 == u2:
        raise ValueError("Un usuario no puede ser amigo de sí mismo.")
    with session() as s:
        s.run("""
            MATCH (a:Usuario {userId: $u1}), (b:Usuario {userId: $u2})
            MERGE (a)-[:AMIGO_DE]->(b)
            MERGE (b)-[:AMIGO_DE]->(a)
        """, u1=u1, u2=u2)
    return True


def eliminarAmistad(u1, u2):
    #Elimina la relación AMIGO_DE en ambas direcciones
    with session() as s:
        s.run("""
            MATCH (a:Usuario {userId: $u1})-[r:AMIGO_DE]-(b:Usuario {userId: $u2})
            DELETE r
        """, u1=u1, u2=u2)
    return True


### Plataformas ###
def vincularPlataforma(userId, plataforma):
    #Asocia un usuario a una plataforma
    with session() as s:
        s.run("""
            MATCH (u:Usuario {userId: $userId})
            MERGE (p:Plataforma {nombre: $plataforma})
            MERGE (u)-[:USA]->(p)
        """, userId=userId, plataforma=plataforma)
    return True


def desvincularPlataforma(userId, plataforma):
    #Quita la relación USA entre usuario y plataforma
    with session() as s:
        s.run("""
            MATCH (u:Usuario {userId: $userId})-[r:USA]->(p:Plataforma {nombre: $plataforma})
            DELETE r
        """, userId=userId, plataforma=plataforma)
    return True


### Estadisticas ###

def estadisticas():
   #Conteo  nodos y relaciones
    queries = {
        "usuarios":         "MATCH (u:Usuario) RETURN count(u) AS n",
        "contenidos":       "MATCH (c:Contenido) RETURN count(c) AS n",
        "géneros":          "MATCH (g:Genero) RETURN count(g) AS n",
        "plataformas":      "MATCH (p:Plataforma) RETURN count(p) AS n",
        "estados de ánimo": "MATCH (e:EstadoAnimo) RETURN count(e) AS n",
        "calificaciones":   "MATCH ()-[r:VIO]->() RETURN count(r) AS n",
        "amistades":        "MATCH ()-[r:AMIGO_DE]->() RETURN count(r)/2 AS n",
        "Usa":              "MATCH ()-[r:USA]->() RETURN count(r) AS n",
        "Disponible_en":    "MATCH ()-[r:DISPONIBLE_EN]->() RETURN count(r) AS n",
    }
    out = {}
    with session() as s:
        for nombre, q in queries.items():
            out[nombre] = s.run(q).single()["n"]
    return out
