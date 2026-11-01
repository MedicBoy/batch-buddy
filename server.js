const http = require("node:http");
const { readFile } = require("node:fs/promises");
const path = require("node:path");
const { analyzeOffer, parseOfferText } = require("./src/advisor");

const publicDirectory = path.join(__dirname, "public");
const mimeTypes = { ".css": "text/css", ".html": "text/html", ".js": "text/javascript", ".webmanifest": "application/manifest+json" };

function respondJson(response, status, payload) {
  response.writeHead(status, { "content-type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(payload));
}

async function readRequestBody(request) {
  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

const server = http.createServer(async (request, response) => {
  try {
    if (request.method === "POST" && request.url === "/api/analyze") {
      return respondJson(response, 200, analyzeOffer(await readRequestBody(request)));
    }

    if (request.method === "POST" && request.url === "/api/parse") {
      return respondJson(response, 200, parseOfferText((await readRequestBody(request)).text));
    }

    if (request.method !== "GET") return respondJson(response, 405, { error: "Method not allowed" });
    const requestPath = request.url === "/" ? "/index.html" : request.url;
    const safePath = path.normalize(requestPath).replace(/^([/\\])+/, "");
    const filePath = path.join(publicDirectory, safePath);
    if (!filePath.startsWith(publicDirectory)) return respondJson(response, 403, { error: "Forbidden" });
    const extension = path.extname(filePath);
    response.writeHead(200, { "content-type": `${mimeTypes[extension] || "application/octet-stream"}; charset=utf-8` });
    response.end(await readFile(filePath));
  } catch (error) {
    const status = error instanceof SyntaxError ? 400 : error.code === "ENOENT" ? 404 : 500;
    respondJson(response, status, { error: status === 500 ? "Unexpected server error" : error.message });
  }
});

server.listen(process.env.PORT || 4173, "127.0.0.1", () => {
  console.log("Batch Buddy POC is ready at http://127.0.0.1:4173");
});
