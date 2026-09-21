# Orienta — chatbot de decisiones

Documentación actualizada el 21 de septiembre de 2026. Base funcional: checkpoint `color-interfaz` (`a7ee19d`).

Chatbot guiado por opciones, con contenido definido en YAML y editor visual de nodos. Usa Python, FastAPI y JavaScript sin framework de interfaz. Las respuestas provienen del árbol configurado; no se generan con inteligencia artificial.

## Iniciar en Linux (WSL)

Requisitos: Git y Python 3.12 con soporte para entornos virtuales. Desde Linux o una terminal de Ubuntu en WSL, clona el repositorio y prepara el entorno una sola vez:

```bash
git clone https://github.com/papumisterioso717-max/Chatbot.Oriente.git
cd Chatbot.Oriente
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Nota sobre las rutas:** `.venv` es una carpeta dentro del proyecto, no un nombre de usuario. Los comandos se ejecutan desde la carpeta donde clonaste el repositorio. Si ya tienes el proyecto, entra en su carpeta y omite `git clone`. Si utilizas un entorno virtual existente en otra ubicación, activa ese entorno con su propia ruta; no es necesario moverlo. Esta guía sustituye las rutas personales de la versión anterior por rutas relativas.

Para volver a iniciar en otra terminal, entra en la carpeta del proyecto y ejecuta:

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Detener con Ctrl+C. Ejecutar un solo proceso: las sesiones no se comparten entre workers.

| Dirección | Uso |
| --- | --- |
| <http://localhost:8000/> | Chatbot |
| <http://localhost:8000/admin> | Editor visual |
| <http://localhost:8000/docs> | API interactiva |

Como alternativa, con `uv` instalado y desde la carpeta del proyecto:

```bash
uv venv --python 3.12 --seed .venv
uv pip install --python .venv/bin/python -r requirements.txt
source .venv/bin/activate
```

Dependencias directas: FastAPI 0.115.12, Uvicorn 0.34.2 y PyYAML 6.0.2. Pydantic se instala como dependencia de FastAPI.

## Documentación

- [Manual de uso](docs/MANUAL.md): chatbot, controles del editor, multimedia y guardado.
- [Documentación técnica](docs/TECNICA.md): arquitectura, datos, API, pruebas y limitaciones.
- [Checkpoints de Git](CHECKPOINTS.md): versiones guardadas y recuperación.

## Estado actual

Incluye navegación por opciones, botón Volver, multimedia, administración del árbol, zoom, selección con recuadro, arrastre de nodos, desplazamiento con rueda presionada, plegado de ramas, acomodo en abanico y paleta azul.

El panel es local y no tiene autenticación. **Guardar árbol** publica el borrador e invalida las conversaciones activas. El borrador no se guarda automáticamente. Las posiciones se conservan por navegador y no forman parte del YAML ni de Git.

## Pruebas

```bash
python -m unittest tests.test_back -v
python -m unittest discover -s tests -v
```

Ejecutar desde la carpeta del proyecto con el entorno activado. Las pruebas históricas dependen parcialmente del árbol de ejemplo, ya personalizado; necesitan fixtures independientes antes de usarse como validación general. Esta actualización documental no certifica una ejecución nueva de toda la suite. Más detalles en la documentación técnica.
