"use strict";
const $ = id => document.getElementById(id);
let snapshot, draft, selected = null, dirty = false, busy = false;
const SVG = "http://www.w3.org/2000/svg";
let graphZoom = 1, graphWidth = 650, graphHeight = 360;
const MIN_ZOOM = 0.25, MAX_ZOOM = 2;
const movingNodes = new Set();
const manualPositions = new Map();
const collapsedNodes = new Set();
function hiddenDescendants() {
  const hidden = new Set();
  for (const parent of collapsedNodes) {
    const visited = new Set([parent]);
    const pending = (draft.nodes[parent]?.options || []).map(option => option.next).filter(Boolean);
    while (pending.length) {
      const id = pending.pop();
      if (visited.has(id) || id === draft.bot.start_node || !draft.nodes[id]) continue;
      visited.add(id); hidden.add(id);
      draft.nodes[id].options.forEach(option => { if(option.next) pending.push(option.next); });
    }
  }
  return hidden;
}
function toggleBranch(id) {
  if (busy) return;
  capture();
  if (collapsedNodes.has(id)) collapsedNodes.delete(id); else collapsedNodes.add(id);
  if (hiddenDescendants().has(selected)) edit(id); else draw();
  const eye = [...$("graph-nodes").querySelectorAll(".node-eye")].find(button => button.dataset.parent === id);
  eye?.focus({preventScroll:true});
}
let renderedPositions = new Map(), dragState = null, suppressGraphClick = false;
try {
  const saved = JSON.parse(localStorage.getItem("orienta-node-positions") || "{}");
  Object.entries(saved).forEach(([id, point]) => {
    if (Number.isFinite(point.x) && Number.isFinite(point.y) && point.x >= 0 && point.y >= 0)
      manualPositions.set(id, point);
  });
} catch { /* Layout storage is optional; the conversation is unaffected. */ }
function storePositions() {
  try { localStorage.setItem("orienta-node-positions", JSON.stringify(Object.fromEntries(manualPositions))); }
  catch { /* Moving nodes also works when browser storage is unavailable. */ }
}
function applyGraphZoom() {
  $("graph-canvas").style.transform = `scale(${graphZoom})`;
  $("graph-space").style.width = Math.ceil(graphWidth * graphZoom) + "px";
  $("graph-space").style.height = Math.ceil(graphHeight * graphZoom) + "px";
  $("zoom-level").textContent = Math.round(graphZoom * 100) + "%";
  $("zoom-out").disabled = graphZoom <= MIN_ZOOM;
  $("zoom-in").disabled = graphZoom >= MAX_ZOOM;
}
function changeGraphZoom(step) {
  const viewport = $("graph-viewport");
  const x = (viewport.scrollLeft + viewport.clientWidth / 2) / graphZoom;
  const y = (viewport.scrollTop + viewport.clientHeight / 2) / graphZoom;
  graphZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, Math.round((graphZoom + step) * 100) / 100));
  applyGraphZoom();
  viewport.scrollLeft = x * graphZoom - viewport.clientWidth / 2;
  viewport.scrollTop = y * graphZoom - viewport.clientHeight / 2;
}
function notice(message, error = false) { $("notice").textContent = message; $("notice").className = error ? "error" : ""; }
async function api(path, method = "GET", body) {
  const response = await fetch("/api/admin" + path, {method, headers:{"Content-Type":"application/json", "X-Admin-Request":"local-panel"}, body:body ? JSON.stringify(body) : undefined});
  const data = await response.json();
  if (!response.ok) throw new Error(Array.isArray(data.detail) ? data.detail.map(e => e.loc.join(" → ") + ": " + e.msg).join("\n") : data.detail || "No se pudo completar la operación.");
  return data;
}
function changed() { dirty = true; $("draft-status").textContent = "● Cambios sin guardar"; $("draft-status").className = "pending"; draw(); }
function capture() {
  if (!selected || !draft.nodes[selected]) return;
  draft.nodes[selected] = {type:$("node-type").value,content:[...$("contents").children].map(row => row.read()),options:[...$("options-editor").children].map(row => row.read())};
}
function unique(prefix, values) { let index = 1; while(values.includes(prefix + index)) index++; return prefix + index; }
function createNode() {
  const id = unique("nodo_",Object.keys(draft.nodes));
  draft.nodes[id] = {type:"information",content:[{type:"text",text:"Nueva respuesta"}],options:[]};
  return id;
}
function svg(tag, attrs) { const element = document.createElementNS(SVG,tag); Object.entries(attrs).forEach(([k,v]) => element.setAttribute(k,v)); return element; }
function draw() {
  if (!draft) return;
  const ids = Object.keys(draft.nodes), levels = new Map(), queue = [draft.bot.start_node];
  levels.set(draft.bot.start_node,0);
  for(let index=0;index<queue.length;index++) {
    const id=queue[index];
    (draft.nodes[id]?.options || []).forEach(option => {
      if(option.next && draft.nodes[option.next] && !levels.has(option.next)) {levels.set(option.next,levels.get(id)+1);queue.push(option.next);}
    });
  }
  const unreachable = ids.filter(id => !levels.has(id));
  const bottom = new Map(), positions = new Map();
  ids.filter(id => levels.has(id)).sort((a,b) => levels.get(a)-levels.get(b)).forEach(id => {
    const level=levels.get(id), row=bottom.get(level)||0; bottom.set(level,row+1); positions.set(id,{x:35+level*285,y:35+row*185});
  });
  const disconnectedY=35+Math.max(1,...bottom.values())*185;
  unreachable.forEach((id,index) => positions.set(id,{x:35+(index%3)*285,y:disconnectedY+Math.floor(index/3)*185}));
  ids.forEach(id => { if (manualPositions.has(id)) positions.set(id, manualPositions.get(id)); });
  const hidden = hiddenDescendants();
  const visibleIds = ids.filter(id => !hidden.has(id));
  for (const id of movingNodes) if (!draft.nodes[id] || hidden.has(id)) movingNodes.delete(id);
  renderedPositions = new Map([...positions].filter(([id]) => !hidden.has(id)));
  const width=Math.max(650,...[...positions.values()].map(p=>p.x+235)), height=Math.max(360,...[...positions.values()].map(p=>p.y+155));
  $("graph-canvas").style.width=width+"px"; $("graph-canvas").style.height=height+"px";
  graphWidth=width; graphHeight=height; applyGraphZoom();
  const lines=$("graph-lines"); lines.replaceChildren(); lines.setAttribute("width",width); lines.setAttribute("height",height);
  const defs=svg("defs",{}), marker=svg("marker",{id:"arrow",viewBox:"0 0 10 10",refX:9,refY:5,markerWidth:6,markerHeight:6,orient:"auto-start-reverse"}); marker.append(svg("path",{d:"M 0 0 L 10 5 L 0 10 z",fill:"#81976f"})); defs.append(marker); lines.append(defs);
  let edges=0;
  ids.forEach(id => draft.nodes[id].options.forEach((option,index) => {
    if(!positions.has(option.next) || hidden.has(id) || hidden.has(option.next) || collapsedNodes.has(id)) return;
    edges++; const a=positions.get(id), b=positions.get(option.next), offset=(index%5)*7;
    const x1=a.x+190,y1=a.y+22+index*72/Math.max(1,draft.nodes[id].options.length-1),x2=b.x,y2=b.y+48;
    let d;
    if(b.x>x1) d=`M ${x1} ${y1} C ${x1+55} ${y1}, ${x2-55} ${y2}, ${x2} ${y2}`;
    else { const arc=Math.max(8,Math.min(a.y,b.y)-18-offset); d=`M ${x1} ${y1} C ${x1+40} ${y1}, ${x1+40} ${arc}, ${x1} ${arc} L ${x2-15} ${arc} Q ${x2-28} ${arc}, ${x2-28} ${y2} L ${x2} ${y2}`; }
    const path=svg("path",{d,class:"graph-edge"+(id===selected || option.next===selected?" active":""),"marker-end":"url(#arrow)"});
    const title=svg("title",{}); title.textContent=option.label; path.append(title); lines.append(path);
    const label=svg("text",{x:x1+5,y:y1-8,class:"edge-label"});label.textContent=option.label.length>14?option.label.slice(0,12)+"…":option.label; lines.append(label);
  }));
  $("graph-nodes").replaceChildren();
  const query=$("search").value.toLowerCase();
  visibleIds.forEach(id => {
    const node=draft.nodes[id], point=positions.get(id), button=document.createElement("button"); button.type="button";
    button.className="graph-node"+(selected===id?" selected":"")+(movingNodes.has(id)?" multi-selected":"")+((id+JSON.stringify(node.content)).toLowerCase().includes(query)?"":" dimmed");
    button.dataset.node=id; button.style.left=point.x+"px";button.style.top=point.y+"px";button.setAttribute("aria-pressed",String(selected===id));
    const title=document.createElement("strong");title.textContent=id;
    const preview=document.createElement("span");preview.className="preview";preview.textContent=node.content.find(c=>c.type==="text")?.text || "Contenido multimedia";
    const meta=document.createElement("span");meta.className="meta";meta.textContent=(id===draft.bot.start_node?"INICIO · ":unreachable.includes(id)?"SIN CONEXIÓN · ":"")+node.options.length+" opciones";
    button.append(title,preview,meta);button.onclick=event=>{if(!busy && event.detail===0){capture();movingNodes.clear();movingNodes.add(id);edit(id);}};$("graph-nodes").append(button);
    const eye=document.createElement("button"); eye.type="button"; eye.className="node-eye";
    eye.dataset.parent=id; eye.style.left=(point.x+153)+"px"; eye.style.top=(point.y+7)+"px";
    const collapsed=collapsedNodes.has(id), hasChildren=node.options.some(option=>option.next && option.next!==id);
    eye.disabled=!hasChildren;
    eye.setAttribute("aria-label",(collapsed?"Mostrar descendientes de ":"Ocultar descendientes de ")+id);
    eye.setAttribute("aria-expanded",String(!collapsed));
    eye.title=hasChildren?(collapsed?"Mostrar descendientes":"Ocultar descendientes"):"Sin nodos hijos";
    const icon=svg("svg",{viewBox:"0 0 24 24",width:20,height:20,"aria-hidden":"true",fill:"none",stroke:"currentColor","stroke-width":1.8});
    icon.append(svg("path",{d:"M2 12 Q12 0 22 12 Q12 24 2 12Z"}),svg("circle",{cx:12,cy:12,r:3}));
    if(collapsed) icon.append(svg("path",{d:"M3 3 L21 21",class:"eye-slash","stroke-width":2.5}));
    eye.append(icon);eye.onclick=()=>toggleBranch(id);$("graph-nodes").append(eye);
  });
  $("graph-count").textContent=visibleIds.length+" de "+ids.length+" nodos · "+edges+" conexiones"+(movingNodes.size?" · "+movingNodes.size+" seleccionados":"");
}
function field(parent,label,value="",multiline=false) {
  const wrapper=document.createElement("label");wrapper.textContent=label;
  const input=document.createElement(multiline?"textarea":"input");input.value=value;input.required=true;wrapper.append(input);parent.append(wrapper);return input;
}
function row(parent,title) {
  const element=document.createElement("div");element.className="row";
  const header=document.createElement("div");header.className="row-head";
  const label=document.createElement("strong");label.textContent=title;
  const remove=document.createElement("button");remove.type="button";remove.textContent="Quitar";
  remove.onclick=()=>{element.remove();capture();changed();};header.append(label,remove);element.append(header);parent.append(element);return element;
}
function contentRow(item) {
  const element=row($("contents"),{text:"Texto",link:"Enlace",image:"Imagen",document:"Documento"}[item.type]),inputs={};
  if(item.type==="text") inputs.text=field(element,"Texto",item.text,true);
  if(["link","document"].includes(item.type)) inputs.label=field(element,"Nombre visible",item.label);
  if(item.type==="link") inputs.url=field(element,"URL http:// o https://",item.url);
  if(["image","document"].includes(item.type)) inputs.file=field(element,"Ruta del archivo",item.file);
  if(item.type==="image"){inputs.alt=field(element,"Descripción de la imagen",item.alt);inputs.alt.required=false;}
  element.read=()=>Object.fromEntries([["type",item.type],...Object.entries(inputs).map(([key,input])=>[key,input.value])]);
}
function optionRow(item) {
  const element=row($("options-editor"),"Opción"),id=field(element,"ID de opción",item.id),label=field(element,"Texto del botón",item.label);id.pattern="[a-zA-Z0-9_-]+";
  const wrapper=document.createElement("label");wrapper.textContent="Destino o acción";
  const select=document.createElement("select");select.required=true;
  const choices=[["","Elige un destino"],["action:back","Volver al nodo anterior"],["action:restart","Menú principal"],...Object.keys(draft.nodes).map(key=>["node:"+key,"Nodo: "+key])];
  choices.forEach(([value,text])=>{const option=document.createElement("option");option.value=value;option.textContent=text;select.append(option);});
  select.value=item.next?"node:"+item.next:item.action?"action:"+item.action:"";wrapper.append(select);element.append(wrapper);
  const open=document.createElement("button");open.type="button";open.className="connection-open";open.textContent="Configurar nodo destino →";
  open.hidden=!select.value.startsWith("node:");select.addEventListener("change",()=>{open.hidden=!select.value.startsWith("node:");});
  open.onclick=()=>{capture();edit(select.value.slice(5));center();};element.append(open);
  element.read=()=>({id:id.value,label:label.value,...(select.value.startsWith("node:")?{next:select.value.slice(5)}:select.value?{action:select.value.slice(7)}:{})});
}
function edit(id) {
  selected=id;const node=draft.nodes[id];$("empty").hidden=true;$("editor").hidden=false;
  $("editor-title").textContent="Configurar · "+id;$("node-id").value=id;$("node-type").value=node.type;$("initial").textContent=id===draft.bot.start_node?"Inicial":"";$("delete").hidden=id===draft.bot.start_node;
  $("contents").replaceChildren();$("options-editor").replaceChildren();node.content.forEach(contentRow);node.options.forEach(optionRow);draw();
}
function center(){const node=[...$("graph-nodes").children].find(node=>node.dataset.node===selected);if(node){const viewport=$("graph-viewport");viewport.scrollLeft=(node.offsetLeft+node.offsetWidth/2)*graphZoom-viewport.clientWidth/2;viewport.scrollTop=(node.offsetTop+node.offsetHeight/2)*graphZoom-viewport.clientHeight/2;}}
async function load(){if(busy || (dirty&&!confirm("¿Descartar los cambios sin guardar y recargar?")))return;try{snapshot=await api("/tree");draft=structuredClone(snapshot.knowledge);dirty=false;$("draft-status").textContent="Guardado";$("draft-status").className="";edit(draft.bot.start_node);center();notice("Selecciona un nodo. Los cambios se publican al guardar el árbol.");}catch(error){notice(error.message,true);}}
$("editor").addEventListener("input",()=>{capture();changed();});$("editor").addEventListener("change",()=>{capture();changed();});$("editor").onsubmit=event=>event.preventDefault();
$("search").oninput=draw;$("locate").onclick=center;$("reload").onclick=load;
$("zoom-out").onclick=()=>changeGraphZoom(-0.25);
$("zoom-in").onclick=()=>changeGraphZoom(0.25);
$("new").onclick=()=>{if(!draft||busy)return;capture();const id=createNode();edit(id);changed();center();};
$("add-content").onclick=()=>{contentRow({type:$("content-type").value});capture();changed();};
$("add-option").onclick=()=>{capture();const id=createNode(),node=draft.nodes[selected];node.options.push({id:unique("opcion_",node.options.map(o=>o.id)),label:"Nueva opción",next:id});edit(selected);changed();notice("Rama creada. Pulsa «Configurar nodo destino» o selecciónalo en el árbol.");};
$("add-existing").onclick=()=>{capture();const node=draft.nodes[selected];node.options.push({id:unique("opcion_",node.options.map(o=>o.id)),label:"Nueva opción",action:"back"});edit(selected);changed();};
$("delete").onclick=()=>{capture();const references=Object.entries(draft.nodes).filter(([id,node])=>id!==selected&&node.options.some(o=>o.next===selected)).map(([id])=>id);if(references.length){notice("Primero quita las conexiones desde: "+references.join(", "),true);return;}if(!confirm("¿Quitar «"+selected+"» del borrador? Se aplicará al guardar."))return;delete draft.nodes[selected];edit(draft.bot.start_node);changed();};
$("save").onclick=async()=>{if(busy||!draft)return;capture();if(!$("editor").reportValidity())return;busy=true;const controls=[...document.querySelectorAll("button,input,select,textarea")].filter(el=>!el.disabled);controls.forEach(el=>el.disabled=true);try{snapshot=await api("/tree","PUT",{revision:snapshot.revision,knowledge:draft});draft=structuredClone(snapshot.knowledge);dirty=false;$("draft-status").textContent="Guardado";$("draft-status").className="";edit(selected in draft.nodes?selected:draft.bot.start_node);notice("Árbol guardado. Ya está disponible en el chatbot.");}catch(error){notice(error.message,true);}finally{busy=false;controls.forEach(el=>el.disabled=false);applyGraphZoom();}};
window.addEventListener("beforeunload",event=>{if(dirty){event.preventDefault();event.returnValue="";}});load();

