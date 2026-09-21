# Manual de uso

Estado documentado: 21 de septiembre de 2026.

## Chatbot

Abrir <http://localhost:8000/>, leer la respuesta y elegir un botón. **↶ Volver**, abajo a la derecha, retrocede un paso por el recorrido realmente visitado. Se puede repetir hasta agotar el historial, incluso desde respuestas sin opciones; entonces queda desactivado.

Si se configuró **Menú principal**, esa opción vuelve al inicio y vacía el historial. Los mensajes previos siguen visibles: el registro visual y el historial de navegación son distintos. Se conservan hasta 100 mensajes en pantalla. Recargar inicia otra conversación. Si la sesión caduca, se reinicia el servidor o se publica un árbol, puede ser necesario iniciar una nueva conversación.

## Controles del editor

Abrir <http://localhost:8000/admin>. El árbol aparece en el lienzo y la configuración del nodo elegido en el panel lateral.

| Control | Resultado |
| --- | --- |
| Clic izquierdo en un nodo | Selecciona el nodo y abre su configuración |
| Clic izquierdo y arrastrar sobre el fondo | Dibuja un recuadro; selecciona las tarjetas que toca |
| Arrastrar una tarjeta seleccionada | Mueve el nodo o el grupo seleccionado |
| Ctrl/Cmd + clic o Shift + clic | Añade o quita un nodo de la selección |
| Seleccionar todos / Ctrl/Cmd + A dentro del lienzo | Selecciona los nodos visibles |
| Escape o clic en el fondo | Limpia la selección de movimiento |
| Mantener presionada la rueda y arrastrar | Desplaza el lienzo en ambas direcciones |
| Barras de desplazamiento | Permiten explorar el lienzo |
| − / + | Zoom entre 25 % y 200 %, en pasos de 25 % |
| Centrar selección | Centra la vista en el nodo abierto en el panel |
| Buscar nodo | Resalta coincidencias en ID o contenido |
| Ojo | Oculta/muestra descendientes; tachado indica rama plegada |
| Ordenar nodos | Distribuye ramas en abanico y mantiene la posición de inicio |

El zoom afecta solo a tarjetas y conexiones. El lienzo conserva un margen amplio. Las etiquetas de las flechas se centran y siguen su inclinación; los nombres largos se abrevian.

El abanico reserva espacio por subárbol. Los nodos compartidos aparecen una sola vez, asignados al primer padre encontrado para calcular su posición. Se conservan todas sus conexiones.

Plegar no elimina datos. Un descendiente compartido también puede ocultarse aunque otra rama lo use. Inicio permanece disponible. Las ramas plegadas dentro de otra conservan temporalmente su estado.

## Crear y editar

- **+ Nodo** crea una respuesta independiente en un hueco de la vista actual, considerando zoom, tarjetas, flechas, etiquetas y controles. Si no cabe, pide desplazarse o alejar el zoom. Se marca **SIN CONEXIÓN** hasta conectarlo.
- **Nueva opción + nodo** crea una rama y su destino. Editar el texto del botón y abrir **Configurar nodo destino** para escribir la respuesta. Este flujo usa la distribución del árbol; la búsqueda de hueco visible corresponde a **+ Nodo**.
- **Conectar existente / acción** añade una opción cuyo destino puede ser un nodo, **Volver al nodo anterior** o **Menú principal**.

Los IDs nuevos son automáticos. Cada nodo tiene tipo (pregunta/información), bloques de contenido y opciones. Cambiar de nodo conserva las ediciones del borrador. Para eliminarlo, quitar primero las opciones que lo referencian. Inicio no se puede eliminar. Eliminar un nodo no borra sus archivos físicos.

## Multimedia

Se admiten texto plano, enlaces HTTP/HTTPS sin credenciales, imágenes y documentos existentes. El texto no interpreta HTML.

Colocar recursos en `storage/images/` o `storage/documents/`. Escribir referencias como `images/guia.png` o `documents/requisitos.pdf`, sin `storage/`. El panel todavía no permite subir archivos.

Imágenes: PNG, JPG/JPEG, GIF y WEBP. Documentos: PDF, TXT, DOCX, XLSX y PPTX. TXT se abre en un diálogo; PDF usa el visor del navegador; Office ofrece descarga. Solo se sirven recursos referenciados por el árbol publicado.

## Guardado

**Guardar árbol** valida y publica el borrador completo. Ante error o conflicto conserva el borrador. **Recargar** recupera la versión publicada y pide confirmación si existen cambios sin guardar.

| Información | Persistencia |
| --- | --- |
| Contenido y conexiones publicados | `data/knowledge.yaml` |
| Multimedia | `storage/` |
| Borrador | Memoria de la pestaña; se pierde al cerrarla |
| Posiciones de nodos | Almacenamiento local del navegador |
| Zoom, selección y plegado | Estado temporal de la página |
| Historial del chat | Memoria del servidor |
| Checkpoints | Archivos versionados en Git |

Guardar el árbol antes de crear un checkpoint si se desea incluir el contenido editado. Git no incluye borradores, sesiones ni posiciones del navegador.

## Problemas habituales

- Cambio visual no visible: guardar el borrador y recargar la página.
- Nodo fuera de vista: buscar, desplegar su rama o usar Centrar selección.
- No hay hueco para crear: desplazarse a una zona vacía o reducir zoom.
- Error al publicar: revisar campos obligatorios, referencias y archivos. Un conflicto requiere reconciliar el borrador con la versión guardada.
- Edición manual de YAML no visible: reiniciar el servidor; el panel sí actualiza el motor al publicar.
- Localhost no responde: comprobar que Uvicorn sigue ejecutándose en Ubuntu en el puerto 8000.
