import React, { useState, useEffect } from 'react';
import api from '../services/api';
import ProjectActions from './ProjectActions';
import VersioningPanel from './VersioningPanel';
import CargaDocumentos from './CargaDocumentos';
import ListaDocumentos from './ListaDocumentos';
import Modal from './Modal';
import RiskScoreBadge from './RiskScoreBadge';
import RiskScoreMiniChart from './RiskScoreMiniChart';

const BotIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="10" rx="2" />
    <circle cx="12" cy="5" r="2" />
    <path d="M12 7v4" />
    <line x1="8" y1="16" x2="8" y2="16" />
    <line x1="16" y1="16" x2="16" y2="16" />
  </svg>
);

const ChartIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10" />
    <line x1="12" y1="20" x2="12" y2="4" />
    <line x1="6" y1="20" x2="6" y2="14" />
  </svg>
);

const LockIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

const CheckIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

const ShieldIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <path d="M9 12l2 2 4-4" />
  </svg>
);

const MoonIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </svg>
);

const SunIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="5" />
    <line x1="12" y1="1" x2="12" y2="3" />
    <line x1="12" y1="21" x2="12" y2="23" />
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
    <line x1="1" y1="12" x2="3" y2="12" />
    <line x1="21" y1="12" x2="23" y2="12" />
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
  </svg>
);

const AlertTriangleIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
);

const TagIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" />
    <line x1="7" y1="7" x2="7.01" y2="7" />
  </svg>
);

const ExternalLinkIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
    <polyline points="15 3 21 3 21 9" />
    <line x1="10" y1="14" x2="21" y2="3" />
  </svg>
);

const ClockIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </svg>
);

const formatCurrency = (amount) => {
  if (amount >= 1000000) {
    return `$${(amount / 1000000).toFixed(1)}M MXN`;
  }
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(amount);
};

const initialDashboardData = {
  kpis: {
    diagnosticos_activos: 6,
    ajustes_solicitados: 54,
    ajustes_resueltos: 24,
    versiones_totales: 17,
    monto_en_revision: 15200000
  },
  distribucion_riesgo: {
    critico: 1,
    alto: 1,
    medio: 2,
    bajo: 2
  },
  proveedores: [
    { id: "PROV-001", nombre: "TechSoft Solutions SA de CV", rfc: "TSO150312AB1", proyecto: "Licencias ERP 2024", monto: 2500000, fase: "A3", progreso: 65, ajustes_sol: 8, ajustes_res: 5, dias_sin_act: 2, riesgo: "medio" },
    { id: "PROV-002", nombre: "Cloud Services MX", rfc: "CSM180924XY2", proyecto: "Infraestructura Cloud Q4", monto: 4200000, fase: "A6", progreso: 35, ajustes_sol: 12, ajustes_res: 3, dias_sin_act: 7, riesgo: "alto" },
    { id: "PROV-003", nombre: "Digital Marketing Pro", rfc: "DMP200115ZZ3", proyecto: "Campaña Digital 2024", monto: 850000, fase: "A7", progreso: 90, ajustes_sol: 4, ajustes_res: 4, dias_sin_act: 1, riesgo: "bajo" },
    { id: "PROV-004", nombre: "Consultoría Estratégica SA", rfc: "CES190507AA4", proyecto: "Asesoría Fiscal Especial", monto: 1800000, fase: "A6", progreso: 20, ajustes_sol: 15, ajustes_res: 2, dias_sin_act: 14, riesgo: "critico" },
    { id: "PROV-005", nombre: "Software Factory MX", rfc: "SFM170823BB5", proyecto: "Desarrollo App Móvil", monto: 3100000, fase: "A7", progreso: 85, ajustes_sol: 6, ajustes_res: 6, dias_sin_act: 0, riesgo: "bajo" },
    { id: "PROV-006", nombre: "Data Analytics Corp", rfc: "DAC210302CC6", proyecto: "BI Dashboard Enterprise", monto: 2750000, fase: "A3", progreso: 50, ajustes_sol: 9, ajustes_res: 4, dias_sin_act: 5, riesgo: "medio" }
  ]
};

