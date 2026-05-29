#Nombre del archivo: config.py
#Autores:
    #Abigail Escobar
    #Alejandro Rustrian
    #Antony Portillo
#Fecha: 27/05/2026
#Descripcion: Limpia la base de datos, lo cual es util para volver a hacer pruebas

import sys
from database import session, closeDriver


def reset(confirmado=False):
    if not confirmado:
        respuesta = input(
            "Esto eliminará TODOS los nodos y relaciones. "
            "Escriba 'si' para confirmar: "
        ).strip().lower()
        if respuesta != "si":
            print("Cancelado.")
            return

    print("Eliminando todo...")
    with session() as s:
        # Borrado por bloques
        while True:
            r = s.run("""
                MATCH (n)
                WITH n LIMIT 10000
                DETACH DELETE n
                RETURN count(n) AS borrados
            """).single()
            borrados = r["borrados"]
            print(f"  borrados {borrados} nodos")
            if borrados == 0:
                break

    print("Base de datos limpia.")


if __name__ == "__main__":
    confirmado = "--yes" in sys.argv or "-y" in sys.argv
    try:
        reset(confirmado=confirmado)
    finally:
        closeDriver()