const graphViewport = $("graph-viewport");
function selectAllNodes() {
  if (!draft || busy) return;
  movingNodes.clear();
  renderedPositions.forEach((point,id) => movingNodes.add(id));
  draw();
  graphViewport.focus({preventScroll:true});
}
$("select-all-nodes").onclick = selectAllNodes;
$("reset-layout").onclick = () => {
  manualPositions.clear(); movingNodes.clear(); storePositions(); draw(); center();
};
graphViewport.addEventListener("keydown", event => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "a") {
    event.preventDefault(); selectAllNodes();
  } else if (event.key === "Escape") { movingNodes.clear(); draw(); }
});
graphViewport.addEventListener("click", event => {
  if (event.target.closest(".node-eye")) return;
  if (suppressGraphClick) { event.preventDefault(); event.stopImmediatePropagation(); suppressGraphClick=false; }
}, true);
graphViewport.addEventListener("pointerdown", event => {
  if (busy || event.button !== 0) return;
  if (event.target.closest(".node-eye")) { suppressGraphClick=false; return; }
  const card = event.target.closest(".graph-node");
  if (!card) { movingNodes.clear(); draw(); return; }
  event.preventDefault();
  const id = card.dataset.node;
  suppressGraphClick=true;
  if (event.ctrlKey || event.metaKey || event.shiftKey) {
    if (movingNodes.has(id)) movingNodes.delete(id); else movingNodes.add(id);
    draw(); graphViewport.focus({preventScroll:true}); return;
  }
  if (!movingNodes.has(id)) { movingNodes.clear(); movingNodes.add(id); }
  const start = new Map([...movingNodes].map(key => [key, {...renderedPositions.get(key)}]));
  dragState={pointer:event.pointerId,id,x:event.clientX,y:event.clientY,left:graphViewport.scrollLeft,top:graphViewport.scrollTop,start,moved:false};
  graphViewport.setPointerCapture(event.pointerId);
  graphViewport.focus({preventScroll:true});
  draw();
});
graphViewport.addEventListener("pointermove", event => {
  if (!dragState || event.pointerId !== dragState.pointer) return;
  const dx=event.clientX-dragState.x, dy=event.clientY-dragState.y;
  if (!dragState.moved && Math.hypot(dx,dy)<4) return;
  dragState.moved=true;
  let x=(dx+graphViewport.scrollLeft-dragState.left)/graphZoom;
  let y=(dy+graphViewport.scrollTop-dragState.top)/graphZoom;
  x=Math.max(x, -Math.min(...[...dragState.start.values()].map(p=>p.x))+8);
  y=Math.max(y, -Math.min(...[...dragState.start.values()].map(p=>p.y))+8);
  dragState.start.forEach((point,id) => manualPositions.set(id,{x:point.x+x,y:point.y+y}));
  graphViewport.classList.add("dragging-nodes");
  draw();
});
function finishNodeDrag(event) {
  if (!dragState || event.pointerId !== dragState.pointer) return;
  const finished=dragState; dragState=null;
  if (graphViewport.hasPointerCapture(event.pointerId)) graphViewport.releasePointerCapture(event.pointerId);
  graphViewport.classList.remove("dragging-nodes");
  if (finished.moved) storePositions();
  else { capture(); edit(finished.id); }
}
graphViewport.addEventListener("pointerup",finishNodeDrag);
graphViewport.addEventListener("pointercancel",finishNodeDrag);
