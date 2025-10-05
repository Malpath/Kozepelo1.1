const output = document.getElementById("output");
const status = document.getElementById("status");
const spinner = document.getElementById("spinner");
const fileLabel = document.getElementById("filePathLabel");
let currentFilePath = null;

function setBusy(isBusy) {
  document.body.classList.toggle("busy", isBusy);
}

function setStatus(msg, type = "") {
  status.textContent = msg;
  status.className = "status" + (type ? ` ${type}` : "");
}

document.getElementById("btnLoad").addEventListener("click", async () => {
  const result = await window.electronAPI.openFile();
  if (result) {
    if (result.error) {
      output.textContent = result.error;
      setStatus("Hiba a fájl betöltésekor.", "err");
    } else {
      currentFilePath = result.path;
      fileLabel.textContent = result.path;
      output.textContent = result.content; // Itt jelenik meg a fájl tartalma
      setStatus("Fájl betöltve.", "ok");
    }
  } else {
    setStatus("Nincs fájl kiválasztva.", "warn");
  }
});

async function runStep(stepName, label) {
  if (!currentFilePath) {
    setStatus("Előbb tölts be egy TXT fájlt.", "warn");
    return;
  }
  setBusy(true);
  setStatus(`${label} fut...`);
  output.textContent = "";

  try {
    const result = await window.electronAPI.runStep(stepName, currentFilePath);
    if (result.success) {
      output.textContent = result.result;
      setStatus(`${label} sikeresen lefutott.`, "ok");
    } else {
      output.textContent = result.result;
      setStatus(`Hiba a ${label} lépésben.`, "err");
    }
  } catch (err) {
    output.textContent = err.toString();
    setStatus(`Kritikus hiba: ${err.message}`, "err");
  } finally {
    setBusy(false);
  }
}

document.getElementById("btnStep1").addEventListener("click", () => runStep("step1", "1. lépés"));
document.getElementById("btnStep2a").addEventListener("click", () => runStep("step2a", "2/A lépés"));
document.getElementById("btnStep2b").addEventListener("click", () => runStep("step2b", "2/B lépés"));

document.getElementById("btnExport").addEventListener("click", () => {
  const blob = new Blob([output.textContent], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "kozepelo_output.txt";
  a.click();
  setStatus("Fájl exportálva.", "ok");
});