import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { empresaService } from '../../services/empresaService';

const IndustryBadge = ({ industry }) => {
  const colors = {
    'Tecnología': 'bg-blue-100 text-blue-700',
    'Finanzas': 'bg-green-100 text-green-700',
    'Manufactura': 'bg-orange-100 text-orange-700',
    'Retail': 'bg-purple-100 text-purple-700',
    'Servicios Profesionales': 'bg-indigo-100 text-indigo-700',
    'Construcción': 'bg-yellow-100 text-yellow-700',
    'Salud': 'bg-red-100 text-red-700',
    'Educación': 'bg-cyan-100 text-cyan-700',
    'Transporte y Logística': 'bg-teal-100 text-teal-700',
    'Energía': 'bg-amber-100 text-amber-700',
    'Agroindustria': 'bg-lime-100 text-lime-700'
  };

  const colorClass = colors[industry] || 'bg-gray-100 text-gray-700';

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colorClass}`}>
      {industry || 'Sin industria'}
    </span>
  );
};

const EmpresaCard = ({ empresa }) => {
  const navigate = useNavigate();
  const tipologiasCount = empresa.tipologias_activas?.length || 0;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-800 mb-1">{empresa.nombre}</h3>
          <p className="text-sm text-gray-500 font-mono">{empresa.rfc}</p>
        </div>
        <IndustryBadge industry={empresa.industria} />
      </div>

      {empresa.vision && (
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">{empresa.vision}</p>
      )}

      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            {tipologiasCount} tipología{tipologiasCount !== 1 ? 's' : ''}
          </span>
          {empresa.pilares_estrategicos?.length > 0 && (
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              {empresa.pilares_estrategicos.length} pilar{empresa.pilares_estrategicos.length !== 1 ? 'es' : ''}
            </span>
          )}
        </div>
        <button
          onClick={() => navigate(`/empresa/${empresa.id}/configuracion`)}
          className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
        >
          Configurar
        </button>
      </div>
    </div>
  );
};

const EmptyState = () => (
  <div className="text-center py-16 bg-white rounded-xl border-2 border-dashed border-gray-300">
    <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
    <h3 className="text-lg font-medium text-gray-800 mb-2">No hay empresas registradas</h3>
    <p className="text-gray-500 mb-6 max-w-sm mx-auto">
      Comience creando su primera empresa para configurar el sistema multi-tenant.
    </p>
    <Link
      to="/empresas/nueva"
      className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
      </svg>
      Crear Primera Empresa
    </Link>
  </div>
);

export default function ListaEmpresas() {
  const [empresas, setEmpresas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadEmpresas();
  }, []);

  const loadEmpresas = async () => {
    try {
      setLoading(true);
      const data = await empresaService.listar();
      setEmpresas(data.empresas || []);
      setError(null);
    } catch (err) {
      setError('Error al cargar las empresas');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-200 rounded-full animate-spin border-t-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando empresas...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Empresas</h1>
            <p className="text-gray-600">Gestione las empresas del sistema multi-tenant</p>
          </div>
          <Link
            to="/empresas/nueva"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Nueva Empresa
          </Link>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
            <button onClick={loadEmpresas} className="ml-4 underline hover:no-underline">
              Reintentar
            </button>
          </div>
        )}

        {empresas.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {empresas.map((empresa) => (
              <EmpresaCard key={empresa.id} empresa={empresa} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
