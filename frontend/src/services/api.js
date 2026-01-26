/**
 * ============================================================
 * ReplicarIA - Servicio de API Centralizado
 * ============================================================
 *
 * Este módulo centraliza TODAS las llamadas a la API.
 * Usar este servicio en lugar de crear instancias de axios separadas.
 *
 * USO:
 *   import api from './services/api';
 *
 *   // GET request
 *   const data = await api.get('/projects');
 *
 *   // POST request
 *   const result = await api.post('/projects', { name: 'Test' });
 *
 * ============================================================
 */

import axios from 'axios';

// Configuración base
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

// Crear instancia de axios configurada
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 segundos
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================
// Request Interceptor - Agregar token automáticamente
// ============================================================
api.interceptors.request.use(
  (config) => {
    // Agregar token de autenticación si existe
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Agregar empresa_id si está seleccionada
    const empresaId = localStorage.getItem('selected_empresa_id');
    if (empresaId) {
      config.headers['X-Empresa-ID'] = empresaId;
    }

    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// ============================================================
// Response Interceptor - Manejo de errores centralizado
// ============================================================
api.interceptors.response.use(
  (response) => {
    // Retornar solo los datos de la respuesta
    return response.data;
  },
  (error) => {
    // Manejar errores de red
    if (!error.response) {
      console.error('Network error:', error.message);
      return Promise.reject({
        message: 'Error de conexión. Verifica tu conexión a internet.',
        isNetworkError: true,
      });
    }

    const { status, data } = error.response;

    // Manejar errores específicos por código de estado
    switch (status) {
      case 401:
        // Token expirado o inválido
        console.warn('Unauthorized - clearing token');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        // Redirigir a login si no estamos ya ahí
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        return Promise.reject({
          message: 'Sesión expirada. Por favor inicia sesión nuevamente.',
          status: 401,
        });

      case 403:
        return Promise.reject({
          message: 'No tienes permisos para realizar esta acción.',
          status: 403,
        });

      case 404:
        return Promise.reject({
          message: data?.detail || 'Recurso no encontrado.',
          status: 404,
        });

      case 422:
        // Error de validación
        return Promise.reject({
          message: data?.detail || 'Error de validación en los datos enviados.',
          status: 422,
          errors: data?.errors,
        });

      case 500:
        console.error('Server error:', data);
        return Promise.reject({
          message: 'Error interno del servidor. Intenta más tarde.',
          status: 500,
        });

      default:
        return Promise.reject({
          message: data?.detail || data?.message || `Error ${status}`,
          status,
          data,
        });
    }
  }
);

// ============================================================
// Métodos de utilidad
// ============================================================

/**
 * Subir archivos con progreso
 */
api.uploadFile = async (url, file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  return api.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });
};

/**
 * Descargar archivos
 */
api.downloadFile = async (url, filename) => {
  const response = await api.get(url, {
    responseType: 'blob',
  });

  // Crear link de descarga
  const downloadUrl = window.URL.createObjectURL(new Blob([response]));
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(downloadUrl);
};

/**
 * Request con retry automático
 */
api.withRetry = async (requestFn, maxRetries = 3, delay = 1000) => {
  let lastError;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error;
      if (error.status === 401 || error.status === 403) {
        // No reintentar errores de autenticación
        throw error;
      }
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
      }
    }
  }

  throw lastError;
};

// ============================================================
// Endpoints específicos (helpers)
// ============================================================

api.auth = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
  refreshToken: () => api.post('/auth/refresh'),
};

api.projects = {
  list: (params) => api.get('/api/projects/', { params }),
  get: (id) => api.get(`/api/projects/${id}`),
  create: (data) => api.post('/api/projects/submit', data),
  update: (id, data) => api.patch(`/api/projects/${id}`, data),
  delete: (id) => api.delete(`/api/projects/${id}`),
  getStatus: (id) => api.get(`/api/projects/${id}/status`),
  executeStage: (id, stage) => api.post(`/api/projects/${id}/stage${stage}`),
};

api.agents = {
  list: () => api.get('/api/agents/'),
  get: (id) => api.get(`/api/agents/${id}`),
  analyze: (id, data) => api.post(`/api/agents/${id}/analyze`, data),
  getInteractions: () => api.get('/api/agents/interactions/recent'),
};

api.empresas = {
  list: () => api.get('/api/empresas/'),
  get: (id) => api.get(`/api/empresas/${id}`),
  create: (data) => api.post('/api/empresas/', data),
  update: (id, data) => api.patch(`/api/empresas/${id}`, data),
};

export default api;
