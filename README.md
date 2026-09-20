# Chatbot de decisiones — Fases 1 a 5

## Editor visual actual (fase 5)

Abre <http://localhost:8000/admin>. A la izquierda verás el árbol y a la derecha
la configuración del nodo seleccionado. En pantallas pequeñas se apilan.

- Pulsa una tarjeta para editar su contenido y sus opciones.
- **Nueva opción + nodo** crea inmediatamente un nodo y una conexión en el borrador.
  Edita el texto del botón y pulsa **Configurar nodo destino** para escribir su respuesta.
  Puedes repetirlo en ese nuevo nodo para crear más niveles.
- **Conectar existente / acción** añade una opción cuyo destino puedes escoger.
  Volver y Menú principal se representan como acciones, sin crear nodos ficticios.
- **+ Nodo** crea un nodo independiente; puedes conectarlo después. Los nodos sin
  ruta desde el inicio se identifican con **SIN CONEXIÓN**.
- Los textos y conexiones del diagrama cambian mientras escribes. Cambiar de nodo
  no descarta el trabajo realizado en otros nodos.
- **Guardar árbol** publica todos los cambios juntos. **Recargar** permite descartar
  el borrador y recuperar la versión guardada, previa confirmación.

El borrador permanece en memoria del navegador; no se recupera tras cerrar la
página. No hay animaciones ni colaboración en vivo entre usuarios.
El lienzo tiene desplazamiento horizontal/vertical, búsqueda que resalta coincidencias
y **Centrar selección**. Cada nodo aparece una sola vez, incluso si se reutiliza.
Los botones **− / +** de la esquina inferior derecha ajustan el zoom del lienzo
entre 25 % y 200 %, en pasos de 25 %. Solo escalan nodos y conexiones; el panel de
configuración y los controles conservan su tamaño. **Centrar selección** respeta
el zoom elegido. El zoom es visual y no modifica el YAML ni requiere guardar.
Mantén el **botón izquierdo** sobre el fondo vacío del lienzo y arrastra para
desplazar la vista horizontal o verticalmente. Funciona con cualquier zoom y
respeta los límites de desplazamiento. No mueve los nodos ni modifica el árbol;
el clic derecho mantiene su menú habitual.
Puedes arrastrar un nodo individual o usar **Ctrl + clic** para seleccionar varios.
**Seleccionar todos** (o Ctrl + A con el foco dentro del lienzo) permite moverlos
juntos arrastrando cualquiera de los seleccionados. Escape o un clic en el fondo
limpia la selección. Las conexiones siguen el movimiento y el arrastre respeta el
zoom. **Ordenar nodos** restablece la distribución automática. Las posiciones se
guardan localmente en este navegador; no cambian el YAML ni las respuestas.
El **ojo** de cada nodo oculta o muestra todos sus descendientes y sus conexiones.
Cuando la rama está plegada, el ojo aparece tachado y el padre permanece visible.
Las ramas plegadas dentro de otra conservan su estado al reabrir el padre.
Los nodos sin hijos muestran el control desactivado. Seleccionar todos solo incluye
los nodos visibles. Es una preferencia temporal de la vista: no elimina contenido
ni cambia el chatbot. Un nodo reutilizado también se oculta si es descendiente
de la rama plegada; el nodo inicial siempre permanece disponible.
Los ciclos no provocan recorridos infinitos en el dibujo.

Los IDs de nodos nuevos se generan automáticamente. El motor sigue utilizando YAML
como fuente. `PUT /api/admin/tree` valida y guarda atómicamente nodos y conexiones
con control de revisión. Un conflicto o error conserva el borrador del panel.
Al guardar se reinician las sesiones activas, como en fase 4.

Archivos: `app/views/admin.html`, `static/admin.js`, `static/graph.css`, modelos,
rutas/controlador/servicio administrativos y `tests/test_phase4.py`. No se añadieron
dependencias. Se mantienen el entorno virtual y el comando de ejecución en Ubuntu.
Las instrucciones históricas de fase 4 sobre crear primero el destino y guardar
cada nodo individualmente quedan sustituidas por este flujo visual.

