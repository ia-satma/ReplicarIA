import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const api = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL 
    ? `${process.env.REACT_APP_BACKEND_URL}/api`
    : '/api',
  headers: {
    'Content-Type': 'application/json',
  }
});

api.interceptors.request.use(config => {
  const authEndpoints = ['/auth/login', '/auth/register', '/auth/otp/request-code', '/auth/otp/verify-code'];
  const isAuthEndpoint = authEndpoints.some(endpoint => config.url?.includes(endpoint));
  
  if (!isAuthEndpoint) {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

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
      const response = await api.get('/auth/otp/session');
      if (response.data.success && response.data.data?.user) {
        setUser(response.data.data.user);
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
      const response = await api.post('/auth/login', { email, password });
      if (response.data.access_token) {
        localStorage.setItem('auth_token', response.data.access_token);
        setUser(response.data.user);
        return { success: true };
      }
      return { success: false, error: 'Error de autenticación' };
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Error al iniciar sesión';
      const statusCode = err.response?.status;
      setError(errorMsg);
      return { success: false, error: errorMsg, statusCode };
    }
  };

  const register = async (userData) => {
    setError(null);
    try {
      const response = await api.post('/auth/register', userData);
      if (response.data.success) {
        if (response.data.pending_approval) {
          return { 
            success: true, 
            pending_approval: true, 
            message: response.data.message 
          };
        }
        if (response.data.access_token) {
          localStorage.setItem('auth_token', response.data.access_token);
          setUser(response.data.user);
          return { success: true };
        }
      }
      return { success: false, error: response.data.message || 'Error en el registro' };
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Error al registrar';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  const loginWithOTP = async (email, code) => {
    setError(null);
    try {
      const response = await api.post('/auth/otp/verify-code', { email, code });
      if (response.data.success && response.data.data?.token) {
        localStorage.setItem('auth_token', response.data.data.token);
        setUser(response.data.data.user);
        return { success: true };
      }
      return { success: false, error: response.data.message || 'Error de verificación' };
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Código inválido o expirado';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  const logout = async () => {
    try {
      await api.post('/auth/otp/logout');
    } catch (err) {
      // El logout puede fallar si el token ya expiró, lo cual está bien
      console.log('Logout request completed (may have already expired)');
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
