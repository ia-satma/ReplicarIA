import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { useInterval } from '../hooks';

const MetricsDashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = useCallback(async () => {
    try {
      const data = await api.get('/api/metrics/llm-costs');
      setMetrics(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching metrics:', error);
      setLoading(false);
    }
  }, []);

  // Fetch inicial
  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  // Actualizar cada 30 segundos
  useInterval(fetchMetrics, 30000);

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-xl text-gray-600">Cargando métricas...</div>
    </div>
  );

  if (!metrics) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-xl text-gray-600">No hay datos disponibles</div>
    </div>
  );

  const { query_router, embedding_cache, rag_parallel } = metrics;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-[#1A1A1A] text-white py-4 px-6 shadow-lg">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">
            <span className="text-[#7FEDD8]">Revisar.ia</span> - Métricas LLM
          </h1>
          <Link 
            to="/" 
            className="px-4 py-2 bg-[#7FEDD8] text-[#1A1A1A] rounded-lg hover:bg-[#5DD5C0] transition font-medium"
          >
            Volver al Dashboard
          </Link>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-lg border-l-4 border-[#7FEDD8]">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Total de Consultas</h3>
            <p className="text-4xl font-bold text-[#1A1A1A]">{query_router.total_queries}</p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-lg border-l-4 border-green-500">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Ahorro Estimado</h3>
            <p className="text-4xl font-bold text-green-600">${query_router.estimated_savings}</p>
            <p className="text-sm text-gray-500 mt-1">{query_router.savings_percent}% de ahorro</p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-lg border-l-4 border-blue-500">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Costo Total</h3>
            <p className="text-4xl font-bold text-blue-600">${query_router.total_cost}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-lg mb-8">
          <h2 className="text-2xl font-bold text-[#1A1A1A] mb-4">Desglose por Tier (Query Router)</h2>
          <div className="space-y-4">
            {Object.entries(query_router.cost_breakdown).map(([tier, data]) => (
              <div key={tier} className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <div>
                  <span className="font-semibold capitalize text-lg">{tier}</span>
                  <span className="text-sm text-gray-500 ml-2">({data.model})</span>
                </div>
                <div className="text-right">
                  <p className="font-bold text-lg">{data.queries} consultas</p>
                  <p className="text-sm text-gray-600">${data.cost}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <h2 className="text-2xl font-bold text-[#1A1A1A] mb-4">Caché de Embeddings</h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Tasa de Aciertos</p>
                <p className="text-3xl font-bold text-[#7FEDD8]">{embedding_cache.hit_rate_percent}%</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Aciertos de Caché</p>
                <p className="text-3xl font-bold text-green-600">{embedding_cache.cache_hits}</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Ahorro</p>
                <p className="text-3xl font-bold text-blue-600">${embedding_cache.estimated_cost_saved}</p>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              Total solicitudes: {embedding_cache.total_requests} | 
              Fallos: {embedding_cache.cache_misses}
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-lg">
            <h2 className="text-2xl font-bold text-[#1A1A1A] mb-4">Pre-carga RAG Paralela</h2>
            <div className="text-center p-6 bg-gradient-to-r from-[#7FEDD8]/20 to-[#5DD5C0]/20 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">Tiempo promedio ahorrado por proyecto</p>
              <p className="text-5xl font-bold text-[#1A1A1A]">{rag_parallel.avg_time_saved_seconds}s</p>
            </div>
            <div className="mt-4 text-center text-gray-500">
              Total precargas: {rag_parallel.total_preloads}
            </div>
          </div>
        </div>

        <div className="mt-8 bg-gradient-to-r from-[#1A1A1A] to-gray-800 text-white p-6 rounded-lg shadow-lg">
          <h2 className="text-xl font-bold mb-4">Resumen de Optimizaciones</h2>
          <div className="grid md:grid-cols-3 gap-6 text-center">
            <div>
              <p className="text-[#7FEDD8] text-3xl font-bold">60-70%</p>
              <p className="text-gray-300 text-sm mt-1">Ahorro Query Router</p>
            </div>
            <div>
              <p className="text-[#7FEDD8] text-3xl font-bold">{embedding_cache.hit_rate_percent}%</p>
              <p className="text-gray-300 text-sm mt-1">Tasa de Aciertos Caché</p>
            </div>
            <div>
              <p className="text-[#7FEDD8] text-3xl font-bold">~6s</p>
              <p className="text-gray-300 text-sm mt-1">Ahorro RAG Paralelo</p>
            </div>
          </div>
        </div>

        <p className="text-center text-gray-400 text-sm mt-6">
          Última actualización: {new Date(metrics.timestamp).toLocaleString('es-MX')}
        </p>
      </main>
    </div>
  );
};

export default MetricsDashboard;
