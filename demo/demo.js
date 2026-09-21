"use strict";
const demoKey = "orienta-demo-tree-v1";
let demoSession = null;
async function demoTree() {
  const stored = localStorage.getItem(demoKey);
  if (stored) return JSON.parse(stored);
  const response = await fetch("knowledge.json");
  if (!response.ok) throw new Error("No se pudo cargar la demo.");
  return {revision:"initial", knowledge:await response.json()};
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
  const saved = await demoTree();
  if (path === "/tree" && method === "GET") return saved;
  if (path !== "/tree" || method !== "PUT") throw new Error("Operación no disponible en esta demo.");
  if (saved.revision !== body.revision) throw new Error("La demo cambió en otra pestaña. Recarga antes de guardar.");
  validateDemo(body.knowledge);
  const next = {revision:crypto.randomUUID(), knowledge:body.knowledge};
  localStorage.setItem(demoKey, JSON.stringify(next));
  return structuredClone(next);
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
  localStorage.removeItem("orienta-demo-positions");
  location.reload();
}
