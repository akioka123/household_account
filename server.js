import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Serves static files from the frontend directory.
 * @module server
 */

const frontendDir = path.join(__dirname, 'frontend');
const port = process.env.PORT || 3000;

const server = http.createServer((req, res) => {
  let filePath = path.join(frontendDir, req.url === '/' ? 'index.html' : req.url);
  if (!filePath.startsWith(frontendDir)) {
    res.statusCode = 400;
    res.end('Bad Request');
    return;
  }
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.statusCode = 404;
      res.end('Not Found');
      return;
    }
    const ext = path.extname(filePath);
    const map = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css' };
    res.setHeader('Content-Type', map[ext] || 'text/plain');
    res.end(data);
  });
});

server.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});
