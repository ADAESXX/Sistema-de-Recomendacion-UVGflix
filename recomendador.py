#Nombre del archivo: recomendador.py
#Autores:
    #Abigail Escobar
    #Alejandro Rustrian
    #Antony Portillo
#Fecha: 27/05/2026

#Descripción: es el motor de recomendación que implementa tanto el filtrado colaborativo, como el filtrado por contenido.
    #Busca usuarios similares
    #Obtiene películas que les gustaron
    #Busca contenido parecido a lo visto por el usuario
    #Aplica filtros contextuales
    #Calcula puntajes
    #Ordena resultados
    #Devuelve las top recomendaciones
    
from database import session

###Parametros importables para el algoritmo (se pueden modificar)###
#Similitud mínima para considerar a otro como similar
umbralSimilitud= 0.30
#Cuántos usuarios similares analizar
topKUsuarios= 15
#Mínimo de contenido en cómun para calcular similitud
minComunes= 2
calificacionMin =4.0
#Tiene más peso que el filtrado por contenido (pesoContenido)
pesoColaborativo= 1.0
PesoContenido= 0.4
limiteCandidatos= 100

### Filtrado colaborativo ###

def encontrarUsuariosSimilares(userId, top_k=topKUsuarios):
    #Compara las calificaciones del usuario con la de otros usuarios
    #Con MATCH busca el contenido visto por ambos y luego calcula el producto punto (escalar que denota la similitud entre ambos)
    query = """
        MATCH (u:Usuario {userId: $userId})-[r1:VIO]->(c:Contenido)<-[r2:VIO]-(otro:Usuario)
        WHERE u <> otro
        WITH otro,
             count(c)                                      AS comunes,
             sum(r1.calificacion * r2.calificacion)        AS dot,
             sum(r1.calificacion * r1.calificacion)        AS sumA,
             sum(r2.calificacion * r2.calificacion)        AS sumB
        WHERE comunes >= $minComunes AND sumA > 0 AND sumB > 0
        WITH otro, dot / (sqrt(sumA) * sqrt(sumB)) AS similitud
        WHERE similitud > $umbral
        RETURN otro.userId AS userId, otro.nombre AS nombre, similitud
        ORDER BY similitud DESC
        LIMIT $topK
    """
    with session() as s:
        result = s.run(query,
                       userId=userId,
                       minComunes=minComunes,
                       umbral=umbralSimilitud,
                       topK=top_k)
        return [dict(r) for r in result]


def candidatosColaborativo(userId, similares):
    if not similares:
        return {}
    # si hay usuarios con gustos similares con peliculas que no ha visto el usuario
    ids_similares = [s["userId"] for s in similares]
    sim_map = {s["userId"]: s["similitud"] for s in similares}

    query = """
        MATCH (otro:Usuario)-[r:VIO]->(c:Contenido)
        WHERE otro.userId IN $ids
          AND r.calificacion >= $minCal
          AND NOT EXISTS {
              MATCH (u:Usuario {userId: $userId})-[:VIO]->(c)
          }
        RETURN c.movieId   AS movieId,
               c.titulo    AS titulo,
               otro.userId AS otroId,
               r.calificacion AS cal
    """
    candidatos = {}
    #ingresa el query a la sesion de Neo4j
    with session() as s:
        for r in s.run(query, ids=ids_similares, userId=userId, minCal=calificacionMin):
            mid = r["movieId"]
            sim = sim_map.get(r["otroId"], 0)
            puntaje = sim * r["cal"] * pesoColaborativo

            if mid not in candidatos:
                candidatos[mid] = {
                    "movieId": mid,
                    "titulo": r["titulo"],
                    "puntaje": 0.0,
                    "razones": set(),
                }
            candidatos[mid]["puntaje"] += puntaje
            candidatos[mid]["razones"].add("A usuarios con gustos similares les gustó")
    return candidatos


### Filtrado basado en contenido ###

def candidatosContenido(userId, candidatos):
    #Busca contenido parecido a lo que el usuario ya vio, conectando por genero, actores y directores
    #Luego con count (DISTINCT attr) cuenta cuantos atributos comparten paara crear más conexiones de similares
    query = """
        MATCH (u:Usuario {userId: $userId})-[r:VIO]->(visto:Contenido)
        WHERE r.calificacion >= 4
        MATCH (visto)-[:ES_DE_GENERO|ACTUADA_POR|DIRIGIDA_POR]->(attr)
              <-[:ES_DE_GENERO|ACTUADA_POR|DIRIGIDA_POR]-(similar:Contenido)
        WHERE similar <> visto
          AND NOT EXISTS {
              MATCH (u)-[:VIO]->(similar)
          }
        WITH similar,
             collect(DISTINCT visto.titulo)[0..3] AS bases,
             count(DISTINCT attr)                 AS conexiones
        RETURN similar.movieId AS movieId,
               similar.titulo  AS titulo,
               bases,
               conexiones
        ORDER BY conexiones DESC
        LIMIT $limite
    """
    with session() as s:
        for r in s.run(query, userId=userId, limite=limiteCandidatos):
            mid = r["movieId"]
            puntaje = r["conexiones"] * PesoContenido
            base_ej = r["bases"][0] if r["bases"] else "algo que viste"

            if mid not in candidatos:
                candidatos[mid] = {
                    "movieId": mid,
                    "titulo": r["titulo"],
                    "puntaje": 0.0,
                    "razones": set(),
                }
            candidatos[mid]["puntaje"] += puntaje
            candidatos[mid]["razones"].add(f"Similar a '{base_ej}'")
    return candidatos

