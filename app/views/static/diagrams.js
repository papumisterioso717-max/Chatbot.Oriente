"use strict";
let layoutDiagram = null, dialogAction = "create", importedBackup = null;
let deleteTimer = null, deleteTarget = null;
function syncDiagrams() {
  if (!snapshot?.diagrams) return;
  const picker = $("diagram-select");
  picker.replaceChildren(...snapshot.diagrams.map(item => {
    const option=document.createElement("option");option.value=item.id;option.textContent=item.name;return option;
  }));
  picker.value=snapshot.diagram_id;picker.disabled=busy;
  $("diagram-delete").disabled=busy || snapshot.diagrams.length < 2;
  if(layoutDiagram === snapshot.diagram_id) return;
  layoutDiagram=snapshot.diagram_id;
  positionKey="orienta-node-positions:"+layoutDiagram;
  manualPositions.clear();movingNodes.clear();collapsedNodes.clear();
  try {
    const saved=localStorage.getItem(positionKey) || (layoutDiagram === "diagrama-1" ? localStorage.getItem("orienta-node-positions") : null);
    Object.entries(JSON.parse(saved || "{}")).forEach(([id,p])=>{
      if(Number.isFinite(p.x)&&Number.isFinite(p.y))manualPositions.set(id,p);
    });
  } catch { /* Layout storage is optional. */ }
}
function currentDiagramName() { return snapshot.diagrams.find(d=>d.id===snapshot.diagram_id)?.name || "Diagrama"; }
function discardAllowed() { return !dirty || confirm("Hay cambios sin guardar. ¿Descartarlos para continuar?"); }
async function changeDiagram(action, extra={}) {
  if(busy || !snapshot) return false;
  busy=true;
  const controls=[...document.querySelectorAll("button,input,select,textarea")].filter(el=>!el.disabled);
  controls.forEach(el=>el.disabled=true);
  try {
    const next=await api("/diagrams","POST",{revision:snapshot.revision,action,...extra});
    snapshot=next;draft=structuredClone(next.knowledge);dirty=false;
    $("draft-status").textContent="Guardado";$("draft-status").className="";
    syncDiagrams();edit(draft.bot.start_node);center();
    notice("Diagrama activo: "+currentDiagramName()+". El chatbot utiliza este árbol.");
    return true;
  } catch(error) { notice(error.message,true);return false; }
  finally {busy=false;controls.forEach(el=>el.disabled=false);syncDiagrams();applyGraphZoom();}
}
$("diagram-select").onchange=async event=>{
  const id=event.target.value;
  if(!discardAllowed()){event.target.value=snapshot.diagram_id;return;}
  await changeDiagram("switch",{diagram_id:id});syncDiagrams();
};
function openName(action, backup=null) {
  if(busy || !snapshot)return;
  if(action==="create"&&!discardAllowed())return;
  dialogAction=action;importedBackup=backup;
  $("diagram-dialog-title").textContent=action==="rename"?"Cambiar nombre":backup?"Importar respaldo":"Nuevo diagrama";
  $("diagram-name").value=action==="rename"?currentDiagramName():backup?.name || "";
  $("diagram-dialog-error").textContent="";
  $("diagram-dialog").showModal();$("diagram-name").focus();
}
$("diagram-new").onclick=()=>openName("create");
$("diagram-rename").onclick=()=>{if(discardAllowed())openName("rename");};
$("diagram-cancel").onclick=()=>$("diagram-dialog").close();
$("diagram-form").onsubmit=async event=>{
  event.preventDefault();const name=$("diagram-name").value.trim();
  if(!name){$("diagram-dialog-error").textContent="Escribe un nombre.";return;}
  const extra={name,...(dialogAction==="rename"?{diagram_id:snapshot.diagram_id}:{})};
  if(importedBackup)extra.knowledge=importedBackup.knowledge;
  if(await changeDiagram(dialogAction,extra)){
    if(importedBackup?.positions){
      Object.entries(importedBackup.positions).forEach(([id,p])=>{if(draft.nodes[id]&&Number.isFinite(p?.x)&&Number.isFinite(p?.y))manualPositions.set(id,p);});
      storePositions();draw();center();
    }
    $("diagram-dialog").close();
  } else $("diagram-dialog-error").textContent=$("notice").textContent;
};
$("diagram-download").onclick=()=>{
  if(busy||!draft)return;capture();
  const backup={format:"orienta-diagram",version:1,name:currentDiagramName(),knowledge:draft,positions:Object.fromEntries(manualPositions)};
  const url=URL.createObjectURL(new Blob([JSON.stringify(backup,null,2)],{type:"application/json"}));
  const link=document.createElement("a");link.href=url;link.download=currentDiagramName().replace(/[^\p{L}\p{N}_-]/gu,"_")+".json";
  link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  notice("Respaldo descargado con el contenido actual. Los archivos multimedia se respaldan por separado.");
};
$("diagram-import").onclick=()=>{if(!busy)$("diagram-file").click();};
$("diagram-file").onchange=async event=>{
  const file=event.target.files[0];event.target.value="";if(!file)return;
  try {
    if(file.size>5*1024*1024)throw new Error("El respaldo supera 5 MB.");
    const backup=JSON.parse(await file.text());
    if(backup.format!=="orienta-diagram"||backup.version!==1||!backup.knowledge)throw new Error("Elige un respaldo JSON de Orienta.");
    openName("create",backup);
  }catch(error){notice(error.message,true);}
};
function cancelDelete() {
  clearInterval(deleteTimer);deleteTimer=null;deleteTarget=null;
  $("diagram-delete-confirm").hidden=false;$("diagram-countdown").textContent="";
}
$("diagram-delete").onclick=()=>{
  if(busy||!snapshot||snapshot.diagrams.length<2)return;
  cancelDelete();deleteTarget={id:snapshot.diagram_id,revision:snapshot.revision};
  $("diagram-delete-warning").textContent="Se eliminará «"+currentDiagramName()+"» y sus nodos."+(dirty?" También se perderán los cambios sin guardar.":"");
  $("diagram-delete-dialog").showModal();$("diagram-delete-cancel").focus();
};
$("diagram-delete-cancel").onclick=()=>{$("diagram-delete-dialog").close();cancelDelete();};
$("diagram-delete-dialog").addEventListener("cancel",cancelDelete);
$("diagram-delete-dialog").addEventListener("close",cancelDelete);
$("diagram-delete-confirm").onclick=()=>{
  if(deleteTimer||!deleteTarget)return;
  let remaining=5;$("diagram-delete-confirm").hidden=true;
  $("diagram-countdown").textContent="Se eliminará en 5 segundos. Puedes cancelar.";
  $("diagram-delete-cancel").focus();
  deleteTimer=setInterval(async()=>{
    remaining--;$("diagram-countdown").textContent="Se eliminará en "+remaining+" segundos. Puedes cancelar.";
    if(remaining>0)return;
    clearInterval(deleteTimer);deleteTimer=null;
    const target=deleteTarget;deleteTarget=null;
    $("diagram-delete-dialog").close();
    if(target && target.id===snapshot.diagram_id && target.revision===snapshot.revision)
      await changeDiagram("delete",{diagram_id:target.id});
  },1000);
};
syncDiagrams();
