# Puntos de guardado

## checkpoint-2026-09-20-editor-visual

Estado inicial bajo Git: motor FastAPI con YAML, chat con contenido multimedia,
panel administrativo y editor visual con creación de ramas, zoom, selección
múltiple, arrastre y plegado de descendientes mediante el ojo.

Incluye el árbol guardado en `data/knowledge.yaml` y los archivos presentes en
`storage/`. Excluye el entorno virtual, cachés, archivos temporales y `.env`.
Los borradores sin guardar y las posiciones guardadas en el navegador no forman
parte de este punto de guardado.

El repositorio es local, sin remoto. Este commit usa la identidad técnica
`Codex <codex@localhost>`; no configura ni suplanta la identidad personal del usuario.

Consultar el historial desde Ubuntu:

```bash
cd /mnt/c/Dev/chatbot
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