Verificación automática: 24 pruebas correctas, incluidas ramas de varios niveles,
navegación tras guardar, conflictos y conservación de datos ante fallos de escritura.

Backend local con Python, FastAPI, Uvicorn, YAML y arquitectura MVC.
Esta entrega implementa el motor, la interfaz y recursos multimedia. Todo el código está completo en
los archivos del proyecto; no es necesario copiar fragmentos de la conversación.

## Qué construimos

El YAML define el nombre del bot, su nodo inicial, textos y opciones. El motor
recibe el ID de una opción del nodo actual y aplica `next`, `back` o `restart`.
Cada conversación tiene un ID de sesión, historial y revisión propios. La revisión
evita procesar dos veces una selección hecha sobre un estado anterior.

La estructura es un grafo dirigido: varios nodos pueden apuntar al mismo destino.
`back` utiliza el historial real, no un supuesto padre del árbol. En el nodo
inicial, volver sin historial conserva el nodo actual. Reiniciar vacía el historial.

## Archivos y responsabilidades

Todos se encuentran dentro de `C:\Dev\chatbot`:

```text
chatbot/
├── venv/                         Entorno virtual local
├── app/
│   ├── main.py                   Construcción de FastAPI y carga inicial
│   ├── models/
│   │   ├── content.py            Contenido de texto (fase 1)
│   │   ├── option.py             Opción: destino o acción
│   │   ├── node.py               Nodo y opciones
│   │   ├── knowledge.py          Configuración y referencias
│   │   └── conversation.py       Entrada y respuesta de la API
│   ├── services/
│   │   ├── yaml_manager.py       Lectura segura y validación del YAML
│   │   └── chatbot_engine.py     Navegación e historial, sin HTTP
│   ├── controllers/
│   │   └── chat_controller.py    Coordina solicitudes y motor
│   ├── routes/
│   │   └── chat.py               Endpoints y modelos de respuesta
│   └── views/
│       ├── chat.html             Página del chat
│       └── static/
│           ├── chat.css          Diseño adaptable a pantallas pequeñas
│           └── chat.js           Mensajes, botones y llamadas a la API
├── data/knowledge.yaml           Única fuente del contenido conversacional
├── tests/test_phase1.py          Pruebas del motor, YAML y API real
├── requirements.txt
└── README.md
```

La interfaz HTML está disponible en `/`, y la documentación de la API en `/docs`.
La fase 2 no añade dependencias. El administrador, las escrituras de YAML y
el gestor de archivos se implementarán en sus fases correspondientes.

## Entorno Linux en WSL (opción elegida)

Distribución: Ubuntu-20.04. El entorno Linux se ubica en
`/home/yaqz/.venvs/chatbot`, separado del entorno Windows. El código compartido
está disponible en `/mnt/c/Dev/chatbot`.

Desde una terminal de Ubuntu:

```bash
cd /mnt/c/Dev/chatbot
source /home/yaqz/.venvs/chatbot/bin/activate
python -m unittest discover -s tests -v
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Abre <http://localhost:8000> desde el navegador de Windows. Para salir del
entorno ejecuta `deactivate`; para detener el servidor usa Ctrl+C.

El Python predeterminado de Ubuntu 20.04 es 3.8 en este equipo. Se utiliza Python
3.12 gestionado por `uv` en el usuario, sin sustituir el Python del sistema.
Para recrear el entorno Linux una vez instalado `uv`:

```bash
~/.local/bin/uv venv --python 3.12 --seed /home/yaqz/.venvs/chatbot
~/.local/bin/uv pip install --python /home/yaqz/.venvs/chatbot/bin/python -r /mnt/c/Dev/chatbot/requirements.txt
```

No actives `venv/Scripts` desde Ubuntu: ese entorno pertenece a Windows.

## Instalar en Windows (alternativa)

En este equipo ya se creó `venv`. Para reconstruirlo en otro equipo con Python
3.10 o posterior disponible:

```powershell
cd C:\Dev\chatbot
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

