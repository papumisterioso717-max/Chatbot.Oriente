# Documentación técnica

Fecha: 21 de septiembre de 2026. La aplicación declara `0.5.0` en `app/main.py`; los checkpoints identifican los avances posteriores de interfaz.

## Arquitectura

Flujo: navegador → rutas FastAPI → controlador → servicio → modelos/datos.

| Ubicación | Responsabilidad |
| --- | --- |
| `app/main.py` | Inicialización, rutas, archivos estáticos, hosts y errores |
| `app/models/` | Validación del conocimiento, contenido y solicitudes |
| `app/routes/` | Endpoints de chat, administración y archivos |
| `app/controllers/` | Coordinación entre rutas y servicios |
| `app/services/chatbot_engine.py` | Sesiones, navegación, historial y revisión |
| `app/services/yaml_manager.py` | Lectura validada y escritura atómica |
| `app/services/admin_service.py` | Publicación, conflictos y actualización del motor |
| `app/services/diagram_catalog.py` | Catálogo de diagramas, migración inicial y escritura atómica |
| `app/services/file_manager.py` | Archivos publicados y rutas seguras |
| `app/views/chat.html`, `static/chat.js`, `static/chat.css` | Interfaz conversacional |
| `app/views/admin.html`, `static/admin.js`, `static/admin.css` | Borrador, formularios y grafo |
| `app/views/static/pan.js`, `graph.css` | Selección, desplazamiento y estilos del lienzo |
| `app/views/static/blue-theme.css` | Paleta azul compartida, cargada después de estilos base |
| `data/knowledge.yaml`, `storage/` | Contenido y recursos |
| `tests/` | Pruebas automáticas |

## Modelo de contenido

El grafo admite nodos compartidos y ciclos. Los IDs aceptan letras ASCII, números, guion y guion bajo. Cada opción tiene exactamente `next` o una acción `back`/`restart`. Se rechazan destinos inexistentes, nodo inicial inexistente, campos desconocidos y claves YAML duplicadas.

Ejemplo ilustrativo; no sustituir el contenido real con este ejemplo:

```yaml
version: 1
bot:
  name: Asistente
  start_node: inicio
nodes:
  inicio:
    type: question
    content:
      - type: text
        text: ¿Qué información necesitas?
    options:
      - id: consultar
        label: Ver información
        next: informacion
  informacion:
    type: information
    content:
      - type: text
        text: Respuesta configurada.
    options:
      - id: menu
        label: Menú principal
        action: restart
```

Los archivos se referencian por ruta y no se incrustan en los respaldos. Publicar valida los recursos y reemplaza atómicamente `data/diagrams.json`. Si el catálogo no existe, se importa el YAML original como Diagrama 1 sin modificarlo. Desde ese momento el catálogo es la fuente de datos activa.

## API

| Método y ruta | Función |
| --- | --- |
| `GET /api/chat/start` | Nueva sesión |
| `POST /api/chat/select` | Seleccionar opción actual |
| `POST /api/chat/back` | Retroceder sin necesitar opción back en el nodo |
| `GET /api/chat/node/{node_id}` | Consulta sin modificar sesión |
| `GET /api/admin/tree` | Conocimiento y revisión administrativa |
| `POST /api/admin/diagrams` | Crear, cambiar, renombrar o eliminar: `{action, revision, diagram_id?, name?, knowledge?}` |
| `PUT /api/admin/tree` | Publicar árbol completo: `{revision, knowledge}` |
| `POST /api/admin/node` | Crear: `{revision, node_id, node}` |
| `PUT /api/admin/node/{node_id}` | Actualizar: `{revision, node_id, node}` |
| `DELETE /api/admin/node/{node_id}` | Eliminar: `{revision}` |
| `GET /api/files/{reference}` | Leer recurso publicado |
| `GET /api/files/{reference}?download=true` | Descargar recurso |

Selección:

```json
{"session_id":"ID_RECIBIDO","option_id":"ID_DE_OPCION_ACTUAL","revision":0}
```

Regreso:

```json
{"session_id":"ID_RECIBIDO","revision":1}
```

