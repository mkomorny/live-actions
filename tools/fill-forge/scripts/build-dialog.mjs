// Bundle the Fill Forge dialog into one HTML file the desktop host can load.
import * as esbuild from "esbuild";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const ui = await esbuild.build({
  absWorkingDir: root,
  entryPoints: ["src/webview/main.ts"],
  bundle: true,
  format: "iife",
  platform: "browser",
  write: false,
  minify: false,
  sourcemap: false,
  logLevel: "info",
});
const js = ui.outputFiles[0].text;
const template = fs.readFileSync(path.join(root, "src/webview/interface.html"), "utf8");
const html = template.replace("/*__UI_BUNDLE__*/", () => js);
const outDir = path.join(root, "ui");
fs.mkdirSync(outDir, { recursive: true });
const out = path.join(outDir, "dialog.html");
fs.writeFileSync(out, html, "utf8");
console.log("wrote", out, "(" + html.length + " bytes)");
