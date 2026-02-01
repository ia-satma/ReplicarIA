import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const clearError = () => setError(null);

  const verifyAuth = useCallback(async () => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const response = await api.get('/api/auth/otp/session');
      // Manejar diferentes formatos de respuesta del backend
      const userData = response?.data?.user || response?.user || response?.data;
      if (response?.success && userData) {
        setUser(userData);
      } else if (userData && !response?.success) {
        // Si no hay flag success pero hay datos de usuario
        setUser(userData);
      } else {
        localStorage.removeItem('auth_token');
        setUser(null);
      }
    } catch (err) {
      localStorage.removeItem('auth_token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    verifyAuth();
  }, [verifyAuth]);

  const login = async (email, password) => {
    setError(null);
    try {
      const response = await api.post('/api/auth/login', { email, password });
      if (response.access_token) {
        localStorage.setItem('auth_token', response.access_token);
        setUser(response.user);
        return { success: true };
      }
      return { success: false, error: 'Error de autenticación' };
    } catch (err) {
      // api.js ya transforma el error - usar .message directamente
      const errorMsg = err.message || err.detail || 'Error al iniciar sesión';
      const statusCode = err.status || err.response?.status;
      setError(errorMsg);
      return { success: false, error: errorMsg, statusCode };
    }
  };

  const register = async (userData) => {
    setError(null);
    try {
      const response = await api.post('/api/auth/register', userData);
      if (response.success) {
        if (response.pending_approval) {
          return {
            success: true,
            pending_approval: true,
            message: response.message
          };
        }
        if (response.access_token) {
          localStorage.setItem('auth_token', response.access_token);
          setUser(response.user);
          return { success: true };
        }
      }
      return { success: false, error: response.message || 'Error en el registro' };
    } catch (err) {
      // api.js ya transforma el error - usar .message directamente
      const errorMsg = err.message || err.detail || 'Error al registrar';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  const loginWithOTP = async (email, code) => {
    setError(null);
    try {
      const response = await api.post('/api/auth/otp/verify-code', { email, code });
      // Manejar diferentes formatos de respuesta
      const token = response?.data?.token || response?.token || response?.access_token;
      const userData = response?.data?.user || response?.user;

      if ((response?.success || token) && token) {
        localStorage.setItem('auth_token', token);
        if (userData) setUser(userData);
        return { success: true };
      }
      return { success: false, error: response?.message || 'Error de verificación' };
    } catch (err) {
      const errorMsg = err?.message || err?.detail || 'Código inválido o expirado';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  const logout = async () => {
    try {
      await api.post('/api/auth/otp/logout');
    } catch {
      // El logout puede fallar si el token ya expiró, lo cual está bien
    }
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    localStorage.removeItem('selected_empresa_id');
    setUser(null);
  };

  const value = {
    user,
    loading,
    error,
    isAuthenticated: !!user,
    login,
    loginWithOTP,
    register,
    logout,
    clearError,
    verifyAuth
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export { api };
