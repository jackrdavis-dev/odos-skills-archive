import fs from "node:fs/promises";
import { createRequire } from "node:module";

const [imagePath, outputPath, modulePath] = process.argv.slice(2);
if (!imagePath || !outputPath || !modulePath) {
  throw new Error("Usage: node qa_ocr_tesseract.mjs <image> <output.txt> <tesseract.js module>");
}

const require = createRequire(import.meta.url);
const { createWorker } = require(modulePath);
const worker = await createWorker("eng");
try {
  const result = await worker.recognize(imagePath);
  await fs.writeFile(outputPath, result.data.text, "utf8");
} finally {
  await worker.terminate();
}
