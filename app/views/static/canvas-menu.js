"use strict";
(() => {
  const viewport = document.getElementById("graph-viewport");
  const menu = document.getElementById("canvas-menu");
  const items = [...menu.querySelectorAll("button")];
  function close(restoreFocus = false) {
    if (menu.hidden) return;
    menu.hidden = true;
    if (restoreFocus) viewport.focus({preventScroll:true});
  }
  viewport.addEventListener("contextmenu", event => {
    if (event.target.closest(".graph-node,.node-eye,button,input,select,textarea")) return;
    const bounds = viewport.getBoundingClientRect();
    const keyboard = event.clientX === 0 && event.clientY === 0;
    if (!keyboard && (event.clientX >= bounds.left + viewport.clientWidth || event.clientY >= bounds.top + viewport.clientHeight)) return;
    event.preventDefault();
    if (busy || !draft) return;
    menu.hidden = false;
    const x = keyboard ? bounds.left + 20 : event.clientX;
    const y = keyboard ? bounds.top + 20 : event.clientY;
    menu.style.left = Math.max(8, Math.min(x, innerWidth - menu.offsetWidth - 8)) + "px";
    menu.style.top = Math.max(8, Math.min(y, innerHeight - menu.offsetHeight - 8)) + "px";
    items.find(item => !item.disabled)?.focus({preventScroll:true});
  });
  // Close before the existing action runs, preserving the current node selection.
  menu.addEventListener("click", event => {
    if (event.target.closest("button")) close(true);
  }, true);
  menu.addEventListener("contextmenu", event => event.preventDefault());
  menu.addEventListener("keydown", event => {
    if (event.key === "Escape" || event.key === "Tab") {
      close(true);
      if (event.key === "Escape") event.preventDefault();
      return;
    }
    if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const enabled = items.filter(item => !item.disabled);
    const index = enabled.indexOf(document.activeElement);
    const next = event.key === "Home" ? 0 : event.key === "End" ? enabled.length - 1 :
      (index + (event.key === "ArrowDown" ? 1 : -1) + enabled.length) % enabled.length;
    enabled[next]?.focus();
  });
  document.addEventListener("pointerdown", event => { if (!menu.contains(event.target)) close(); });
  document.addEventListener("focusin", event => { if (!menu.contains(event.target)) close(); });
  document.addEventListener("scroll", () => close(), true);
  window.addEventListener("resize", () => close());
  window.addEventListener("blur", () => close());
})();
