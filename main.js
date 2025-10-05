const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const pythonScript = path.join(__dirname, "feldolgozo.py");
const fs = require("fs");
const { spawn } = require("child_process");

let mainWindow;
let previousOutput = "";

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
    },
  });
  mainWindow.loadFile("index.html");
}

app.whenReady().then(createWindow);

// --- TXT betöltés ---
ipcMain.handle("dialog:openFile", async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    filters: [{ name: "Text files", extensions: ["txt"] }],
    properties: ["openFile"],
  });
  if (canceled) return null;
  const filePath = filePaths[0];
  try {
    const content = await fs.promises.readFile(filePath, "utf8");
    return { path: filePath, content: content };
  } catch (err) {
    return { path: null, error: `Hiba a fájl olvasása közben: ${err.message}` };
  }
});

// --- Lépések futtatása ---
ipcMain.handle("run-step", async (event, step, infile) => {
  const pythonPath = "python3"; // Ha Windows-on vagy, lehet 'python' kell ide
  const scriptPath = path.join(__dirname, "feldolgozo.py");

  let inputPath = infile;
  if (step !== "step1") {
    if (!previousOutput) {
      return { success: false, result: "Előbb futtasd a step1-et, hogy legyen előző kimenet." };
    }
    const tempDir = app.getPath("temp");
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }
    inputPath = path.join(tempDir, "prev_step_output.txt");
    try {
      fs.writeFileSync(inputPath, previousOutput, "utf8");
    } catch (err) {
      return { success: false, result: `Temp fájl írási hiba: ${err.message}` };
    }
  }

  return new Promise((resolve) => {
    let output = "";
    let error = "";

    const py = spawn(pythonPath, [scriptPath, inputPath, step]); // Fordítva: infile (inputPath), majd step

    py.stdout.on("data", (data) => (output += data.toString()));
    py.stderr.on("data", (data) => (error += data.toString()));

    py.on("error", (err) => {
      resolve({ success: false, result: `Python indítási hiba: ${err.message} (Ellenőrizd, hogy a python3 telepítve van-e!)` });
    });

    py.on("close", (code) => {
      if (code === 0) {
        previousOutput = output;
        resolve({ success: true, result: output.trim() });
      } else {
        resolve({
          success: false,
          result: `Hiba: ${error || "Ismeretlen hiba. Ellenőrizd a Python szkriptet."}`,
        });
      }
    });
  });
});