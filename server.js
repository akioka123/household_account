import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { addExpense, getExpenses, addIncome, getIncomes, getIncomesByMonth, updateIncome, updateExpense } from './db.js';

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

  if (req.url.startsWith('/expenses/') && req.method === 'PUT') {
    const id = Number(req.url.split('/')[2]);
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      const data = JSON.parse(body || '{}');
      updateExpense(id, Number(data.amount), data.description || '');
      res.statusCode = 200;
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

  if (req.url.startsWith('/incomes/month/') && req.method === 'GET') {
    const parts = req.url.split('/');
    const year = parseInt(parts[3]);
    const month = parseInt(parts[4]);
    if (!isNaN(year) && !isNaN(month)) {
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify(getIncomesByMonth(year, month)));
    } else {
      res.statusCode = 400;
      res.end('Bad Request');
    }
    return;
  }

  if (req.url.startsWith('/incomes/') && req.method === 'PUT') {
    const parts = req.url.split('/');
    const id = parseInt(parts[2]);
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      const data = JSON.parse(body || '{}');
      if (!isNaN(id) && data.amount && data.description !== undefined) {
        updateIncome(id, Number(data.amount), data.description);
        res.statusCode = 200;
        res.end('OK');
      } else {
        res.statusCode = 400;
        res.end('Bad Request');
      }
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
