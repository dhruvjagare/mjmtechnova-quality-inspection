// src/api.js — simple axios wrapper, no auth
import axios from 'axios';

const api = axios.create({ baseURL: 'http://localhost:8000' });

export default api;
