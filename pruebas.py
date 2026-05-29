
#Nombre del archivo: config.py
#Autores:
    #Abigail Escobar
    #Alejandro Rustrian
    #Antony Portillo
#Fecha: 27/05/2026
#Descripcion: escenario de pruebas con el testing de usuarios

import sys

from database import closeDriver
from recomendador import recomendar, recomendarAmigos, perfilUsuario
from operacionesGrafo import listarUsuarios, historialUsuario


def imprimir_recs(recs, titulo):
    print(f"\n  >> {titulo}")

    if not recs:
        print("     (sin resultados)")
        return

    for i, r in enumerate(recs, 1):
        razon = r["razones"][0] if r["razones"] else ""
        print(f"     {i}. {r['titulo']}  —  {razon}")


def escenario_completo(userId):

    perfil = perfilUsuario(userId)

    if not perfil:
        print(f"\nUsuario {userId} no existe.")
        return

    print("\n" + "=" * 70)
    print(f"USUARIO {userId} — {perfil['nombre']}")
    print("=" * 70)

    print(f"  Edad: {perfil['edad']}   Ubicación: {perfil['ubicacion']}")
    print(f"  Plataformas: {', '.join(perfil['plataformas']) or '—'}")
    print(f"  Géneros favoritos: {', '.join(perfil['generosFavoritos']) or '—'}")
    print(f"  Contenidos calificados: {perfil['contenidosVistos']}")

    print("\n  Top 5 mejor calificados por este usuario:")

    for h in historialUsuario(userId, limite=5):
        print(f"     ★ {h['calificacion']:.1f}  {h['titulo']}")

    # Escenario 1
    imprimir_recs(
        recomendar(userId, n=5),
        "Escenario 1: recomendaciones generales"
    )

    # Escenario 2
    imprimir_recs(
        recomendar(userId, n=5, tiempoDisponible=100),
        "Escenario 2: menos de 100 minutos"
    )

    # Escenario 3
    imprimir_recs(
        recomendar(userId, n=5, estadoAnimo="relajado"),
        "Escenario 3: estado relajado"
    )

    # Escenario 4
    imprimir_recs(
        recomendar(
            userId,
            n=5,
            estadoAnimo="emocionado",
            tiempoDisponible=140
        ),
        "Escenario 4: emocionante hasta 140 min"
    )

    # Escenario 5
    imprimir_recs(
        recomendar(
            userId,
            n=5,
            incluirContenido=False
        ),
        "Escenario 5: solo colaborativo"
    )

    # Escenario 6
    imprimir_recs(
        recomendar(
            userId,
            n=5,
            incluirColaborativo=False
        ),
        "Escenario 6: solo contenido"
    )

    # Escenario 7
    imprimir_recs(
        recomendarAmigos(userId, n=5),
        "Escenario 7: recomendaciones sociales"
    )


def main():

    if len(sys.argv) > 1:
        ids = [int(x) for x in sys.argv[1:]]

    else:
        ids = [u["userId"] for u in listarUsuarios(limite=3)]

        print(
            f"Sin IDs especificados; usando los 3 usuarios más activos: {ids}"
        )

    try:
        for uid in ids:
            escenario_completo(uid)

    finally:
        closeDriver()


if __name__ == "__main__":
    main()