"use strict";
const demoKey = "orienta-demo-tree-v1";
const demoCatalogKey = "orienta-demo-diagrams-v1";
let demoSession = null;
async function demoCatalog() {
  const stored=localStorage.getItem(demoCatalogKey);
  if(stored)return JSON.parse(stored);
  const legacy=localStorage.getItem(demoKey);
  if(legacy){const item=JSON.parse(legacy);return {active:"diagrama-1",revision:item.revision,diagrams:{"diagrama-1":{name:"Diagrama 1",knowledge:item.knowledge}}};}
  const response=await fetch("diagrams.json");
  if(!response.ok)throw new Error("No se pudo cargar la demo.");
  return {...await response.json(),revision:"initial"};
}
function demoSnapshot(catalog) {
  return {revision:catalog.revision,diagram_id:catalog.active,
    knowledge:catalog.diagrams[catalog.active].knowledge,
    diagrams:Object.entries(catalog.diagrams).map(([id,item])=>({id,name:item.name}))};
}
async function demoTree() {
  return demoSnapshot(await demoCatalog());
}
function validateDemo(tree) {
  if (!tree.nodes[tree.bot.start_node]) throw new Error("Falta el nodo inicial.");
  for (const node of Object.values(tree.nodes)) {
    if (!node.content.length) throw new Error("Cada nodo necesita contenido.");
    const ids = new Set();
    for (const option of node.options) {
      if (!option.id || !option.label || ids.has(option.id)) throw new Error("Revisa los IDs y textos de las opciones.");
      ids.add(option.id);
      if (option.next ? !tree.nodes[option.next] : !["back","restart"].includes(option.action))
        throw new Error("Hay una opción sin destino válido.");
    }
  }
}
async function demoAdmin(path, method, body) {
  const catalog=await demoCatalog();
  if(path==="/tree"&&method==="GET")return demoSnapshot(catalog);
  if(catalog.revision!==body.revision)throw new Error("La demo cambió en otra pestaña. Recarga antes de guardar.");
  if(path==="/tree"&&method==="PUT"){
    validateDemo(body.knowledge);catalog.diagrams[catalog.active].knowledge=body.knowledge;
  }else if(path==="/diagrams"&&method==="POST"){
    const {action,diagram_id:id}=body, name=body.name?.trim();
    if(["create","rename"].includes(action)){
      if(!name||name.length>80)throw new Error("Escribe un nombre de hasta 80 caracteres.");
      if(Object.entries(catalog.diagrams).some(([key,item])=>key!==id&&item.name.toLowerCase()===name.toLowerCase()))throw new Error("Ya existe un diagrama con ese nombre.");
    }
    if(action==="create"){
      const knowledge=body.knowledge || {version:1,bot:{name,start_node:"inicio"},nodes:{inicio:{type:"question",content:[{type:"text",text:"¡Hola! Elige una opción para comenzar."}],options:[]}}};
      validateDemo(knowledge);const key=crypto.randomUUID();catalog.diagrams[key]={name,knowledge};catalog.active=key;
    }else{
      if(!catalog.diagrams[id])throw new Error("El diagrama ya no existe.");
      if(action==="switch")catalog.active=id;
      else if(action==="rename")catalog.diagrams[id].name=name;
      else if(action==="delete"){
        if(Object.keys(catalog.diagrams).length===1)throw new Error("Conserva al menos un diagrama.");
        delete catalog.diagrams[id];if(catalog.active===id)catalog.active=Object.keys(catalog.diagrams)[0];
      }else throw new Error("Operación no disponible.");
    }
  }else throw new Error("Operación no disponible en esta demo.");
  catalog.revision=crypto.randomUUID();localStorage.setItem(demoCatalogKey,JSON.stringify(catalog));
  return structuredClone(demoSnapshot(catalog));
}
async function demoChat(path, body) {
  if (path === "/api/chat/start") {
    const {knowledge} = await demoTree();
    demoSession = {knowledge, current:knowledge.bot.start_node, history:[], revision:0, id:crypto.randomUUID()};
  } else {
    if (!demoSession || body.session_id !== demoSession.id || body.revision !== demoSession.revision)
      throw new Error("Inicia una nueva conversación.");
    const s = demoSession;
    if (path === "/api/chat/back") {
      if (s.history.length) s.current = s.history.pop();
    } else if (path === "/api/chat/select") {
      const option = s.knowledge.nodes[s.current].options.find(o=>o.id === body.option_id);
      if (!option) throw new Error("Opción no disponible.");
      if (option.next) { s.history.push(s.current); s.current = option.next; }
      else if (option.action === "back" && s.history.length) s.current = s.history.pop();
      else if (option.action === "restart") { s.current = s.knowledge.bot.start_node; s.history = []; }
    } else throw new Error("Operación no disponible.");
    s.revision++;
  }
  const s = demoSession;
  return structuredClone({session_id:s.id,bot_name:s.knowledge.bot.name,node_id:s.current,
    node:s.knowledge.nodes[s.current],history:s.history,revision:s.revision});
}
function resetDemo() {
  if (!confirm("¿Restablecer el árbol de demostración? Se perderán las ediciones de esta demo en este navegador.")) return;
  localStorage.removeItem(demoKey);
  localStorage.removeItem(demoCatalogKey);
  Object.keys(localStorage).filter(key=>key.startsWith("orienta-demo-positions:")).forEach(key=>localStorage.removeItem(key));
  localStorage.removeItem("orienta-demo-positions");
  location.reload();
}
