// ============================================================
// ReplicarIA - Empresa Service
// ============================================================

// Obtener URL del backend desde variable de entorno o usar relativa
const API_URL = process.env.REACT_APP_BACKEND_URL || '';

/**
 * Helper para obtener headers con autenticación
 */
const getAuthHeaders = () => {
  const token = localStorage.getItem('auth_token');
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

/**
 * Helper para manejar respuestas de la API
 */
const handleResponse = async (response) => {
  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage;
    try {
      const errorJson = JSON.parse(errorText);
      errorMessage = errorJson.detail || errorJson.message || `Error ${response.status}`;
    } catch {
      errorMessage = errorText || `Error ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorMessage);
  }

  const text = await response.text();
  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
};

export const empresaService = {
  /**
   * Crear nueva empresa
   */
  async crear(data) {
    try {
      const response = await fetch(`${API_URL}/api/empresas/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(data)
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Error creando empresa:', error);
      throw error;
    }
  },

  /**
   * Auto-completar datos con IA
   */
  async autofill(data) {
    try {
      const response = await fetch(`${API_URL}/api/empresas/autofill-ia`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(data)
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Error en autofill IA:', error);
      throw error;
    }
  },

  /**
   * Obtener empresa por ID
   */
  async obtener(empresaId) {
    try {
      const response = await fetch(`${API_URL}/api/empresas/${empresaId}`, {
        headers: getAuthHeaders()
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Error obteniendo empresa:', error);
      throw error;
    }
  },

  /**
   * Listar todas las empresas
   */
  async listar() {
    try {
      const response = await fetch(`${API_URL}/api/empresas/`, {
        headers: getAuthHeaders()
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Error listando empresas:', error);
      throw error;
    }
  },

  /**
   * Actualizar empresa
   */
  async actualizar(empresaId, data) {
    try {
      const response = await fetch(`${API_URL}/api/empresas/${empresaId}`, {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body: JSON.stringify(data)
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Error actualizando empresa:', error);
      throw error;
    }
  },

  /**
   * Actualizar visión y misión
   */
  async actualizarVisionMision(empresaId, vision, mision) {
    try {
      const response = await fetch(`${API_URL}/api/empresas/${empresaId}/vision-mision`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ vision, mision })
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Error actualizando visión/misión:', error);
      throw error;
    }
  },

  /**
   * Actualizar pilares estratégicos
   */
  async actualizarPilares(empresaId, pilares) {
    try {
      const response = await fetch(`${API_URL}/api/empresas/${empresaId}/pilares`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ pilares })
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Error actualizando pilares:', error);
      throw error;
    }
  },

  /**
   * Actualizar OKRs
   */
  async actualizarOKRs(empresaId, okrs) {
    try {
      const response = await fetch(`${API_URL}/api/empresas/${empresaId}/okrs`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ okrs })
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Error actualizando OKRs:', error);
      throw error;
    }
  },

  /**
   * Obtener tipologías de una empresa
   */
  async getTipologias(empresaId) {
    try {
      const response = await fetch(`${API_URL}/api/empresas/${empresaId}/tipologias`, {
        headers: getAuthHeaders()
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Error obteniendo tipologías:', error);
      throw error;
    }
  },

  /**
   * Configurar tipologías
   */
  async configurarTipologias(empresaId, tipologias) {
    try {
      const response = await fetch(`${API_URL}/api/empresas/${empresaId}/tipologias`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ tipologias })
      });
      return await handleResponse(response);
    } catch (error) {
      console.error('Error configurando tipologías:', error);
      throw error;
    }
  }
};
