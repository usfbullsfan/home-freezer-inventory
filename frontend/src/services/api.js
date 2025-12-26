import axios from 'axios';

const API_BASE_URL = '/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }),

  register: (username, password, role = 'user') =>
    api.post('/auth/register', { username, password, role }),

  getCurrentUser: () =>
    api.get('/auth/me'),

  getUsers: () =>
    api.get('/auth/users'),
};

// Items API
export const itemsAPI = {
  getItems: (params = {}) =>
    api.get('/items/', { params }),

  getItem: (id) =>
    api.get(`/items/${id}`),

  getItemByQR: (qrCode) =>
    api.get(`/items/qr/${qrCode}`),

  createItem: (data) =>
    api.post('/items/', data),

  updateItem: (id, data) =>
    api.put(`/items/${id}`, data),

  updateItemStatus: (id, status) =>
    api.put(`/items/${id}/status`, { status }),

  deleteItem: (id) =>
    api.delete(`/items/${id}`),

  getExpiringSoon: (days = 30) =>
    api.get('/items/expiring-soon', { params: { days } }),

  getOldestItems: (limit = 10) =>
    api.get('/items/oldest', { params: { limit } }),

  getQRImage: (qrCode) =>
    `/api/items/qr/${qrCode}/image`,
};

// Categories API
export const categoriesAPI = {
  getCategories: () =>
    api.get('/categories/'),

  getCategory: (id) =>
    api.get(`/categories/${id}`),

  createCategory: (data) =>
    api.post('/categories/', data),

  updateCategory: (id, data) =>
    api.put(`/categories/${id}`, data),

  deleteCategory: (id) =>
    api.delete(`/categories/${id}`),
};

// Settings API
export const settingsAPI = {
  getSettings: () =>
    api.get('/settings/'),

  updateSettings: (data) =>
    api.put('/settings/', data),

  purgeHistory: () =>
    api.post('/settings/purge-history'),
};

export default api;
