# UVGflix - Sistema de Recomendacion

Sistema de recomendacion de peliculas construido con Python y Neo4j. El proyecto usa un grafo para conectar usuarios, contenido, generos, plataformas, estados de animo y calificaciones.

## Que hace

- Carga el dataset de MovieLens (`movies.csv` y `ratings.csv`) en Neo4j.
- Crea usuarios, peliculas, generos, plataformas, estados de animo y amistades.
- Recomienda contenido con un enfoque hibrido:
  - filtrado colaborativo: usuarios con gustos similares;
  - filtrado por contenido: peliculas parecidas por genero;
  - filtros por tiempo disponible, plataforma y estado de animo.
- Incluye interfaz de consola y una interfaz grafica con login, guest y registro de usuario.

## Requisitos

- Python 3.10 o superior.
- Neo4j Desktop o Neo4j Server.
- Git, si se va a clonar desde GitHub.

Dependencias de Python:

```powershell
python -m pip install -r requirements.txt
```

## Configurar Neo4j

1. Crea o abre una base de datos en Neo4j.
2. Inicia la base.
3. Asegurate de que Bolt este activo en:

```text
bolt://127.0.0.1:7687
```

4. Configura las credenciales en `config.py`:

```python
url = "bolt://127.0.0.1:7687"
user = "neo4j"
password = "uvgflixproyecto"
databaseNeo4j = "neo4j"
```

Si tu Neo4j tiene otra contrasena, cambia `password`.

## Instalacion

Desde PowerShell:

```powershell
git clone https://github.com/ADAESXX/Sistema-de-Recomendacion-UVGflix.git
cd Sistema-de-Recomendacion-UVGflix
python -m pip install -r requirements.txt
```

## Cargar la base de datos

Con Neo4j encendido, ejecuta:

```powershell
python -X utf8 loadMovieLens.py
```

Esto carga:

- peliculas;
- usuarios;
- calificaciones;
- generos;
- plataformas;
- estados de animo;
- amistades ficticias para probar recomendaciones sociales.

La carga completa usa 9,742 peliculas y 100,836 calificaciones. Para una prueba rapida puedes limitar ratings:

```powershell
python -X utf8 loadMovieLens.py 5000
```

No vuelvas a correr la carga completa si la base ya tiene datos, a menos que quieras recargar o reiniciar el grafo.

## Ejecutar la interfaz grafica

Primero inicia Neo4j. Luego:

```powershell
.\runUVGflixGUI.bat
```

O directamente:

```powershell
python -X utf8 gui_uvgflix.py
```

La GUI incluye:

- inicio de sesion por ID;
- ingreso como guest;
- registro de usuario con preferencias;
- recomendaciones hibridas;
- busqueda de contenido;
- calificaciones;
- usuarios e historial;
- amistades;
- plataformas;
- estadisticas de la base.

## Ejecutar la version de consola

Primero inicia Neo4j. Luego:

```powershell
.\runUVGflix.bat
```

O directamente:

```powershell
python -X utf8 main.py
```

## Ejecutar pruebas de recomendacion

Para probar escenarios con un usuario especifico:

```powershell
python -X utf8 pruebas.py 1
```

Si no pasas IDs, el script usa los usuarios mas activos:

```powershell
python -X utf8 pruebas.py
```

## Limpiar la base de datos

Advertencia: esto borra todos los nodos y relaciones.

```powershell
python -X utf8 reset.py --yes
```

Despues de limpiar, vuelve a cargar datos con:

```powershell
python -X utf8 loadMovieLens.py
```

## Problemas comunes

### No se puede conectar a Neo4j

Verifica que Neo4j este encendido:

```powershell
Test-NetConnection 127.0.0.1 -Port 7687
```

Debe mostrar:

```text
TcpTestSucceeded : True
```

Si sale `False`, abre Neo4j Desktop e inicia la base de datos.

### Error de autenticacion

Revisa `config.py`. El usuario y contrasena deben coincidir con tu base de Neo4j.

### Caracteres raros o errores con tildes

Usa siempre `-X utf8`:

```powershell
python -X utf8 gui_uvgflix.py
```

Los scripts `.bat` ya lo usan automaticamente.

## Estructura principal

```text
config.py              Configuracion de Neo4j
database.py            Conexion, sesiones, constraints e indices
loadMovieLens.py       Carga de datos a Neo4j
recomendador.py        Motor de recomendaciones
operacionesGrafo.py    Operaciones CRUD sobre el grafo
main.py                Interfaz de consola
gui_uvgflix.py         Interfaz grafica
pruebas.py             Escenarios de prueba
reset.py               Limpieza de base de datos
```

## Notas

El sistema usa Neo4j porque el problema se basa en relaciones: usuarios conectados con peliculas, peliculas conectadas con generos, usuarios similares, amistades, plataformas y preferencias. Esa estructura permite recomendaciones mas personalizadas y explicables que una busqueda simple por categorias.