### Filtrados contextuales ###

def filtrarContexto(userId, candidatos, tiempoDisponible=None, estadoAnimo=None):
   # Filtra por duración, estado de ánimo y plataformas del usuario
   #Si el usuario no tiene plataformas no se filtra en esa categoría
    if not candidatos:
        return candidatos

    ids = list(candidatos.keys())

    query = """
        MATCH (u:Usuario {userId: $userId})
        OPTIONAL MATCH (u)-[:USA]->(userP:Plataforma)
        WITH u, collect(DISTINCT userP.nombre) AS userPlats
        MATCH (c:Contenido) WHERE c.movieId IN $ids

        // Filtro de tiempo
        WHERE ($tiempo IS NULL OR c.duracion IS NULL OR c.duracion <= $tiempo)

        // Filtro de plataforma
        WITH c, userPlats
        OPTIONAL MATCH (c)-[:DISPONIBLE_EN]->(contP:Plataforma)
        WITH c, userPlats, collect(DISTINCT contP.nombre) AS contPlats
        WHERE size(userPlats) = 0
           OR any(p IN contPlats WHERE p IN userPlats)

        // Filtro de estado de ánimo
        WITH c, $animo AS animo
        WHERE animo IS NULL OR EXISTS {
            MATCH (c)-[:ES_DE_GENERO]->(:Genero)-[:COMPATIBLE_CON]->(:EstadoAnimo {nombre: animo})
        }

        RETURN c.movieId AS movieId
    """
    with session() as s:
        result = s.run(query,
                       userId=userId,
                       ids=ids,
                       tiempo=tiempoDisponible,
                       animo=estadoAnimo)
        ids_validos = {r["movieId"] for r in result}

    return {mid: c for mid, c in candidatos.items() if mid in ids_validos}

### Función central ###

def recomendar(userId, n=5, tiempoDisponible=None, estadoAnimo=None, incluirContenido=True, incluirColaborativo=True):
    candidatos = {}
    
    if incluirColaborativo:
        similares = encontrarUsuariosSimilares(userId)
        candidatos = candidatosColaborativo(userId, similares)

    if incluirContenido:
        candidatos = candidatosContenido(userId, candidatos)

    candidatos = filtrarContexto(userId, candidatos, tiempoDisponible, estadoAnimo)
    ordenados = sorted(candidatos.values(), key=lambda c: c["puntaje"], reverse=True)

    for c in ordenados:
        c["razones"] = list(c["razones"])

    return ordenados[:n]

### Función adicional - social ###

def recomendarAmigos(userId, n=5):
    query = """
        MATCH (u:Usuario {userId: $userId})-[:AMIGO_DE]->(amigo)-[r:VIO]->(c:Contenido)
        WHERE r.calificacion >= 4
          AND NOT EXISTS {
              MATCH (u)-[:VIO]->(c)
          }
        WITH c,
             count(DISTINCT amigo) AS cuantosAmigos,
             avg(r.calificacion)   AS calProm
        RETURN c.movieId AS movieId,
               c.titulo  AS titulo,
               cuantosAmigos,
               calProm
        ORDER BY cuantosAmigos DESC, calProm DESC
        LIMIT $n
    """
    with session() as s:
        return [{
            "movieId": r["movieId"],
            "titulo":  r["titulo"],
            "puntaje": r["cuantosAmigos"] * r["calProm"],
            "razones": [f"A {r['cuantosAmigos']} de tus amigos les gustó (cal. promedio {r['calProm']:.1f})"],
        } for r in s.run(query, userId=userId, n=n)]


### perfil del usuario ###

def perfilUsuario(userId):
    query = """
        MATCH (u:Usuario {userId: $userId})
        OPTIONAL MATCH (u)-[:USA]->(p:Plataforma)
        WITH u, collect(DISTINCT p.nombre) AS plataformas
        OPTIONAL MATCH (u)-[r:VIO]->(c:Contenido)-[:ES_DE_GENERO]->(g:Genero)
        WHERE r.calificacion >= 4
        WITH u, plataformas, g, count(g) AS frec
        ORDER BY frec DESC
        WITH u, plataformas, collect(g.nombre)[0..5] AS generosFavoritos
        OPTIONAL MATCH (u)-[r2:VIO]->()
        RETURN u.nombre    AS nombre,
               u.edad      AS edad,
               u.ubicacion AS ubicacion,
               plataformas,
               generosFavoritos,
               count(r2)   AS contenidosVistos
    """
    with session() as s:
        record = s.run(query, userId=userId).single()
        return dict(record) if record else None
