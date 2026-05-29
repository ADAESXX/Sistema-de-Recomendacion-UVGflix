
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

    # historial corto
    print("\n  Top 5 mejor calificados por este usuario:")
    for h in historialUsuario(userId, limite=5):
        print(f"     ★ {h['calificacion']:.1f}  {h['titulo']}")

    # escenarios
    imprimir_recs(
        recomendar(userId, n=5),
        "Escenario 1: recomendaciones generales (sin filtros)",
    )
    imprimir_recs(
        recomendar(userId, n=5, tiempo_disponible=100),
        "Escenario 2: tengo menos de 100 min disponibles",
    )
    imprimir_recs(
        recomendar(userId, n=5, estado_animo="relajado"),
        "Escenario 3: estoy relajado, algo tranquilo",
    )
    imprimir_recs(
        recomendar(userId, n=5, estado_animo="emocionado", tiempo_disponible=140),
        "Escenario 4: quiero algo emocionante (hasta 140 min)",
    )
    imprimir_recs(
        recomendar(userId, n=5, incluir_contenido=False),
        "Escenario 5: solo filtrado colaborativo (cómo se ve sin contenido)",
    )
    imprimir_recs(
        recomendar(userId, n=5, incluir_colaborativo=False),
        "Escenario 6: solo filtrado basado en contenido",
    )
    imprimir_recs(
        recomendarAmigos(userId, n=5),
        "Escenario 7: recomendaciones sociales (de los amigos)",
    )


def main():
    if len(sys.argv) > 1:
        ids = [int(x) for x in sys.argv[1:]]
    else:
        # usuarios más activos por defecto
        ids = [u["userId"] for u in listarUsuarios(limite=3)]
        print(f"Sin IDs especificados; usando los 3 usuarios más activos: {ids}")

    try:
        for uid in ids:
            escenario_completo(uid)
    finally:
        closeDriver()


if __name__ == "__main__":
    main()