En CMD, la activación es `venv\Scripts\activate.bat`. La activación es opcional:
si PowerShell no permite ejecutar el script, usa directamente el intérprete del
entorno sin cambiar las políticas del sistema:

```powershell
cd C:\Dev\chatbot
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Las dependencias directas son FastAPI, Uvicorn y PyYAML. FastAPI instala Pydantic,
que se usa para validar los modelos. Las pruebas usan la biblioteca estándar.

## Ejecutar

```powershell
cd C:\Dev\chatbot
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Abre <http://127.0.0.1:8000> para el chat o `/docs` para la API.
Detén el servidor con Ctrl+C.

## Probar la interfaz de fase 2

1. Abre `/`: aparece el texto del nodo inicial y sus botones.
2. Selecciona **Titulación → Modalidades → Tesis**.
3. Selecciona **Volver**: reaparecen las opciones de Modalidades.
4. Selecciona **Menú principal**: vuelven las opciones iniciales.

La interfaz conserva los mensajes visibles, aunque reiniciar vacía el historial
de navegación del motor. Solo hay botones activos para el nodo actual. Los textos
se insertan como texto plano, no como HTML. Cada recarga inicia una sesión nueva;
la conversación no se guarda en el navegador. Si una solicitud falla, se ofrece
iniciar otra conversación para evitar repetir una selección cuyo resultado se
desconoce. El registro visual conserva los últimos 100 mensajes.

Verificación realizada en Ubuntu: 10 pruebas automáticas correctas, más recorrido
completo en navegador con botones, volver y menú principal. La página también se
inspeccionó visualmente en una ventana estrecha.

## Probar manualmente

1. En `/docs`, ejecuta `GET /api/chat/start` usando **Try it out** y **Execute**.
2. Copia `session_id` y `revision` de la respuesta. El nodo inicial es `inicio`.
3. Ejecuta `POST /api/chat/select` con este cuerpo, sustituyendo el ID:

```json
{
  "session_id": "ID_RECIBIDO",
  "option_id": "titulacion",
  "revision": 0
}
```

4. Con el mismo ID y la nueva revisión de cada respuesta, selecciona `modalidades`
   y luego `tesis`. El historial será `inicio`, `titulacion`, `modalidades`.
5. Selecciona `volver`: aparecerá `modalidades`.
6. Selecciona `inicio`: aparecerá `inicio` y el historial quedará vacío.
7. Prueba una opción inexistente: devuelve 400 sin cambiar la conversación.

| Endpoint | Función |
| --- | --- |
| `GET /api/chat/start` | Crea una conversación independiente |
| `POST /api/chat/select` | Selecciona una opción del nodo actual |
| `GET /api/chat/node/{node_id}` | Consulta un nodo sin modificar ninguna sesión |

Errores: 400 para opción inválida; 404 para nodo o sesión inexistente/caducada;
409 para revisión desactualizada o historial lleno; 422 para cuerpo inválido;
503 si se alcanza el límite de sesiones.

## Pruebas automáticas

