"use strict";

function enableMiddlePan(viewport) {
  let pan = null;
  function finish() {
    if (!pan) return;
    const pointer = pan.pointer;
    pan = null;
    viewport.classList.remove("panning-canvas");
    if (viewport.hasPointerCapture(pointer)) viewport.releasePointerCapture(pointer);
  }
  viewport.addEventListener("pointerdown", event => {
    if (event.button !== 1 || event.buttons !== 4) return;
    const bounds = viewport.getBoundingClientRect();
    if (event.clientX >= bounds.left + viewport.clientWidth || event.clientY >= bounds.top + viewport.clientHeight) return;
    event.preventDefault();
    pan = {pointer:event.pointerId, x:event.clientX, y:event.clientY,
      left:viewport.scrollLeft, top:viewport.scrollTop};
    viewport.setPointerCapture(event.pointerId);
    viewport.classList.add("panning-canvas");
    viewport.focus({preventScroll:true});
  });
  // Suppress the browser's middle-button autoscroll and auxiliary click.
  viewport.addEventListener("mousedown", event => { if(event.button === 1) event.preventDefault(); });
  viewport.addEventListener("auxclick", event => { if(event.button === 1) event.preventDefault(); });
  viewport.addEventListener("pointermove", event => {
    if (!pan || event.pointerId !== pan.pointer) return;
    if (!(event.buttons & 4)) { finish(); return; }
    event.preventDefault();
    viewport.scrollLeft = pan.left - (event.clientX - pan.x);
    viewport.scrollTop = pan.top - (event.clientY - pan.y);
  });
  for (const name of ["pointerup", "pointercancel", "lostpointercapture"]) {
    viewport.addEventListener(name, event => { if(pan && event.pointerId === pan.pointer) finish(); });
  }
  viewport.addEventListener("keydown", event => { if(event.key === "Escape") finish(); });
  window.addEventListener("blur", finish);
}

function enableCanvasSelection(viewport, onSelect) {
  let selection = null;
  function finish() {
    if (!selection) return;
    const {pointer, box} = selection;
    selection = null;
    box.remove();
    viewport.classList.remove("selecting-nodes");
    if (viewport.hasPointerCapture(pointer)) viewport.releasePointerCapture(pointer);
  }
  viewport.addEventListener("pointerdown", event => {
    if (event.button !== 0 || busy || !draft || event.target.closest(".graph-node,.node-eye,button,input,select,textarea")) return;
    const bounds = viewport.getBoundingClientRect();
    // Ignore native scrollbars.
    if (event.clientX >= bounds.left + viewport.clientWidth || event.clientY >= bounds.top + viewport.clientHeight) return;
    event.preventDefault();
    const box = document.createElement("div");
    box.className = "node-selection-box";
    box.setAttribute("aria-hidden", "true");
    viewport.parentElement.append(box);
    selection = {pointer:event.pointerId, x:event.clientX, y:event.clientY, bounds, box,
      cards:[...viewport.querySelectorAll(".graph-node")].map(card => ({id:card.dataset.node, rect:card.getBoundingClientRect()}))};
    viewport.setPointerCapture(event.pointerId);
    viewport.classList.add("selecting-nodes");
    viewport.focus({preventScroll:true});
    onSelect([]);
  });
  viewport.addEventListener("pointermove", event => {
    if (!selection || event.pointerId !== selection.pointer) return;
    if (!(event.buttons & 1)) { finish(); return; }
    event.preventDefault();
    const {bounds, box, cards, x, y} = selection;
    const endX = Math.max(bounds.left, Math.min(bounds.left+viewport.clientWidth,event.clientX));
    const endY = Math.max(bounds.top, Math.min(bounds.top+viewport.clientHeight,event.clientY));
    const left=Math.min(x,endX), top=Math.min(y,endY), right=Math.max(x,endX), bottom=Math.max(y,endY);
    Object.assign(box.style,{left:(left-bounds.left)+"px",top:(top-bounds.top)+"px",width:(right-left)+"px",height:(bottom-top)+"px"});
    onSelect(cards.filter(({rect}) => rect.left < right && rect.right > left && rect.top < bottom && rect.bottom > top).map(card=>card.id));
  });
  for (const name of ["pointerup", "pointercancel", "lostpointercapture"]) {
    viewport.addEventListener(name, event => { if (selection && event.pointerId === selection.pointer) finish(); });
  }
  viewport.addEventListener("keydown", event => { if(event.key === "Escape") finish(); });
  window.addEventListener("blur",finish);
}

enableMiddlePan(document.getElementById("graph-viewport"));
enableCanvasSelection(document.getElementById("graph-viewport"), ids => {
  movingNodes.clear();
  ids.forEach(id=>movingNodes.add(id));
  draw();
});
