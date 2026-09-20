"use strict";

function enableCanvasPan(viewport) {
  let pan = null;
  const isNode = target => target.closest(".graph-node,.node-eye,button,input,select,textarea");
  function finish() {
    if (!pan) return;
    const pointer = pan.pointer;
    pan = null;
    viewport.classList.remove("panning-canvas");
    if (viewport.hasPointerCapture(pointer)) viewport.releasePointerCapture(pointer);
  }
  viewport.addEventListener("pointerdown", event => {
    if (event.button !== 0 || isNode(event.target)) return;
    event.preventDefault();
    pan = {pointer:event.pointerId, x:event.clientX, y:event.clientY,
           left:viewport.scrollLeft, top:viewport.scrollTop};
    viewport.setPointerCapture(event.pointerId);
    viewport.classList.add("panning-canvas");
    viewport.focus({preventScroll:true});
  });
  viewport.addEventListener("pointermove", event => {
    if (!pan || event.pointerId !== pan.pointer) return;
    if (!(event.buttons & 1)) { finish(); return; }
    event.preventDefault();
    // Scroll is in screen pixels, independent of the graph's zoom level.
    viewport.scrollLeft = pan.left - (event.clientX - pan.x);
    viewport.scrollTop = pan.top - (event.clientY - pan.y);
  });
  for (const name of ["pointerup", "pointercancel", "lostpointercapture"]) {
    viewport.addEventListener(name, event => {
      if (pan && event.pointerId === pan.pointer) finish();
    });
  }
}

if (typeof document !== "undefined") enableCanvasPan(document.getElementById("graph-viewport"));
if (typeof module !== "undefined") module.exports = enableCanvasPan;
