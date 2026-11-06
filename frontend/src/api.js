// src/api.js — relative URL so it works everywhere (local, Render, cloud)
import axios from 'axios';

// When deployed on Render, frontend & backend are on the same domain/port,
// so relative baseURL '' routes directly to /api/extract and /api/report
const api = axios.create({ baseURL: '' });

export default api;
