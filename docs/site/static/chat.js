"use strict";
const messages = document.querySelector("#messages");
const options = document.querySelector("#options");
const status = document.querySelector("#status");
const errorBox = document.querySelector("#error-box");
const recover = document.querySelector("#recover");
const caption = document.querySelector("#choice-caption");
const backButton = document.querySelector("#go-back");
let state = null;
let busy = false;

function setBusy(value) {
  busy = value;
  options.querySelectorAll("button").forEach(button => { button.disabled = value; });
  recover.disabled = value;
  backButton.disabled = value || !state?.history.length;
  status.textContent = value ? "Un momento…" : "";
  options.setAttribute("aria-busy", String(value));
}

async function request(path, body) { return demoChat(path, body); }

function fileUrl(reference) {
  return "files/" + reference.split("/").map(encodeURIComponent).join("/");
}

function link(label, url) {
  const element = document.createElement("a");
  element.textContent = label;
  element.href = url;
  element.target = "_blank";
  element.rel = "noopener noreferrer";
  return element;
}

async function previewText(item, trigger) {
  const dialog = document.createElement("dialog");
  dialog.className = "document-preview";
  dialog.setAttribute("aria-label", item.label);
  const title = document.createElement("h2");
  title.textContent = item.label;
  const close = document.createElement("button");
  close.textContent = "Cerrar";
  close.type = "button";
  close.addEventListener("click", () => dialog.close());
  const body = document.createElement("pre");
  body.textContent = "Cargando documento…";
  body.setAttribute("aria-live", "polite");
  dialog.append(title, close, body);
  document.body.append(dialog);
  dialog.showModal();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  dialog.addEventListener("close", () => {
    controller.abort();
    dialog.remove();
    trigger.focus();
  }, { once: true });
  try {
    const response = await fetch(fileUrl(item.file), {signal: controller.signal, cache: "no-store"});
    if (!response.ok) throw new Error("Archivo no disponible");
    body.textContent = await response.text();
  } catch (error) {
    body.textContent = "No se pudo abrir el documento. Comprueba la conexión o vuelve a intentarlo.";
  } finally { clearTimeout(timeout); }
}

function renderContent(item) {
  if (item.type === "text") {
    const paragraph = document.createElement("p");
    paragraph.textContent = item.text;
    return paragraph;
  }
  if (item.type === "link") {
    const external = link(item.label + " ↗", item.url);
    external.className = "external-link";
    return external;
  }
  if (item.type === "image") {
    const figure = document.createElement("figure");
    figure.className = "content-image";
    const image = document.createElement("img");
    image.alt = item.alt;
    image.src = fileUrl(item.file);
    const open = link("Abrir imagen ↗", image.src);
    image.addEventListener("error", () => {
      image.hidden = true;
      open.textContent = "Imagen no disponible";
      open.removeAttribute("href");
    }, { once: true });
    figure.append(image, open);
    return figure;
  }
  const card = document.createElement("section");
  card.className = "document-card";
  const title = document.createElement("strong");
  title.textContent = item.label;
  const details = document.createElement("span");
  details.textContent = item.file.split("/").pop();
  const actions = document.createElement("div");
  const url = fileUrl(item.file);
  if (/\.txt$/i.test(item.file)) {
    const preview = document.createElement("button");
    preview.type = "button";
    preview.textContent = "Ver documento";
    preview.addEventListener("click", () => previewText(item, preview));
    actions.append(preview);
  } else if (/\.pdf$/i.test(item.file)) actions.append(link("Ver documento ↗", url));
  const download = link("Descargar ↓", url + "?download=true");
  download.removeAttribute("target");
  download.setAttribute("download", "");
  actions.append(download);
  card.append(title, details, actions);
  return card;
}

function addMessage(content, user = false) {
  const article = document.createElement("article");
  article.className = user ? "message user" : "message";
  const label = document.createElement("p");
  label.className = "message-label";
  label.textContent = user ? "Tú" : state.bot_name;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  content.forEach(item => bubble.append(renderContent(item)));
  article.append(label, bubble);
  messages.append(article);
  // Bound the visible transcript separately from the engine's navigation history.
  while (messages.children.length > 100) messages.firstElementChild.remove();
}

function render() {
  document.querySelector("#bot-name").textContent = state.bot_name;
  document.title = state.bot_name;
  addMessage(state.node.content);
  options.replaceChildren();
  caption.textContent = state.node.options.length ? "Elige una opción para continuar" : "Has llegado al final de este recorrido.";
  state.node.options.forEach(option => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = option.label;
    if (option.action) button.className = "navigation";
    button.addEventListener("click", () => select(option));
    options.append(button);
  });
  const body = document.querySelector("#chat-body");
  body.scrollTop = body.scrollHeight;
}

function showError(error) {
  // A lost response may have advanced the server; never silently resend a selection.
  state = null;
  options.replaceChildren();
  caption.textContent = "Inicia otra conversación para continuar.";
  document.querySelector("#error").textContent = error.status === 404
    ? "La conversación ha caducado o el servidor se reinició."
    : error.status === 409
      ? "La conversación cambió. Inicia una nueva para continuar."
      : "No pudimos conectar con el asistente. Comprueba la conexión e inicia una nueva conversación.";
  errorBox.hidden = false;
  recover.focus();
}

async function start() {
  if (busy) return;
  setBusy(true);
  errorBox.hidden = true;
  try {
    state = await request("/api/chat/start");
    messages.replaceChildren();
    render();
  } catch (error) { showError(error); }
  finally { setBusy(false); if (!errorBox.hidden) recover.focus(); }
}

async function select(option) {
  if (busy || !state) return;
  setBusy(true);
  try {
    const next = await request("/api/chat/select", {
      session_id: state.session_id, option_id: option.id, revision: state.revision,
    });
    addMessage([{type: "text", text: option.label}], true);
    state = next;
    render();
  } catch (error) { showError(error); }
  finally {
    setBusy(false);
    if (!errorBox.hidden) recover.focus();
    else options.querySelector("button")?.focus({ preventScroll: true });
  }
}

backButton.addEventListener("click", async () => {
  if (busy || !state?.history.length) return;
  setBusy(true);
  try {
    const previous = await request("/api/chat/back", {
      session_id: state.session_id, revision: state.revision,
    });
    addMessage([{type:"text",text:"Volver al paso anterior"}], true);
    state = previous;
    render();
  } catch (error) { showError(error); }
  finally {
    setBusy(false);
    if (!errorBox.hidden) recover.focus();
    else if (!backButton.disabled) backButton.focus({preventScroll:true});
    else options.querySelector("button")?.focus({preventScroll:true});
  }
});
recover.addEventListener("click", start);
start();
