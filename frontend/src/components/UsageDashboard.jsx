import { useState, useEffect } from 'react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

export function UsageDashboard({ empresaId }) {
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchUsage();
  }, [empresaId]);

  const fetchUsage = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setError('Sesión no iniciada');
        setLoading(false);
        return;
      }
      
      const url = empresaId 
        ? `${API_BASE}/api/usage/dashboard?empresa_id=${empresaId}`
        : `${API_BASE}/api/usage/dashboard`;
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const text = await response.text();
      let data;
      try {
        data = text ? JSON.parse(text) : {};
      } catch {
        data = { detail: 'Error de servidor' };
      }
      
      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Error al cargar uso');
      }
      
      setUsage(data);
    } catch (err) {
      setError(err.message || 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-gray-800/50 rounded-xl p-4 animate-pulse">
        <div className="h-4 bg-gray-700 rounded w-1/3 mb-4"></div>
        <div className="h-8 bg-gray-700 rounded w-full"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500/30 rounded-xl p-4">
        <p className="text-red-400 text-sm">Error: {error}</p>
      </div>
    );
  }

  const requestsPct = usage?.pct_requests_usado || usage?.pct_requests || 0;
  const tokensPct = usage?.pct_tokens_usado || usage?.pct_tokens || 0;
  
  const getBarColor = (pct) => {
    if (pct >= 90) return 'bg-red-500';
    if (pct >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-4 border border-gray-700/50">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-300">Uso del Plan</h3>
        <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs uppercase">
          {usage?.plan_nombre || usage?.plan || 'Free'}
        </span>
      </div>
      
      <div className="space-y-4">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">Requests</span>
            <span className="text-gray-300">
              {usage?.requests_hoy || 0} / {usage?.limite_requests_dia || usage?.limite_requests || 50}
            </span>
          </div>
          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
            <div 
              className={`h-full ${getBarColor(requestsPct)} transition-all duration-500`}
              style={{ width: `${Math.min(requestsPct, 100)}%` }}
            />
          </div>
        </div>
        
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">Tokens</span>
            <span className="text-gray-300">
              {((usage?.tokens_hoy || 0) / 1000).toFixed(1)}K / {((usage?.limite_tokens_dia || usage?.limite_tokens || 100000) / 1000).toFixed(0)}K
            </span>
          </div>
          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
            <div 
              className={`h-full ${getBarColor(tokensPct)} transition-all duration-500`}
              style={{ width: `${Math.min(tokensPct, 100)}%` }}
            />
          </div>
        </div>
      </div>
      
      {(requestsPct >= 80 || tokensPct >= 80) && (
        <div className="mt-4 p-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
          <p className="text-xs text-yellow-400">
            Estas cerca del limite diario. Considera actualizar tu plan.
          </p>
        </div>
      )}
    </div>
  );
}

export default UsageDashboard;