Respuesta de navegación: `session_id`, `bot_name`, `node_id`, `node`, `history`, `revision`. Enviar siempre la última revisión recibida. `next` apila el nodo actual; `back` extrae el último visitado; `restart` vacía el historial y regresa al inicio. Volver sin historial mantiene el nodo actual. Cada operación válida incrementa la revisión.

Las rutas administrativas requieren `X-Admin-Request: local-panel` y comprueban el origen. Esto no es autenticación. Su revisión es una cadena, independiente del entero de revisión del chat. El editor actual usa el guardado completo del árbol.

Errores principales: 400 opción inválida, 403 petición administrativa no autorizada, 404 recurso o sesión inexistente, 409 conflicto/revisión desactualizada, 422 validación y 503 capacidad de sesiones. Consultar esquemas exactos en `/docs`.

## Persistencia y límites

Sesiones en memoria de un proceso: máximo 1000 sesiones, historial de hasta 1000 pasos y caducidad de una hora sin actividad. Reiniciar o publicar el árbol invalida las sesiones. El cliente bloquea operaciones simultáneas y evita reintentos automáticos ambiguos si se pierde una respuesta. El registro visible conserva 100 mensajes.

El borrador vive en `admin.js`. Las posiciones se guardan en localStorage bajo `orienta-node-positions`; selección y plegado son temporales. + Nodo busca huecos en coordenadas de pantalla y convierte la ubicación según zoom y desplazamiento. El lienzo es amplio pero finito.

El acomodo en abanico construye una jerarquía de primer padre para posicionar nodos compartidos sin recorrer ciclos infinitamente. Reserva altura por subárbol y conserva la posición de inicio. Las etiquetas se colocan a mitad de longitud de la curva con orientación legible.

Los archivos se limitan a referencias publicadas dentro de `storage/`. Se rechazan rutas inseguras y enlaces simbólicos. Se valida extensión y existencia, no el contenido binario. Las respuestas llevan `Cache-Control: no-store`.

Aplicación local sin autenticación, colaboración simultánea, subida de archivos ni recuperación automática de borradores. Mantener Uvicorn en `127.0.0.1` con un solo proceso.

## Pruebas

```bash
python -m unittest tests.test_back -v
python -m unittest discover -s tests -v
```

| Archivo | Cobertura prevista |
| --- | --- |
| `test_phase1.py` | Motor, YAML, sesiones y API |
| `test_phase3.py` | Multimedia y archivos |
| `test_phase4.py` | Administración, conflictos y guardado |
| `test_back.py` | Regreso repetido, revisión y sesión inexistente |
| `test_diagrams.py` | Migración, independencia, importación, conflictos, eliminación y fallos de escritura |

Las cuatro pruebas de `tests.test_diagrams` usan datos temporales independientes y se verificaron para esta actualización. La interfaz incluye una cuenta regresiva cancelable de cinco segundos antes de enviar la eliminación al servidor. Las posiciones se guardan por diagrama bajo `orienta-node-positions:<id>`; los respaldos JSON incluyen nombre, conocimiento y posiciones. La demo conserva su catálogo en el almacenamiento local del navegador.

Las pruebas históricas dependen parcialmente del árbol de ejemplo original. El contenido actual está personalizado: los conteos históricos de pruebas aprobadas no certifican este estado. `test_back.py` presupone dos opciones next consecutivas. Migrar a fixtures explícitos antes de automatizar validación general; no reemplazar datos reales para satisfacer pruebas antiguas. En esta actualización documental no se ejecutó la suite.

Comprobaciones manuales recomendadas tras cambios funcionales:

1. Avanzar dos pasos y volver dos veces; comprobar opciones.
2. Seleccionar por clic/recuadro, mover un grupo y desplazar con rueda presionada.
3. Probar zoom mínimo/máximo y crear un nodo en un hueco visible.
4. Plegar ramas y ordenar en abanico; verificar posición de inicio.
5. En datos de prueba, publicar cambios y comprobar conflictos y renovación de sesión.
6. Revisar multimedia, teclado y pantallas estrechas cuando se afecten esas áreas.

## Mantenimiento

Si WSL no detecta cambios Python sobre la carpeta compartida, detener y reiniciar Uvicorn. Editar el YAML original no modifica un catálogo ya creado; publicar desde el editor actualiza el motor. Para cambios estáticos, guardar el borrador y recargar la página. Git conserva archivos versionados, no el estado del navegador.
