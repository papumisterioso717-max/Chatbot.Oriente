# Puntos de guardado

Actualizado el 22 de septiembre de 2026. Último checkpoint funcional: `gestion-diagramas-multiples`.

## Historial disponible

| Commit | Etiqueta | Contenido principal |
| --- | --- | --- |
| `a8e6619` | `checkpoint-2026-09-20-editor-visual` | Editor visual, zoom, arrastre y plegado |
| `0a30a67` | `checkpoint-2026-09-20-lienzo-amplio` | Lienzo amplio; desplazamiento izquierdo de aquella versión |
| `97b0a55` | `checkpoint-2026-09-20-nodos-en-vista` | Crear nodos en huecos de la vista actual |
| `d7da6b5` | `cuadro-seleccionador` | Selección por recuadro con clic izquierdo |
| `8d697cf` | `acomodo-abanico` | Ordenar ramas centradas respecto a su padre |
| `f8d562a` | `arrastre-con-click-rueda` | Desplazamiento con rueda presionada y etiquetas centradas |
| `9036512` | `boton-de-regreso` | Botón Volver y endpoint de historial |
| `a7ee19d` | `color-interfaz` | Paleta azul en chatbot y editor |
| Este commit | `gestion-diagramas-multiples` | Diagramas independientes, respaldos e eliminación cancelable |

`d7da6b5` también tiene la etiqueta `checkpoint-2026-09-20-seleccion-recuadro`.

Para consultar una versión sin modificar el proyecto actual:

```bash
git show color-interfaz --stat
git worktree add --detach ../chatbot-consulta color-interfaz
```

Para restaurar archivos versionados a una etiqueta, revisar primero `git status` y respaldar cualquier trabajo pendiente que se quiera conservar. La siguiente operación reemplaza los archivos versionados y el área de preparación; no elimina archivos nuevos sin seguimiento ni mueve la rama:

```bash
git restore --source=color-interfaz --staged --worktree -- .
git status --short
```

No usar limpieza indiscriminada de archivos sin seguimiento: revisarlos individualmente. Tras restaurar código Python, reiniciar el servidor; para cambios de interfaz, recargar la página. Guardar antes cualquier borrador del panel que se quiera conservar.

Ejecutar los comandos desde la carpeta del proyecto, con Git instalado y disponible en la terminal. Repositorio de GitHub: <https://github.com/papumisterioso717-max/Chatbot.Oriente>. El remoto `origin` apunta a este repositorio. La documentación se versiona junto al código; los checkpoints existentes conservan su contenido original.

## checkpoint-2026-09-20-editor-visual

Estado inicial bajo Git: motor FastAPI con YAML, chat con contenido multimedia,
panel administrativo y editor visual con creación de ramas, zoom, selección
múltiple, arrastre y plegado de descendientes mediante el ojo.

Incluye el árbol guardado en `data/knowledge.yaml` y los archivos presentes en
`storage/`. Excluye el entorno virtual, cachés, archivos temporales y `.env`.
Los borradores sin guardar y las posiciones guardadas en el navegador no forman
parte de este punto de guardado.

El repositorio se creó inicialmente de forma local, sin remoto. Este commit usa la identidad técnica
`Codex <codex@localhost>`; no configura ni suplanta la identidad personal del usuario.

Consultar el historial desde Ubuntu:

```bash
cd Chatbot.Oriente
git log --oneline --decorate
git status
git show checkpoint-2026-09-20-editor-visual --stat
```

Crear otro punto de guardado tras guardar los cambios del editor:

```bash
git add app data storage tests README.md CHECKPOINTS.md requirements.txt .gitignore .gitattributes
git commit -m "Describe los cambios realizados"
git tag checkpoint-nombre-descriptivo
```

Configura antes tu nombre y correo de Git si aún no los tienes establecidos.
Para consultar este punto en una carpeta independiente, sin sobrescribir el
trabajo actual:

```bash
git worktree add --detach ../chatbot-checkpoint checkpoint-2026-09-20-editor-visual
```

Git no guarda automáticamente las ediciones del panel. Pulsa primero Guardar
árbol y después crea el commit correspondiente. Un repositorio local no sustituye
una copia de respaldo en otro dispositivo.