function DurezzaDashboard() {
  const [dashboardData, setDashboardData] = useState(initialDashboardData);
  const [subagentes, setSubagentes] = useState([]);
  const [fases, setFases] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tipificacionResult, setTipificacionResult] = useState(null);
  const [riesgosResult, setRiesgosResult] = useState(null);
  const [showVersioning, setShowVersioning] = useState(false);
  const [selectedProyectoId, setSelectedProyectoId] = useState(null);
  const [showDocumentUpload, setShowDocumentUpload] = useState(false);
  const [docRefreshTrigger, setDocRefreshTrigger] = useState(0);
  const [estadisticas, setEstadisticas] = useState(null);
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('durezza-dark-mode');
      return saved === 'true';
    }
    return false;
  });

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('durezza-dark-mode', darkMode);
  }, [darkMode]);

  useEffect(() => {
    cargarDatos();
  }, []);

  async function cargarDatos() {
    setLoading(true);
    try {
      // Cargar datos principales - sin trailing slash para evitar redirects
      const [subRes, fasesRes, estadisticasRes] = await Promise.allSettled([
        api.get('/api/subagentes'),
        api.get('/api/fases'),
        api.get('/api/durezza/estadisticas')
      ]);

      // Handle responses defensively with null checks
      if ((subRes?.status === 'fulfilled')) {
        setSubagentes((subRes?.value?.subagentes) || []);
      } else {
        setSubagentes([]);
      }

      if ((fasesRes?.status === 'fulfilled')) {
        setFases((fasesRes?.value) || null);
      } else {
        setFases(null);
      }

      if ((estadisticasRes?.status === 'fulfilled')) {
        const statsData = estadisticasRes.value;
        setEstadisticas(statsData || null);

        // Always update dashboard to reflect backend state (even if empty) to remove fake data
        if (statsData) {
          setDashboardData(prev => ({
            ...prev,
            kpis: statsData.kpis || {
              diagnosticos_activos: 0,
              ajustes_solicitados: 0,
              ajustes_resueltos: 0,
              versiones_totales: 0,
              monto_en_revision: 0
            },
            proveedores: statsData.proyectos?.lista_dashboard || [],
            distribucion_riesgo: statsData.distribucion_riesgo || {
              critico: 0,
              alto: 0,
              medio: 0,
              bajo: 0
            }
          }));
        }
      } else {
        setEstadisticas(null);
      }

      // Load examples - these can fail without breaking the dashboard
      try {
        const ejemploRes = await api.get('/api/subagentes/ejemplo/tipificacion');
        if (ejemploRes) {
          setTipificacionResult(ejemploRes);
        }
      } catch (e) {
        console.warn('No se pudo cargar ejemplo tipificación:', (e?.message) || 'Error desconocido');
      }

      try {
        const riesgosRes = await api.get('/api/subagentes/ejemplo/riesgos-criticos');
        if (riesgosRes) {
          setRiesgosResult(riesgosRes);
        }
      } catch (e) {
        console.warn('No se pudo cargar ejemplo riesgos:', (e?.message) || 'Error desconocido');
      }

    } catch (err) {
      console.error('Error cargando datos:', err);
      setError((err?.message) || 'Error desconocido al cargar datos');
      // Set safe defaults on error
      setSubagentes([]);
      setFases(null);
      setEstadisticas(null);
    }
    setLoading(false);
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center transition-colors duration-300">
        <div className="text-center animate-fade-in">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-blue-200 dark:border-blue-800 rounded-full animate-pulse-glow border-t-blue-600 dark:border-t-blue-400 mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <ShieldIcon className="w-6 h-6 flex-shrink-0 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <p className="mt-6 text-slate-600 dark:text-slate-300 font-medium animate-fade-in">Preparando tu espacio de trabajo...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-50 to-blue-50 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800 transition-colors duration-300">
      <header className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-900"></div>
        <div className="absolute inset-0 opacity-30">
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="mesh" width="40" height="40" patternUnits="userSpaceOnUse">
                <circle cx="20" cy="20" r="1" fill="rgba(255,255,255,0.3)" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#mesh)" />
          </svg>
        </div>
        <div className="absolute inset-0 backdrop-blur-[1px]"></div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="animate-fade-in-up">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-gradient-to-br from-blue-400 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
                  <ShieldIcon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">REVISAR.IA</h1>
                  <p className="text-blue-200 text-sm sm:text-base">Tu aliado en la gestión fiscal de servicios intangibles</p>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 sm:gap-3">
              <a
                href={`/api/defense-file/${selectedProyectoId || 'demo-proyecto-001'}/download-complete`}
                download
                className="btn-ghost-premium text-white hover:bg-green-500/20 border border-green-400/50 hover:border-green-400 bg-green-500/10"
              >
                <span className="text-lg flex-shrink-0">📥</span>
                <span className="hidden sm:inline text-sm font-medium">Descargar Expediente</span>
              </a>
              <button
                onClick={() => {
                  setSelectedProyectoId('demo-proyecto-001');
                  setShowVersioning(true);
                }}
                className="btn-ghost-premium text-white hover:bg-white/10 border border-white/30 hover:border-white/50"
              >
                <span className="text-lg flex-shrink-0">📋</span>
                <span className="hidden sm:inline text-sm font-medium">Control de Versiones</span>
              </button>
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="btn-ghost-premium text-white hover:bg-white/10 border border-white/30 hover:border-white/50"
              >
                {darkMode ? (
                  <>
                    <SunIcon className="w-5 h-5 flex-shrink-0" />
                    <span className="hidden sm:inline text-sm font-medium">Modo Claro</span>
                  </>
                ) : (
                  <>
                    <MoonIcon className="w-5 h-5 flex-shrink-0" />
                    <span className="hidden sm:inline text-sm font-medium">Modo Oscuro</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-8">
        {/* New KPIs Section */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4 lg:gap-6 mb-6 sm:mb-8">
          <KPICardNew
            title="Diagnósticos Activos"
            value={dashboardData.kpis.diagnosticos_activos}
            icon="🔍"
            gradientFrom="#7C3AED"
            gradientTo="#9333EA"
            delay="0"
          />
          <KPICardNew
            title="Ajustes Solicitados"
            value={dashboardData.kpis.ajustes_solicitados}
            icon="📝"
            gradientFrom="#F59E0B"
            gradientTo="#D97706"
            delay="100"
          />
          <KPICardNew
            title="Ajustes Resueltos"
            value={dashboardData.kpis.ajustes_resueltos}
            subtitle={`${((dashboardData.kpis.ajustes_resueltos / dashboardData.kpis.ajustes_solicitados) * 100).toFixed(1)}%`}
            icon="✅"
            gradientFrom="#10B981"
            gradientTo="#059669"
            delay="200"
          />
          <KPICardNew
            title="Versiones Generadas"
            value={dashboardData.kpis.versiones_totales}
            icon="📋"
            gradientFrom="#3B82F6"
            gradientTo="#2563EB"
            delay="300"
          />
          <KPICardNew
            title="Monto en Revisión"
            value={formatCurrency(dashboardData.kpis.monto_en_revision)}
            icon="💰"
            gradientFrom="#5B21B6"
            gradientTo="#7C3AED"
            delay="400"
            isLarge
          />
        </div>

        {/* Risk Distribution Section */}
        <div className="glass-card-hover overflow-hidden animate-fade-in mb-6 sm:mb-8">
          <div className="h-1 bg-gradient-to-r from-red-500 via-amber-500 to-green-500"></div>
          <div className="bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-700 px-4 sm:px-6 py-4 border-b border-slate-200/50 dark:border-slate-700/50">
            <h2 className="text-base sm:text-lg font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
              <AlertTriangleIcon className="w-5 h-5 flex-shrink-0 text-amber-600 dark:text-amber-400" />
              Distribución de Riesgo
            </h2>
          </div>
          <div className="p-4 sm:p-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <RiskDistributionCard
                label="Crítico"
                count={dashboardData.distribucion_riesgo.critico}
                color="#EF4444"
                bgColor="bg-red-50 dark:bg-red-900/20"
                borderColor="border-red-200 dark:border-red-800"
              />
              <RiskDistributionCard
                label="Alto"
                count={dashboardData.distribucion_riesgo.alto}
                color="#F59E0B"
                bgColor="bg-amber-50 dark:bg-amber-900/20"
                borderColor="border-amber-200 dark:border-amber-800"
              />
              <RiskDistributionCard
                label="Medio"
                count={dashboardData.distribucion_riesgo.medio}
                color="#3B82F6"
                bgColor="bg-blue-50 dark:bg-blue-900/20"
                borderColor="border-blue-200 dark:border-blue-800"
              />
              <RiskDistributionCard
                label="Bajo"
                count={dashboardData.distribucion_riesgo.bajo}
                color="#10B981"
                bgColor="bg-green-50 dark:bg-green-900/20"
                borderColor="border-green-200 dark:border-green-800"
              />
            </div>
          </div>
        </div>

        {/* Proveedores Table Section */}
        <div className="glass-card-hover overflow-hidden animate-fade-in mb-6 sm:mb-8">
          <div className="h-1 bg-gradient-to-r from-violet-500 via-purple-500 to-indigo-500"></div>
          <div className="bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-700 px-4 sm:px-6 py-4 border-b border-slate-200/50 dark:border-slate-700/50">
            <h2 className="text-base sm:text-lg font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
              <BotIcon className="w-5 h-5 flex-shrink-0 text-purple-600 dark:text-purple-400" />
              Proveedores en Diagnóstico
              <span className="ml-auto text-sm font-normal text-slate-500 dark:text-slate-400">
                {dashboardData.proveedores.length} proveedores activos
              </span>
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 dark:bg-slate-800/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">Proveedor</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">Proyecto</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">Fase</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">Progreso</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">Ajustes</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">Días sin Act.</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">Riesgo</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">Expediente</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                {dashboardData.proveedores.map((proveedor) => (
                  <ProveedorRow key={proveedor.id} proveedor={proveedor} />
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="glass-card-hover overflow-hidden animate-fade-in mb-6 sm:mb-8">
          <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-blue-600 p-4 sm:p-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="text-white">
                <h2 className="text-lg sm:text-xl font-bold flex items-center gap-2">
                  <span className="text-2xl">🧠</span>
                  Sistema RAG Multi-Tenant Activo
                </h2>
                <p className="text-indigo-200 text-sm mt-1">
                  {estadisticas?.plantillas_rag?.total || 42} documentos de contexto configurados para {estadisticas?.agentes?.total || 8} agentes especializados
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <div className="bg-white/10 backdrop-blur rounded-lg px-4 py-2 text-center">
                  <div className="text-2xl font-bold text-white">{estadisticas?.agentes?.activos || 7}</div>
                  <div className="text-xs text-indigo-200">Agentes IA</div>
                </div>
                <div className="bg-white/10 backdrop-blur rounded-lg px-4 py-2 text-center">
                  <div className="text-2xl font-bold text-white">{estadisticas?.plantillas_rag?.total || 42}</div>
                  <div className="text-xs text-indigo-200">Plantillas RAG</div>
                </div>
                <div className="bg-white/10 backdrop-blur rounded-lg px-4 py-2 text-center">
                  <div className="text-2xl font-bold text-white">{estadisticas?.plantillas_rag?.docs_universales || 5}</div>
                  <div className="text-xs text-indigo-200">Docs Universales</div>
                </div>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {(estadisticas?.agentes?.lista || ['A1_ESTRATEGIA', 'A2_PMO', 'A3_FISCAL', 'A4_LEGAL', 'A5_FINANZAS', 'A6_PROVEEDOR', 'A7_DEFENSA']).filter(a => a !== 'KNOWLEDGE_BASE').map(agente => (
                <span key={agente} className="px-2 py-1 bg-white/20 text-white text-xs rounded-full">
                  {agente.replace('_', ' ')}
                </span>
              ))}
              <span className="px-2 py-1 bg-yellow-400/30 text-yellow-100 text-xs rounded-full border border-yellow-400/50">
                KNOWLEDGE_BASE
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <div className="lg:col-span-2">
            <div className="glass-card-hover overflow-hidden animate-fade-in">
              <div className="bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-700 px-4 sm:px-6 py-4 border-b border-slate-200/50 dark:border-slate-700/50">
                <h2 className="text-base sm:text-lg font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                  <ChartIcon className="w-5 h-5 flex-shrink-0 text-blue-600 dark:text-blue-400" />
                  Timeline de Fases con Candados
                </h2>
              </div>
              <div className="p-3 sm:p-6 overflow-x-auto">
                {estadisticas?.hay_datos && estadisticas?.proyectos?.fase_actual ? (
                  <TimelineFases
                    faseActual={estadisticas.proyectos.fase_actual}
                    fasesCompletadas={estadisticas.proyectos.fases_completadas || []}
                  />
                ) : (
                  <EmptyStatePanel
                    title="No hay proyectos activos"
                    message="Crea tu primer proyecto para ver el progreso de las fases"
                    icon={ChartIcon}
                  />
                )}
              </div>
            </div>
          </div>

          <div className="glass-card-hover overflow-hidden animate-fade-in">
            <div className="bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-700 px-4 sm:px-6 py-4 border-b border-slate-200/50 dark:border-slate-700/50">
              <h2 className="text-base sm:text-lg font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                <BotIcon className="w-5 h-5 flex-shrink-0 text-purple-600 dark:text-purple-400" />
                <span className="truncate">Especialistas del Equipo</span>
              </h2>
            </div>
            <div className="p-3 space-y-2 max-h-80 overflow-y-auto">
              {subagentes.map((sub, index) => (
                <SubagentCard key={sub.id} subagent={sub} index={index} />
              ))}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <div className="glass-card-hover overflow-hidden animate-fade-in">
            <div className="h-1 bg-gradient-to-r from-blue-500 via-cyan-500 to-blue-500"></div>
            <div className="bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/30 dark:to-cyan-900/30 px-4 sm:px-6 py-4 border-b border-slate-200/50 dark:border-slate-700/50">
              <h2 className="text-base sm:text-lg font-semibold text-blue-800 dark:text-blue-200 flex items-center gap-2">
                <TagIcon className="w-5 h-5 flex-shrink-0" />
                <span className="truncate">Ejemplo: Tipificación de Proyecto</span>
              </h2>
            </div>
            <div className="p-4 sm:p-6">
              {tipificacionResult && (
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Proyecto:</p>
                    <p className="font-medium text-slate-800 dark:text-slate-100">{tipificacionResult.input?.proyecto?.nombre}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">Tipología Asignada</p>
                      <span className="inline-block px-3 py-1.5 bg-gradient-to-r from-blue-100 to-cyan-100 dark:from-blue-900/50 dark:to-cyan-900/50 text-blue-800 dark:text-blue-200 rounded-lg text-sm font-medium border border-blue-200 dark:border-blue-700">
                        {tipificacionResult.resultado?.tipologia_asignada?.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">Confianza</p>
                      <span className={`inline-block px-3 py-1.5 rounded-lg text-sm font-medium ${tipificacionResult.resultado?.confianza_clasificacion === 'ALTA'
                        ? 'bg-gradient-to-r from-emerald-100 to-green-100 dark:from-emerald-900/50 dark:to-green-900/50 text-emerald-800 dark:text-emerald-200 border border-emerald-200 dark:border-emerald-700'
                        : tipificacionResult.resultado?.confianza_clasificacion === 'MEDIA'
                          ? 'bg-gradient-to-r from-amber-100 to-yellow-100 dark:from-amber-900/50 dark:to-yellow-900/50 text-amber-800 dark:text-amber-200 border border-amber-200 dark:border-amber-700'
                          : 'bg-gradient-to-r from-rose-100 to-red-100 dark:from-rose-900/50 dark:to-red-900/50 text-rose-800 dark:text-rose-200 border border-rose-200 dark:border-rose-700'
                        }`}>
                        {tipificacionResult.resultado?.confianza_clasificacion}
                      </span>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">Palabras Clave Detectadas</p>
                    <div className="flex flex-wrap gap-2">
                      {tipificacionResult.resultado?.palabras_clave_detectadas?.map((kw, i) => (
                        <span key={i} className="px-2.5 py-1 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-full text-xs font-medium border border-slate-200 dark:border-slate-600 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors cursor-default">
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="glass-card-hover overflow-hidden animate-fade-in">
            <div className="h-1 bg-gradient-to-r from-rose-500 via-red-500 to-rose-500"></div>
            <div className="bg-gradient-to-r from-rose-50 to-red-50 dark:from-rose-900/30 dark:to-red-900/30 px-4 sm:px-6 py-4 border-b border-slate-200/50 dark:border-slate-700/50">
              <h2 className="text-base sm:text-lg font-semibold text-rose-800 dark:text-rose-200 flex items-center gap-2">
                <AlertTriangleIcon className="w-5 h-5 flex-shrink-0" />
                <span className="truncate">Ejemplo: Detección de Riesgos Críticos</span>
              </h2>
            </div>
            <div className="p-4 sm:p-6">
              {riesgosResult && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between flex-wrap gap-4">
                    <div>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">Nivel Global</p>
                      <span className={`inline-block px-4 py-2 rounded-xl text-sm font-bold shadow-lg ${riesgosResult.resultado?.nivel_riesgo_global === 'CRITICO'
                        ? 'bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-red-500/30'
                        : riesgosResult.resultado?.nivel_riesgo_global === 'ALTO'
                          ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-orange-500/30'
                          : 'bg-gradient-to-r from-yellow-400 to-amber-400 text-slate-900 shadow-yellow-500/30'
                        }`}>
                        {riesgosResult.resultado?.nivel_riesgo_global}
                      </span>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">Puede Continuar</p>
                      <span className={`inline-block px-4 py-2 rounded-xl text-sm font-medium ${riesgosResult.resultado?.puede_continuar
                        ? 'bg-gradient-to-r from-emerald-100 to-green-100 dark:from-emerald-900/50 dark:to-green-900/50 text-emerald-800 dark:text-emerald-200 border border-emerald-200 dark:border-emerald-700'
                        : 'bg-gradient-to-r from-rose-100 to-red-100 dark:from-rose-900/50 dark:to-red-900/50 text-rose-800 dark:text-rose-200 border border-rose-200 dark:border-rose-700'
                        }`}>
                        {riesgosResult.resultado?.puede_continuar ? 'SI' : 'NO - BLOQUEADO'}
                      </span>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-3">
                      Alertas Detectadas ({riesgosResult.resultado?.alertas_detectadas?.length})
                    </p>
                    <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                      {riesgosResult.resultado?.alertas_detectadas?.slice(0, 4).map((alerta, i) => (
                        <AlertCard key={i} alerta={alerta} />
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="glass-card-hover overflow-hidden animate-fade-in">
          <div className="h-1 bg-gradient-to-r from-violet-500 via-purple-500 to-indigo-500"></div>
          <div className="bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-700 px-4 sm:px-6 py-4 border-b border-slate-200/50 dark:border-slate-700/50">
            <h2 className="text-base sm:text-lg font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
              <ShieldIcon className="w-5 h-5 flex-shrink-0 text-purple-600 dark:text-purple-400" />
              Análisis de Riesgo por Pilar
            </h2>
          </div>
          <div className="p-4 sm:p-6">
            <RiskScoreDisplay
              razonNegocios={5}
              beneficioEconomico={8}
              materialidad={3}
              trazabilidad={6}
            />
          </div>
        </div>
      </main>

      {showVersioning && (
        <VersioningPanel
          proyectoId={selectedProyectoId}
          onClose={() => setShowVersioning(false)}
        />
      )}

      {selectedProyectoId && (
        <div className="glass-card-hover mt-6 overflow-hidden animate-fade-in">
          <div className="h-1 bg-gradient-to-r from-blue-500 via-cyan-500 to-teal-500"></div>
          <div className="bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-700 px-4 sm:px-6 py-4 border-b border-slate-200/50 dark:border-slate-700/50 flex justify-between items-center">
            <h2 className="text-base sm:text-lg font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
              <span className="text-xl">📁</span>
              Documentos del Proyecto
            </h2>
            <button
              onClick={() => setShowDocumentUpload(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
            >
              <span>+</span> Cargar Documento
            </button>
          </div>
          <div className="p-4 sm:p-6">
            <ListaDocumentos
              proyectoId={selectedProyectoId}
              faseActual="F0"
              refreshTrigger={docRefreshTrigger}
            />
          </div>
        </div>
      )}

      <Modal isOpen={showDocumentUpload} onClose={() => setShowDocumentUpload(false)}>
        <CargaDocumentos
          proyectoId={selectedProyectoId}
          faseActual="F0"
          onDocumentoCargado={(doc) => {
            setShowDocumentUpload(false);
            setDocRefreshTrigger(prev => prev + 1);
          }}
          onClose={() => setShowDocumentUpload(false)}
        />
      </Modal>
    </div>
  );
}

function KPICard({ title, value, subtitle, icon: Icon, gradient, delay, valueColor }) {
  return (
    <div
      className="group glass-card-hover p-5 sm:p-6 animate-fade-in-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 font-medium truncate">{title}</p>
          <p className={`text-2xl sm:text-3xl font-bold mt-2 ${valueColor || 'text-slate-900 dark:text-white'}`}>{value}</p>
        </div>
        <div className={`icon-container-lg bg-gradient-to-br ${gradient} shadow-lg group-hover:shadow-xl transition-all duration-300 flex-shrink-0`}>
          <Icon className="w-6 h-6 flex-shrink-0 text-white" />
        </div>
      </div>
      <p className="text-xs text-slate-400 dark:text-slate-500 mt-3 line-clamp-2">{subtitle}</p>
    </div>
  );
}

function SubagentCard({ subagent, index }) {
  return (
    <div
      className="glass-card-hover p-3 sm:p-4 flex items-center justify-between gap-3 transition-all duration-300 cursor-default animate-fade-in"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <div className="relative flex-shrink-0">
          <div className={`w-2.5 h-2.5 rounded-full ${subagent.puede_bloquear ? 'bg-rose-500' : 'bg-emerald-500'}`}></div>
          <div className={`absolute inset-0 w-2.5 h-2.5 rounded-full ${subagent.puede_bloquear ? 'bg-rose-500' : 'bg-emerald-500'} animate-pulse-ring`}></div>
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-medium text-slate-800 dark:text-slate-100 text-sm truncate">{subagent.id}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{subagent.fases.join(', ')}</p>
        </div>
      </div>
      {subagent.puede_bloquear ? (
        <span className="text-xs bg-rose-100 dark:bg-rose-900/50 text-rose-700 dark:text-rose-300 px-2.5 py-1 rounded-lg font-medium border border-rose-200 dark:border-rose-800 flex-shrink-0 whitespace-nowrap">
          Bloquea
        </span>
      ) : (
        <span className="text-xs bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 px-2.5 py-1 rounded-lg font-medium border border-emerald-200 dark:border-emerald-800 flex-shrink-0 whitespace-nowrap">
          Activo
        </span>
      )}
    </div>
  );
}

function AlertCard({ alerta }) {
  const severityConfig = {
    CRITICA: {
      bg: 'bg-gradient-to-r from-rose-50 to-red-50 dark:from-rose-900/30 dark:to-red-900/30',
      border: 'border-l-4 border-rose-500',
      badge: 'bg-rose-200 dark:bg-rose-800 text-rose-800 dark:text-rose-200'
    },
    ALTA: {
      bg: 'bg-gradient-to-r from-orange-50 to-amber-50 dark:from-orange-900/30 dark:to-amber-900/30',
      border: 'border-l-4 border-orange-500',
      badge: 'bg-orange-200 dark:bg-orange-800 text-orange-800 dark:text-orange-200'
    },
    MEDIA: {
      bg: 'bg-gradient-to-r from-yellow-50 to-amber-50 dark:from-yellow-900/30 dark:to-amber-900/30',
      border: 'border-l-4 border-yellow-500',
      badge: 'bg-yellow-200 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-200'
    }
  };

  const config = severityConfig[alerta.severidad] || severityConfig.MEDIA;

  return (
    <div className={`p-3 rounded-lg text-xs ${config.bg} ${config.border} transition-all duration-200 hover:shadow-md`}>
      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
        <span className="font-semibold text-slate-800 dark:text-slate-100">{alerta.tipo_riesgo}</span>
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${config.badge}`}>
          {alerta.severidad}
        </span>
        {alerta.bloquea_avance && (
          <span className="px-2 py-0.5 bg-gradient-to-r from-red-600 to-rose-600 text-white rounded-full text-xs font-bold flex items-center gap-1">
            <LockIcon className="w-3 h-3" />
            BLOQUEA
          </span>
        )}
      </div>
      <p className="text-slate-600 dark:text-slate-300 leading-relaxed">{alerta.descripcion}</p>
    </div>
  );
}

function TimelineFases({ faseActual, fasesCompletadas = [] }) {
  const fases = [
    { id: 'F0', nombre: 'Aprobación BEE', candado: false },
    { id: 'F1', nombre: 'Pre-contratación', candado: false },
    { id: 'F2', nombre: 'Validación inicio', candado: true },
    { id: 'F3', nombre: 'Ejecución inicial', candado: false },
    { id: 'F4', nombre: 'Revisión iterativa', candado: false },
    { id: 'F5', nombre: 'Entrega final', candado: false },
    { id: 'F6', nombre: 'VBC Fiscal/Legal', candado: true },
    { id: 'F7', nombre: 'Auditoría interna', candado: false },
    { id: 'F8', nombre: 'CFDI y pago', candado: true },
    { id: 'F9', nombre: 'Post-implementación', candado: false }
  ];

  function getEstadoFase(faseId) {
    if (fasesCompletadas.includes(faseId)) return 'completada';
    if (faseId === faseActual) return 'actual';
    const indexActual = fases.findIndex(f => f.id === faseActual);
    const indexFase = fases.findIndex(f => f.id === faseId);
    if (indexFase < indexActual) return 'completada';
    return 'pendiente';
  }

  const indexActual = fases.findIndex(f => f.id === faseActual);
  const progreso = (indexActual / (fases.length - 1)) * 100;

  return (
    <div className="relative min-w-[800px] lg:min-w-0">
      <div className="absolute top-6 left-0 right-0 h-2 bg-slate-200 dark:bg-slate-700 rounded-full" />
      <div
        className="absolute top-6 left-0 h-2 bg-gradient-to-r from-blue-500 via-indigo-500 to-violet-500 rounded-full transition-all duration-1000 ease-out shadow-lg shadow-blue-500/30"
        style={{ width: `${progreso}%` }}
      />

      <div className="relative flex justify-between">
        {fases.map((fase, index) => {
          const estado = getEstadoFase(fase.id);
          return (
            <div key={fase.id} className="flex flex-col items-center group" style={{ width: '10%' }}>
              <div className={`
                w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold
                transition-all duration-300 relative z-10 border-4
                ${estado === 'completada'
                  ? 'bg-gradient-to-br from-emerald-400 to-green-500 text-white border-emerald-300 dark:border-emerald-600 shadow-lg shadow-emerald-500/30'
                  : estado === 'actual'
                    ? 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white border-blue-300 dark:border-blue-600 ring-4 ring-blue-200 dark:ring-blue-900 shadow-xl shadow-blue-500/40 scale-110'
                    : 'bg-slate-100 dark:bg-slate-700 text-slate-400 dark:text-slate-500 border-slate-200 dark:border-slate-600'}
                ${fase.candado && estado !== 'completada' ? 'ring-2 ring-rose-300 dark:ring-rose-700' : ''}
                group-hover:scale-110
              `}>
                {fase.candado && estado !== 'completada' ? (
                  <LockIcon className="w-5 h-5 text-rose-500 dark:text-rose-400" />
                ) : estado === 'completada' ? (
                  <CheckIcon className="w-5 h-5" />
                ) : (
                  <span className="text-xs">{fase.id}</span>
                )}
              </div>
              <div className="mt-3 text-xs text-center text-slate-600 dark:text-slate-400 leading-tight font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-200 w-20">
                {fase.nombre}
              </div>
              {fase.candado && (
                <div className="text-xs text-rose-500 dark:text-rose-400 mt-1 font-semibold flex items-center gap-1">
                  <LockIcon className="w-3 h-3" />
                  Candado
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function EmptyStatePanel({ title, message, icon: Icon, actionLabel, onAction }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center mb-4">
        {Icon ? (
          <Icon className="w-8 h-8 text-slate-400 dark:text-slate-500" />
        ) : (
          <ShieldIcon className="w-8 h-8 text-slate-400 dark:text-slate-500" />
        )}
      </div>
      <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-300 mb-2">{title}</h3>
      <p className="text-sm text-slate-500 dark:text-slate-400 max-w-sm mb-4">{message}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-lg text-sm font-medium hover:from-blue-600 hover:to-indigo-700 transition-all shadow-lg shadow-blue-500/30"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}

function RiskScoreDisplay({ razonNegocios, beneficioEconomico, materialidad, trazabilidad }) {
  const total = razonNegocios + beneficioEconomico + materialidad + trazabilidad;

  const pilares = [
    { nombre: 'Razón de Negocios', valor: razonNegocios, max: 25, gradient: 'from-blue-500 to-cyan-500', icon: '🎯', descripcion: 'Art. 5-A CFF' },
    { nombre: 'Beneficio Económico', valor: beneficioEconomico, max: 25, gradient: 'from-emerald-500 to-green-500', icon: '📈', descripcion: 'ROI documentado' },
    { nombre: 'Materialidad', valor: materialidad, max: 25, gradient: 'from-violet-500 to-purple-500', icon: '📦', descripcion: 'Art. 69-B CFF' },
    { nombre: 'Trazabilidad', valor: trazabilidad, max: 25, gradient: 'from-orange-500 to-amber-500', icon: '🔗', descripcion: 'NOM-151' }
  ];

  const getRiskLevel = (score) => {
    if (score < 30) return { label: 'BAJO', color: 'text-emerald-600 dark:text-emerald-400', stroke: 'stroke-emerald-500', bg: 'bg-emerald-100 dark:bg-emerald-900/50' };
    if (score < 50) return { label: 'MODERADO', color: 'text-amber-600 dark:text-amber-400', stroke: 'stroke-amber-500', bg: 'bg-amber-100 dark:bg-amber-900/50' };
    if (score < 70) return { label: 'ALTO', color: 'text-orange-600 dark:text-orange-400', stroke: 'stroke-orange-500', bg: 'bg-orange-100 dark:bg-orange-900/50' };
    return { label: 'CRITICO', color: 'text-rose-600 dark:text-rose-400', stroke: 'stroke-rose-500', bg: 'bg-rose-100 dark:bg-rose-900/50' };
  };

  const getPilarLevel = (valor, max) => {
    const porcentaje = (valor / max) * 100;
    if (porcentaje < 40) return { label: 'Bajo', color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-100 dark:bg-emerald-900/50' };
    if (porcentaje < 60) return { label: 'Medio', color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-100 dark:bg-amber-900/50' };
    if (porcentaje < 80) return { label: 'Alto', color: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-100 dark:bg-orange-900/50' };
    return { label: 'Crítico', color: 'text-rose-600 dark:text-rose-400', bg: 'bg-rose-100 dark:bg-rose-900/50' };
  };

  const riskLevel = getRiskLevel(total);
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (total / 100) * circumference;

  return (
    <div className="flex flex-col lg:flex-row gap-6 sm:gap-8 items-center justify-center lg:justify-start">
      <div className="flex-shrink-0 text-center">
        <div className="relative w-32 sm:w-40 h-32 sm:h-40">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
            <circle
              cx="60"
              cy="60"
              r="54"
              stroke="currentColor"
              strokeWidth="8"
              fill="none"
              className="text-slate-200 dark:text-slate-700"
            />
            <circle
              cx="60"
              cy="60"
              r="54"
              strokeWidth="8"
              fill="none"
              strokeLinecap="round"
              className={`${riskLevel.stroke} transition-all duration-1000 ease-out`}
              style={{
                strokeDasharray: circumference,
                strokeDashoffset: offset
              }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-4xl font-bold ${riskLevel.color}`}>{total}</span>
            <span className="text-sm text-slate-500 dark:text-slate-400 font-medium">/100</span>
          </div>
        </div>
        <div className={`mt-3 inline-block px-4 py-1.5 rounded-full ${riskLevel.bg} ${riskLevel.color} font-bold text-sm`}>
          {riskLevel.label}
        </div>
      </div>

      <div className="flex-1 w-full space-y-4">
        {pilares.map((pilar, i) => {
          const pilarLevel = getPilarLevel(pilar.valor, pilar.max);
          return (
            <div key={i} className="group">
              <div className="flex justify-between items-center text-sm mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{pilar.icon}</span>
                  <div>
                    <span className="text-slate-600 dark:text-slate-300 font-medium group-hover:text-slate-900 dark:group-hover:text-white transition-colors">{pilar.nombre}</span>
                    <span className="text-xs text-slate-400 dark:text-slate-500 ml-2 hidden sm:inline">{pilar.descripcion}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-800 dark:text-slate-100">{pilar.valor}/{pilar.max}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${pilarLevel.bg} ${pilarLevel.color} font-medium`}>
                    {pilarLevel.label}
                  </span>
                </div>
              </div>
              <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden shadow-inner">
                <div
                  className={`h-full bg-gradient-to-r ${pilar.gradient} rounded-full transition-all duration-1000 ease-out shadow-lg`}
                  style={{ width: `${(pilar.valor / pilar.max) * 100}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function KPICardNew({ title, value, subtitle, icon, gradientFrom, gradientTo, delay, isLarge }) {
  return (
    <div
      className={`group glass-card-hover p-4 sm:p-5 animate-fade-in-up ${isLarge ? 'col-span-2 lg:col-span-1' : ''}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 font-medium truncate">{title}</p>
          <p className={`${isLarge ? 'text-xl sm:text-2xl' : 'text-2xl sm:text-3xl'} font-bold mt-2 text-slate-900 dark:text-white`}>{value}</p>
          {subtitle && (
            <p className="text-sm font-medium text-slate-600 dark:text-slate-300 mt-1">{subtitle}</p>
          )}
        </div>
        <div
          className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center text-xl sm:text-2xl shadow-lg group-hover:shadow-xl transition-all duration-300 flex-shrink-0"
          style={{ background: `linear-gradient(135deg, ${gradientFrom}, ${gradientTo})` }}
        >
          {icon}
        </div>
      </div>
    </div>
  );
}

function RiskDistributionCard({ label, count, color, bgColor, borderColor }) {
  return (
    <div className={`${bgColor} ${borderColor} border-2 rounded-xl p-4 text-center transition-all duration-300 hover:shadow-lg hover:scale-105`}>
      <div
        className="text-3xl sm:text-4xl font-bold mb-1"
        style={{ color }}
      >
        {count}
      </div>
      <div className="text-sm font-medium text-slate-600 dark:text-slate-300">{label}</div>
    </div>
  );
}

function ProveedorRow({ proveedor }) {
  const riesgoConfig = {
    critico: {
      bg: 'bg-red-100 dark:bg-red-900/50',
      text: 'text-red-700 dark:text-red-300',
      border: 'border-red-200 dark:border-red-800',
      label: 'Crítico'
    },
    alto: {
      bg: 'bg-amber-100 dark:bg-amber-900/50',
      text: 'text-amber-700 dark:text-amber-300',
      border: 'border-amber-200 dark:border-amber-800',
      label: 'Alto'
    },
    medio: {
      bg: 'bg-blue-100 dark:bg-blue-900/50',
      text: 'text-blue-700 dark:text-blue-300',
      border: 'border-blue-200 dark:border-blue-800',
      label: 'Medio'
    },
    bajo: {
      bg: 'bg-green-100 dark:bg-green-900/50',
      text: 'text-green-700 dark:text-green-300',
      border: 'border-green-200 dark:border-green-800',
      label: 'Bajo'
    }
  };

  const faseConfig = {
    A3: { bg: 'bg-violet-100 dark:bg-violet-900/50', text: 'text-violet-700 dark:text-violet-300' },
    A6: { bg: 'bg-blue-100 dark:bg-blue-900/50', text: 'text-blue-700 dark:text-blue-300' },
    A7: { bg: 'bg-emerald-100 dark:bg-emerald-900/50', text: 'text-emerald-700 dark:text-emerald-300' }
  };

  const riesgo = riesgoConfig[proveedor.riesgo] || riesgoConfig.medio;
  const fase = faseConfig[proveedor.fase] || faseConfig.A3;

  return (
    <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
      <td className="px-4 py-4">
        <div className="flex flex-col">
          <span className="font-medium text-slate-800 dark:text-slate-100 text-sm">{proveedor.nombre}</span>
          <span className="text-xs text-slate-500 dark:text-slate-400">{proveedor.rfc}</span>
        </div>
      </td>
      <td className="px-4 py-4">
        <div className="flex flex-col">
          <span className="font-medium text-slate-700 dark:text-slate-200 text-sm">{proveedor.proyecto}</span>
          <span className="text-xs text-slate-500 dark:text-slate-400">{formatCurrency(proveedor.monto)}</span>
        </div>
      </td>
      <td className="px-4 py-4 text-center">
        <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${fase.bg} ${fase.text}`}>
          {proveedor.fase}
        </span>
      </td>
      <td className="px-4 py-4">
        <div className="flex items-center gap-2 min-w-[120px]">
          <div className="flex-1 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-500"
              style={{ width: `${proveedor.progreso}%` }}
            />
          </div>
          <span className="text-xs font-medium text-slate-600 dark:text-slate-400 w-8">{proveedor.progreso}%</span>
        </div>
      </td>
      <td className="px-4 py-4 text-center">
        <div className="flex flex-col items-center">
          <span className="text-sm font-medium text-slate-800 dark:text-slate-100">
            {proveedor.ajustes_res}/{proveedor.ajustes_sol}
          </span>
          <span className="text-xs text-slate-500 dark:text-slate-400">resueltos</span>
        </div>
      </td>
      <td className="px-4 py-4 text-center">
        <div className={`flex items-center justify-center gap-1 ${proveedor.dias_sin_act > 7 ? 'text-red-600 dark:text-red-400' : proveedor.dias_sin_act > 3 ? 'text-amber-600 dark:text-amber-400' : 'text-slate-600 dark:text-slate-400'}`}>
          <ClockIcon className="w-4 h-4" />
          <span className="text-sm font-medium">{proveedor.dias_sin_act}</span>
        </div>
      </td>
      <td className="px-4 py-4 text-center">
        <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold border ${riesgo.bg} ${riesgo.text} ${riesgo.border}`}>
          {riesgo.label}
        </span>
      </td>
      <td className="px-4 py-4 text-center">
        <a
          href={`https://pcloud.com/defense/${proveedor.id}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 px-3 py-1.5 bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 rounded-lg text-xs font-medium hover:bg-indigo-200 dark:hover:bg-indigo-800/50 transition-colors"
        >
          <ExternalLinkIcon className="w-3 h-3" />
          pCloud
        </a>
      </td>
    </tr>
  );
}

export default DurezzaDashboard;
export { ProjectActions };
