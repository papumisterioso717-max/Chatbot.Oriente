"""Export the existing interfaces as a self-contained GitHub Pages demo."""
import json
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "site"
OUT.mkdir(parents=True, exist_ok=True)
shutil.copytree(ROOT / "app/views/static", OUT / "static", dirs_exist_ok=True)
knowledge = yaml.safe_load((ROOT / "data/knowledge.yaml").read_text(encoding="utf-8"))
(OUT / "knowledge.json").write_text(json.dumps(knowledge, ensure_ascii=False), encoding="utf-8")
for node in knowledge["nodes"].values():
    for item in node["content"]:
        if "file" in item:
            source = (ROOT / "storage" / item["file"]).resolve()
            source.relative_to((ROOT / "storage").resolve())
            target = OUT / "files" / item["file"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

banner = '''<nav class="demo-bar" aria-label="Demostración"><strong>Demo interactiva</strong>
<a href="index.html">Inicio</a><a href="chat.html">Chatbot</a><a href="admin.html">Administrador</a>
<span>Los cambios se guardan solo en este navegador.</span>
<button type="button" onclick="resetDemo()">Restablecer demo</button></nav>'''
for page in ("chat", "admin"):
    html = (ROOT / f"app/views/{page}.html").read_text(encoding="utf-8")
    html = html.replace('"/static/', '"static/').replace('href="/"', 'href="chat.html"')
    html = html.replace('<script src=', '<script src=', 1)
    html = html.replace('</head>', '<link rel="stylesheet" href="demo.css"></head>')
    html = html.replace('<script src="static/', '<script src="demo.js" defer></script><script src="static/', 1)
    html = html.replace('<body>', '<body>' + banner)
    html = html.replace('Guardar árbol', 'Guardar en esta demo')
    (OUT / f"{page}.html").write_text(html, encoding="utf-8")

chat = (OUT / "static/chat.js").read_text(encoding="utf-8")
start, end = chat.index('async function request('), chat.index('function fileUrl(')
chat = chat[:start] + 'async function request(path, body) { return demoChat(path, body); }\n\n' + chat[end:]
chat = chat.replace('"/api/files/"', '"files/"')
(OUT / "static/chat.js").write_text(chat, encoding="utf-8")
admin = (OUT / "static/admin.js").read_text(encoding="utf-8")
start, end = admin.index('async function api('), admin.index('function changed(')
admin = admin[:start] + 'async function api(path, method="GET", body) { return demoAdmin(path, method, body); }\n' + admin[end:]
admin = admin.replace('orienta-node-positions', 'orienta-demo-positions')
admin = admin.replace('Árbol guardado. Ya está disponible en el chatbot.', 'Guardado en este navegador. Abre el chatbot de la demo para probarlo.')
admin = admin.replace('Los cambios se publican al guardar el árbol.', 'Los cambios se guardan solo en este navegador.')
(OUT / "static/admin.js").write_text(admin, encoding="utf-8")
(OUT / ".nojekyll").touch()
for name in ("index.html", "demo.js", "demo.css"):
    shutil.copy2(ROOT / "demo" / name, OUT / name)
print("Demo generada en docs/site")
