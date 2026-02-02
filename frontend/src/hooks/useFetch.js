/**
 * useFetch - Hook para fetch de datos con manejo de estado
 *
 * USO:
 *   const { data, loading, error, refetch } = useFetch('/api/projects');
 *
 *   // Con dependencias (refetch cuando cambien)
 *   const { data } = useFetch(`/api/projects/${id}`, [id]);
 *
 *   // Con opciones
 *   const { data } = useFetch('/api/projects', [], { method: 'POST', body: {...} });
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import api from '../services/api';

export function useFetch(url, dependencies = [], options = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Ref para evitar actualizar estado después de desmontar
  const isMounted = useRef(true);

  // Ref para almacenar opciones de forma estable (evita re-renders infinitos)
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const fetchData = useCallback(async () => {
    if (!url) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let result;
      const { method = 'GET', body, ...restOptions } = optionsRef.current;

      switch (method.toUpperCase()) {
        case 'POST':
          result = await api.post(url, body, restOptions);
          break;
        case 'PUT':
          result = await api.put(url, body, restOptions);
          break;
        case 'PATCH':
          result = await api.patch(url, body, restOptions);
          break;
        case 'DELETE':
          result = await api.delete(url, restOptions);
          break;
        default:
          result = await api.get(url, restOptions);
      }

      if (isMounted.current) {
        setData(result);
        setError(null);
      }
    } catch (err) {
      if (isMounted.current) {
        setError(err.message || 'Error fetching data');
        setData(null);
      }
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, [url]);

  useEffect(() => {
    isMounted.current = true;
    fetchData();

    return () => {
      isMounted.current = false;
    };
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    setData, // Para actualizaciones optimistas
  };
}

export default useFetch;
