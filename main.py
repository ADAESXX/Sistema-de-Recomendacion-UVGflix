#Nombre del archivo: config.py
#Autores:
    #Abigail Escobar
#Fecha: 27/05/2026
#Descripcion: programa que interactua co  el usuario

from database import*
import recomendador as rec
import operacionesGrafo as og

estadosAnimo= ["alegre", "relajado", "emocionado", "triste", "nostálgico", "curioso"]

# Funciones útiles para poder leer y escribir
def imprimirRecomendaciones(recs, titulo=""):
    if titulo:
        print(f"\n=== {titulo} ===")
    if not recs:
        print("  (sin resultados con estos filtros)")
        return
    for i, r in enumerate(recs, 1):
        print(f"\n  {i}. {r['titulo']}  (movieId: {r['movieId']})")
        print(f"     puntaje: {r['puntaje']:.2f}")
        for razon in r["razones"]:
            print(f"     • {razon}")


def leerInt(prompt, default=None):
    raw = input(prompt).strip()
    if not raw:
        return default
    return int(raw)


def leerFloat(prompt, default=None):
    raw = input(prompt).strip()
    if not raw:
        return default
    return float(raw)

#Acciones del menu
def accion_recomendar():
    print("\n--- Obtener recomendaciones ---")

    userId = leerInt("ID de usuario: ")

    if userId is None:
        return

    perfil = rec.perfilUsuario(userId)

    if not perfil:
        print(f"  Usuario {userId} no existe.")
        return

    print(f"\n  Usuario: {perfil['nombre']}")
    print(f"  Edad:    {perfil['edad']}    Ubicación: {perfil['ubicacion']}")
    print(f"  Plataformas: {', '.join(perfil['plataformas']) or '—'}")
    print(f"  Géneros favoritos: {', '.join(perfil['generosFavoritos']) or '—'}")
    print(f"  Contenidos calificados: {perfil['contenidosVistos']}")

    n = leerInt("\n  ¿Cuántas recomendaciones? [5]: ", default=5)

    tiempo = leerInt(
        "  Tiempo disponible en minutos [enter = sin filtro]: ",
        default=None
    )

    print(f"  Estados de ánimo: {', '.join(estadosAnimo)}")

    animo = input(
        "  Estado de ánimo [enter = sin filtro]: "
    ).strip().lower() or None

    if animo and animo not in estadosAnimo:
        print("  (estado de ánimo inválido, ignorado)")
        animo = None

    print("\n  Calculando recomendaciones...")

    recs = rec.recomendar(
        userId,
        n=n,
        tiempoDisponible=tiempo,
        estadoAnimo=animo
    )

    imprimirRecomendaciones(recs, "Recomendaciones híbridas")

    print()

    recs_amigos = rec.recomendarAmigos(userId, n=n)

    imprimirRecomendaciones(
        recs_amigos,
        "Recomendaciones sociales (de tus amigos)"
    )


def accion_listar_usuarios():
    print("\n--- Usuarios más activos ---")

    for u in og.listarUsuarios(limite=20):
        print(
            f"  [{u['userId']:>5}] "
            f"{u['nombre'] or '(sin nombre)':<25}  "
            f"edad: {u['edad'] or '?':<3}  "
            f"contenidos vistos: {u['contenidosVistos']}"
        )


def accion_agregar_usuario():
    print("\n--- Agregar usuario ---")

    userId = leerInt("  ID nuevo: ")
    nombre = input("  Nombre: ").strip()

    if not userId or not nombre:
        print("  Datos incompletos.")
        return

    edad = leerInt(
        "  Edad [enter = sin definir]: ",
        default=None
    )

    ubicacion = input(
        "  Ubicación [enter = sin definir]: "
    ).strip() or None

    og.agregarUsuario(userId, nombre, edad, ubicacion)

    print(f"  ✓ Usuario '{nombre}' creado con id {userId}.")


def accion_eliminar_usuario():
    print("\n--- Eliminar usuario ---")

    userId = leerInt("  ID a eliminar: ")

    confirma = input(
        f"  ¿Confirmar eliminación del usuario {userId}? (s/N): "
    ).strip().lower()

    if confirma != "s":
        return

    nombre = og.eliminarUsuario(userId)

    if nombre:
        print(f"  ✓ Usuario '{nombre}' eliminado.")
    else:
        print("  No existe.")


