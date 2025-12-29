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

  updateUser: (userId, data) =>
    api.put(`/auth/users/${userId}`, data),

  deleteUser: (userId) =>
    api.delete(`/auth/users/${userId}`),

  resetUserPassword: (userId, newPassword) =>
    api.post(`/auth/users/${userId}/reset-password`, { new_password: newPassword }),

  changePassword: (currentPassword, newPassword) =>
    api.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword }),
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

  lookupUPC: (upc) =>
    api.get(`/items/lookup-upc/${upc}`),

  searchImage: (productName, categoryName) =>
    api.post('/items/search-image', { product_name: productName, category_name: categoryName }),

  printLabels: async (itemIds, options = {}) => {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/items/print-labels', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        item_ids: itemIds,
        ...options,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to generate labels');
    }

    const html = await response.text();
    return html;
  },
};

// Categories API
export const categoriesAPI = {
  getCategories: () =>
    api.get('/categories/'),

  getCategory: (id) =>
    api.get(`/categories/${id}`),

  getCategoryStockImage: (id) =>
    api.get(`/categories/${id}/stock-image`),

  createCategory: (data) =>
    api.post('/categories/', data),

  updateCategory: (id, data) =>
    api.put(`/categories/${id}`, data),

  deleteCategory: (id) =>
    api.delete(`/categories/${id}`),
};

// Uploads API
export const uploadsAPI = {
  uploadCategoryImage: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/uploads/category-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  deleteCategoryImage: (filename) =>
    api.delete(`/uploads/category-images/${filename}`),

  getCategoryImageUrl: (filename) =>
    `/api/uploads/category-images/${filename}`,
};

// Settings API
export const settingsAPI = {
  getSettings: () =>
    api.get('/settings/'),

  updateSettings: (data) =>
    api.put('/settings/', data),

  getSystemSettings: () =>
    api.get('/settings/system'),

  updateSystemSettings: (data) =>
    api.put('/settings/system', data),

  purgeHistory: () =>
    api.post('/settings/purge-history'),

  getBackupInfo: () =>
    api.get('/settings/backup/info'),

  downloadBackup: async () => {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/settings/backup/download', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to download backup');
    }

    // Get filename from Content-Disposition header if available
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = 'freezer_inventory_backup.db';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
      if (filenameMatch) {
        filename = filenameMatch[1];
      }
    }

    // Create blob and download
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    return response;
  },

  restoreBackup: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/settings/backup/restore', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

export default api;
