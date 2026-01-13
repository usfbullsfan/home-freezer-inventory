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

// Handle auth errors and auto-logout
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Check if it's an authentication error
    if (error.response) {
      const { status, data } = error.response;

      // Auth errors: 401 Unauthorized or 403 Forbidden
      if (status === 401 || status === 403) {
        // Clear stored auth data
        localStorage.removeItem('token');
        localStorage.removeItem('user');

        // Redirect to login page if not already there
        if (!window.location.pathname.includes('/login') &&
            !window.location.pathname.includes('/activate')) {
          window.location.href = '/login';
        }
      }

      // Also handle 500 errors that might be DB connection issues
      if (status === 500 && data?.error) {
        // If the error message suggests a backend issue, clear session
        const backendErrorPatterns = [
          'database',
          'connection',
          'backend',
          'server error'
        ];
        const errorMessage = (data.error || '').toLowerCase();

        if (backendErrorPatterns.some(pattern => errorMessage.includes(pattern))) {
          localStorage.removeItem('token');
          localStorage.removeItem('user');

          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login';
          }
        }
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }),

  register: (username, password, role = 'user') =>
    api.post('/auth/register', { username, password, role }),

  activate: (activationCode) =>
    api.post('/auth/activate', { activation_code: activationCode }),

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

  // Regenerate activation code for a user
  regenerateActivationCode: (userId) =>
    api.post(`/auth/users/${userId}/regenerate-activation`),

  changePassword: (currentPassword, newPassword) =>
    api.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword }),

  useRecoveryCode: (username, code) =>
    api.post('/passkey/recovery/use', { username, code }),

  // Quick login (development only)
  getQuickLoginStatus: () =>
    axios.get('/api/auth/quick-login-status'),

  getQuickLoginUsers: () =>
    axios.get('/api/auth/quick-login-users'),

  quickLogin: (userId) =>
    axios.post('/api/auth/quick-login', { user_id: userId }),
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

  purgeAllItems: () =>
    api.delete('/items/purge-all'),

  copyProdDb: () =>
    api.post('/items/copy-prod-db'),

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

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const filename = response.headers.get('Content-Disposition')?.match(/filename="?(.+)"?/)?.[1] || 'freezer_labels.pdf';
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  exportCSV: async (status = 'in_freezer') => {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/items/export/csv?status=${status}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to export CSV');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const filename = response.headers.get('Content-Disposition')?.match(/filename="?(.+)"?/)?.[1] || 'inventory.csv';
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  exportJSON: async (status = 'in_freezer') => {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/items/export/json?status=${status}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to export JSON');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const filename = response.headers.get('Content-Disposition')?.match(/filename="?(.+)"?/)?.[1] || 'inventory.json';
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  importCSV: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/items/import/csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  importJSON: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/items/import/json', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
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

// Feedback API
export const feedbackAPI = {
  submit: (type, description) =>
    api.post('/feedback/submit', { type, description }),

  list: () =>
    api.get('/feedback/list'),

  process: () =>
    api.post('/feedback/process'),

  getStats: () =>
    api.get('/feedback/stats'),
};

export default api;