def accion_calificar():
    print("\n--- Calificar contenido ---")

    userId = leerInt("  ID de usuario: ")

    texto = input(
        "  Buscar contenido por título: "
    ).strip()

    if not userId or not texto:
        return

    resultados = og.buscarContenido(texto, limite=10)

    if not resultados:
        print("  Sin resultados.")
        return

    for i, r in enumerate(resultados, 1):
        gens = ", ".join(r["generos"][:3])

        print(
            f"  {i:>2}. "
            f"[{r['movieId']}] "
            f"{r['titulo']} "
            f"({r['year'] or '?'})  "
            f"{gens}"
        )

    idx = leerInt("  Selecciona número: ")

    if not idx or idx < 1 or idx > len(resultados):
        return

    cal = leerFloat("  Calificación (0-5): ")

    if cal is None:
        return

    titulo = og.agregarCalificacion(
        userId,
        resultados[idx - 1]["movieId"],
        cal
    )

    print(f"  ✓ Calificación {cal} guardada para '{titulo}'.")


def accion_historial():
    print("\n--- Historial de usuario ---")

    userId = leerInt("  ID de usuario: ")

    historial = og.historialUsuario(userId, limite=30)

    if not historial:
        print("  Sin historial.")
        return

    for h in historial:
        print(
            f"  ★ {h['calificacion']:.1f}  "
            f"{h['titulo']}  "
            f"(movieId: {h['movieId']})"
        )


def accion_buscar():
    print("\n--- Buscar contenido ---")

    texto = input("  Texto a buscar: ").strip()

    if not texto:
        return

    for r in og.buscarContenido(texto, limite=15):
        gens = ", ".join(r["generos"][:3])

        print(
            f"  [{r['movieId']:>5}] "
            f"{r['titulo']} "
            f"({r['year'] or '?'})  "
            f"{r['duracion'] or '?'} min  "
            f"{gens}"
        )


def accion_amistad():
    print("\n--- Agregar amistad ---")

    u1 = leerInt("  ID usuario 1: ")
    u2 = leerInt("  ID usuario 2: ")

    if u1 is None or u2 is None:
        return

    try:
        og.agregarAmistad(u1, u2)
        print(f"  ✓ Amistad creada entre {u1} y {u2}.")

    except ValueError as e:
        print(f"  Error: {e}")


def accion_plataforma():
    print("\n--- Vincular plataforma a un usuario ---")

    userId = leerInt("  ID de usuario: ")

    plataforma = input(
        "  Nombre de plataforma: "
    ).strip()

    if not userId or not plataforma:
        return

    og.vincularPlataforma(userId, plataforma)

    print(f"  ✓ Usuario {userId} ahora usa {plataforma}.")


def accion_estadisticas():
    print("\n--- Estadísticas de la base de datos ---")

    for k, v in og.estadisticas().items():
        print(f"  {k:<20}: {v}")
        
#Menú principal
acciones=[
    ("Obtener recomendaciones",     accion_recomendar),
    ("Listar usuarios",             accion_listar_usuarios),
    ("Ver historial de un usuario", accion_historial),
    ("Agregar usuario",             accion_agregar_usuario),
    ("Eliminar usuario",            accion_eliminar_usuario),
    ("Calificar contenido",         accion_calificar),
    ("Buscar contenido",            accion_buscar),
    ("Agregar amistad",             accion_amistad),
    ("Vincular plataforma a usuario", accion_plataforma),
    ("Estadísticas de la BD",       accion_estadisticas),
]

def menu():
    if not comprobarConexion():
        print("No se pudo conectar a Neo4j. Revise config.py y que la BD esté arriba.")
        return

    try:
        while True:
            print("\n" + "=" * 50)
            print("  UVGflix - Sistema de Recomendaciones")
            print("=" * 50)
            for i, (nombre, _) in enumerate(acciones, 1):
                print(f"  {i:>2}. {nombre}")
            print("   0. Salir")

            raw = input("\n  Opción: ").strip()
            if raw == "0":
                break
            try:
                idx = int(raw)
                if 1 <= idx <= len(acciones):
                    acciones[idx - 1][1]()
                else:
                    print("  Opción inválida.")
            except ValueError:
                print("  Ingrese un número.")
            except Exception as e:
                print(f"  Error: {e}")
    finally:
        closeDriver()
        print("\n¡Hasta luego!")


if __name__ == "__main__":
    menu()
