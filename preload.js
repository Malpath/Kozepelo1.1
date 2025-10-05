const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  openFile: () => ipcRenderer.invoke("dialog:openFile"),
  runStep: (step, infile) => ipcRenderer.invoke("run-step", step, infile),
});
