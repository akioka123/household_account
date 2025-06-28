import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { addExpense, getExpenses, addIncome, getIncomes } from './db.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Serves static files from the frontend directory.
 * @module server
 */

const frontendDir = path.join(__dirname, 'frontend');
const port = process.env.PORT || 3000;

const server = http.createServer((req, res) => {
  if (req.url === '/expenses' && req.method === 'GET') {
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(getExpenses()));
    return;
  }

  if (req.url === '/incomes' && req.method === 'GET') {
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(getIncomes()));
    return;
  }

  if (req.url === '/expenses' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      const data = JSON.parse(body || '{}');
      addExpense(Number(data.amount), data.description || '');
      res.statusCode = 201;
      res.end('OK');
    });
    return;
  }

  if (req.url === '/incomes' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      const data = JSON.parse(body || '{}');
      addIncome(Number(data.amount), data.description || '');
      res.statusCode = 201;
      res.end('OK');
    });
    return;
  }

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