```powershell
cd C:\Dev\chatbot
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas arrancan y detienen su propio servidor local en un puerto temporal.
Comprueban navegación completa, volver, reiniciar, nodos compartidos, sesiones
independientes, caducidad, capacidad, selecciones inválidas/desactualizadas,
ciclos y errores YAML, además de respuestas HTTP reales.

## Editar el contenido durante esta fase

Edita `data/knowledge.yaml` y reinicia el servidor: el YAML se carga y valida al
arrancar, no en cada solicitud. No dependas de `--reload` para detectar cambios
en YAML. El ejemplo no contiene información institucional real.

Los IDs de nodo admiten letras ASCII, números, guiones y guiones bajos. Los IDs
de opciones son únicos dentro de cada nodo; `volver` puede reutilizarse en nodos
distintos. Cada opción exige exactamente un `next` o una `action`. Se rechazan
claves YAML duplicadas, campos desconocidos, destinos inexistentes y un nodo
inicial inexistente. `version: 1` identifica el formato para futuras migraciones.

## Alcance y próximos pasos

Las sesiones viven en memoria, caducan tras una hora sin selección y se pierden
al reiniciar. El límite es de 1000 sesiones y 1000 pasos de historial por sesión.
Ejecuta un solo proceso de Uvicorn: varios workers no compartirían sesiones.
Esta versión es para uso local y no incorpora autenticación ni persistencia de
sesiones. Las opciones `back` y `restart` deben estar declaradas en el YAML.

Los ciclos explícitos están permitidos en esta fase; no se recorre el grafo
recursivamente. La detección configurable de ciclos y nodos huérfanos queda para
la fase de validaciones. Imágenes, documentos y enlaces están disponibles desde
la fase 3; los tipos desconocidos se rechazan para evitar contenido ignorado.

El editor visual de la fase 5 está disponible; su uso se explica al inicio de esta guía.

## Fase 3: enlaces, imágenes y documentos

No se requieren dependencias adicionales. Activa el entorno de Ubuntu y ejecuta
el mismo comando de Uvicorn indicado arriba. Abre `/` y selecciona **Recursos de
ejemplo**: verás una imagen del recorrido, una guía TXT con opciones para verla o
descargarla y un enlace a Python.org. Volver y Menú principal funcionan igual.

Archivos creados/modificados:

- `app/models/content.py`: unión de tipos text, link, image y document; valida URL,
  rutas relativas, carpetas y extensiones. `node.py` acepta la unión conservando
  compatibilidad con los nodos de texto anteriores.
- `app/services/file_manager.py`: comprueba existencia y rutas; solo permite
  servir referencias presentes en el YAML y rechaza enlaces simbólicos.
- `app/controllers/file_controller.py` y `app/routes/files.py`: visualización y
  descarga mediante `GET /api/files/{referencia}?download=true`.
- `app/main.py`: valida todas las referencias al iniciar y registra la ruta.
- `app/views/static/chat.js` y `chat.css`: muestran contenido mixto en su orden,
  imágenes adaptables, tarjetas de documento y enlaces en otra pestaña.
- `storage/images/recorrido.png` y `storage/documents/guia.txt`: recursos de ejemplo.
- `data/knowledge.yaml`: nodo `recursos`. `tests/test_phase3.py`: pruebas adicionales.

Coloca archivos dentro de `storage/images/` o `storage/documents/`. En el YAML,
escribe la referencia sin el prefijo `storage/`:

```yaml
content:
  - type: text
    text: "Consulta los recursos disponibles."
  - type: image
    file: "images/recorrido.png"
    alt: "Tres pasos para navegar por el chatbot."
  - type: document
    label: "Guía de navegación"
    file: "documents/guia.txt"
  - type: link
    label: "Python.org"
    url: "https://www.python.org/"
```

Imágenes permitidas: PNG, JPG/JPEG, GIF y WEBP. Documentos: PDF, TXT, DOCX, XLSX y
PPTX. PDF y TXT ofrecen **Ver documento** y **Descargar**; los formatos de Office
ofrecen descarga para abrirlos con su aplicación. La vista PDF depende del visor
del navegador. Los TXT se leen en un visor dentro del chat, compatible con el
navegador integrado. Las imágenes ofrecen también un enlace para abrirlas aparte.

Los archivos nunca se incrustan en YAML. Para reemplazar un recurso manualmente,
sustituye el archivo conservando su ruta. Si añades o cambias referencias, reinicia
el servidor. Un archivo referenciado inexistente impide el arranque con un error
claro. Si se elimina después del arranque, devuelve 404. Estos recursos son
públicos para quien acceda al chatbot; no coloques documentos privados en ellos.

Esta fase valida extensiones y rutas, pero no analiza el contenido binario de
archivos subidos: la subida y su control se implementarán con la administración.
No se monta toda la carpeta storage como directorio público. Los enlaces admiten
solo HTTP/HTTPS sin credenciales y se abren con separación de la pestaña original.

Verificación: 16 pruebas automáticas correctas en Ubuntu. En el navegador se
comprobó el nodo mixto, la imagen y la apertura/cierre del visor TXT. La respuesta
de descarga se verificó por HTTP; no se ha probado el visor PDF con un PDF real.

Pruebas en Ubuntu:

```bash
cd /mnt/c/Dev/chatbot
source /home/yaqz/.venvs/chatbot/bin/activate
python -m unittest discover -s tests -v
```

## Fase 4: panel administrativo local

Abre <http://localhost:8000/admin>. No se añadieron dependencias. Inicia el
servidor con el entorno de Ubuntu y el mismo comando de Uvicorn de esta guía.

1. Selecciona un nodo de la lista o pulsa **Crear nodo**.
2. Escribe un ID único (letras, números, guiones o guiones bajos) y elige su tipo.
3. Añade bloques de texto, enlaces, imágenes o documentos existentes.
4. Añade opciones: cada una tiene un ID, el texto del botón y un nodo destino o
   una acción **Volver** / **Menú principal**. Puedes editar o quitar cada opción.
5. Pulsa **Guardar cambios**. El YAML se guarda y el motor se actualiza al momento.

Para crear una bifurcación, crea y guarda primero el nodo destino. Después edita
el nodo origen y añade una opción que lo apunte. Los nodos aún no conectados se
marcan como **Sin ruta desde el inicio**. El editor gráfico llegará en fase 5.

El ID de un nodo existente no cambia. El nodo inicial no puede eliminarse y la
eliminación de un nodo con referencias se rechaza mostrando las opciones que lo
usan. Al eliminar un nodo no se eliminan sus archivos físicos. Los archivos se
referencian con rutas relativas; este panel aún no incluye subida de archivos.

El guardado valida el grafo y los archivos antes de reemplazar el YAML de forma
atómica. Si otro panel o una edición externa cambió el archivo, se rechaza el
guardado desactualizado: usa **Recargar datos** y revisa los cambios. Al guardar
se invalidan las sesiones de chat activas para evitar que naveguen sobre opciones
antiguas; la interfaz ofrecerá iniciar otra conversación. No hay deshacer ni
versionado de contenido todavía. La reescritura conserva los datos, no comentarios
ni formato manual del YAML.

Archivos de fase 4:

- `app/models/admin.py`: solicitudes administrativas.
- `app/services/admin_service.py`: cambios, referencias, revisiones y actualización
  del motor. `yaml_manager.py`: escritura atómica.
- `app/controllers/admin_controller.py` y `app/routes/admin.py`: API administrativa.
- `app/views/admin.html`, `static/admin.css` y `static/admin.js`: formularios.
- `app/main.py`: registra panel, servicios y protección del host.
- `tests/test_phase4.py`: pruebas sobre una copia temporal, sin alterar el YAML real.

API: `GET /api/admin/tree`, `POST /api/admin/node`, `PUT /api/admin/node/{id}` y
`DELETE /api/admin/node/{id}`. Las opciones se guardan junto con su nodo para que
el cambio completo sea atómico. Las peticiones requieren el encabezado
`X-Admin-Request: local-panel`; las escrituras incluyen la revisión recibida del
panel. Este encabezado y la comprobación de origen protegen contra solicitudes
desde otras páginas; no sustituyen autenticación. El panel es para uso local:
mantén Uvicorn en `127.0.0.1`, con un solo proceso. No lo publiques en red sin
añadir autenticación. Cualquier usuario con acceso local puede administrarlo.

Verificación de fase 4: 21 pruebas correctas, incluidas creación/edición/eliminación,
opciones, conflictos, referencias inválidas, archivos inexistentes, recuperación
ante fallos de escritura y acceso HTTP al panel.

El lienzo conserva un margen amplio alrededor del árbol en todos los niveles de zoom. Arrastra el fondo con el botón izquierdo para explorar en cualquier dirección; Centrar selección permite regresar al nodo seleccionado.
