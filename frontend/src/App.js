import React, { useState, useEffect, Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, Link, Navigate } from "react-router-dom";
import axios from "axios";
import "@/App.css";
import ProjectForm from "./ProjectForm";
import LoginPage from "./pages/LoginPage";
import LandingPage from "./pages/LandingPage";
import RegisterPage from "./pages/RegisterPage";
import AdminPage from "./pages/AdminPage";
import AdminDocumentacion from "./pages/AdminDocumentacion";
import MetricsDashboard from "./components/MetricsDashboard";
import CostsDashboard from "./components/CostsDashboard";
import ListaEmpresas from "./components/empresa/ListaEmpresas";
import OnboardingEmpresa from "./components/empresa/OnboardingEmpresa";
import ConfiguracionEmpresa from "./components/empresa/ConfiguracionEmpresa";
import { AuthProvider, useAuth } from "./context/AuthContext";
import VersionHistoryTimeline from "./components/VersionHistoryTimeline";
import ChatbotArchivo from "./components/ChatbotArchivoRefactored";
import BibliotecaChat from "./components/BibliotecaChat";
import EstadoAcervo from "./components/EstadoAcervo";
import DisenarIA from "./components/DisenarIA";
import AgentChecklist from "./components/AgentChecklist";
import TemplatesPage from "./pages/TemplatesPage";
import ProveedoresPage from "./pages/ProveedoresPage";
import AdminClientes from "./components/AdminClientes";
import Footer from "./components/Footer";
import SupportChatWidget from "./components/SupportChatWidget";
import FacturarIAWidget from "./components/FacturarIAWidget";
import KnowledgeRepository from "./components/KnowledgeRepository";
import DefenseFileDownload from "./components/DefenseFileDownload";
import UsageDashboard from "./components/UsageDashboard";
import AgentsDashboard from "./components/agents/AgentsDashboard";

const DurezzaDashboard = lazy(() => import("./components/DurezzaDashboard"));

const LoadingFallback = () => (
  <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center" role="status" aria-label="Cargando contenido">
    <div className="text-center">
      <div className="w-16 h-16 border-4 border-blue-200 rounded-full animate-spin border-t-blue-600 mx-auto" aria-hidden="true"></div>
      <p className="mt-6 text-slate-600 font-medium">Cargando...</p>
    </div>
  </div>
);

const api = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL 
    ? `${process.env.REACT_APP_BACKEND_URL}/api`
    : '/api',
  headers: {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
  }
});

api.interceptors.request.use(config => {
  config.params = { ...config.params, _t: Date.now() };
  
  const authEndpoints = ['/auth/login', '/auth/register', '/auth/otp/request-code', '/auth/otp/verify-code'];
  const isAuthEndpoint = authEndpoints.some(endpoint => config.url?.includes(endpoint));
  
  if (!isAuthEndpoint) {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.empresa_id) {
          config.headers['X-Empresa-ID'] = payload.empresa_id;
        }
      } catch (e) {
        console.warn('No se pudo extraer empresa_id del token');
      }
    }
  }
  const storedEmpresaId = localStorage.getItem('empresa_id');
  if (!config.headers['X-Empresa-ID'] && storedEmpresaId) {
    config.headers['X-Empresa-ID'] = storedEmpresaId;
  }
  return config;
});

const formatMonto = (amount) => {
  if (!amount || amount === 0) return "$0";
  const millions = amount / 1000000;
  if (millions >= 1) {
    return `$${millions.toFixed(2)}M`;
  }
  const thousands = amount / 1000;
  if (thousands >= 1) {
    return `$${thousands.toFixed(0)}K`;
  }
  return `$${amount.toLocaleString('es-MX')}`;
};

const formatMontoTotal = (amount) => {
  if (!amount || amount === 0) return "$0";
  const millions = amount / 1000000;
  return `$${millions.toFixed(1)}M`;
};

const getStatusColor = (status) => {
  switch (status?.toUpperCase()) {
    case 'APPROVED':
      return 'bg-green-500';
    case 'IN_REVIEW':
      return 'bg-yellow-500';
    case 'REJECTED':
      return 'bg-red-500';
    default:
      return 'bg-gray-400';
  }
};

const getStatusLabel = (status) => {
  switch (status?.toUpperCase()) {
    case 'APPROVED':
      return 'Aprobado';
    case 'IN_REVIEW':
      return 'En Revisión';
    case 'REJECTED':
      return 'Rechazado';
    default:
      return status || 'Pendiente';
  }
};

const getDecisionColor = (decision) => {
  switch (decision?.toLowerCase()) {
    case 'approve':
    case 'approved':
      return {
        bg: 'bg-green-100',
        text: 'text-green-700',
        border: 'border-green-500',
        dot: 'bg-green-500'
      };
    case 'reject':
    case 'rejected':
      return {
        bg: 'bg-red-100',
        text: 'text-red-700',
        border: 'border-red-500',
        dot: 'bg-red-500'
      };
    case 'request_adjustment':
    case 'request_adjustments':
      return {
        bg: 'bg-amber-100',
        text: 'text-amber-700',
        border: 'border-amber-500',
        dot: 'bg-amber-500'
      };
    case 'abstain':
      return {
        bg: 'bg-gray-100',
        text: 'text-gray-700',
        border: 'border-gray-400',
        dot: 'bg-gray-400'
      };
    default:
      return {
        bg: 'bg-blue-100',
        text: 'text-blue-700',
        border: 'border-blue-400',
        dot: 'bg-blue-400'
      };
  }
};

const getDecisionLabel = (decision) => {
  switch (decision?.toLowerCase()) {
    case 'approve':
    case 'approved':
      return 'Aprobado';
    case 'reject':
    case 'rejected':
      return 'Rechazado';
    case 'request_adjustment':
    case 'request_adjustments':
      return 'Requiere Ajustes';
    case 'abstain':
      return 'Abstención';
    default:
      return decision || 'Pendiente';
  }
};

const getStageLabel = (stage) => {
  const stages = {
    'E1_ESTRATEGIA': 'Estrategia',
    'E2_FISCAL': 'Fiscal',
    'E3_FINANZAS': 'Finanzas',
    'E4_LEGAL': 'Legal',
    'E5_APROBADO': 'Aprobación Final',
    'E5_PMO': 'Consolidación PMO',
    'intake': 'Recepción',
    'fiscal_review': 'Revisión Fiscal',
    'finance_review': 'Revisión Financiera',
    'pmo_consolidation': 'Consolidación PMO',
    'sponsor_approval': 'Aprobación Sponsor',
    'completed': 'Completado'
  };
  return stages[stage] || stage || 'Sin etapa';
};

const getStageNumber = (stage) => {
  const stageMap = {
    'E1_ESTRATEGIA': 1,
    'E2_FISCAL': 2,
    'E3_FINANZAS': 3,
    'E4_LEGAL': 4,
    'E5_APROBADO': 5,
    'E5_PMO': 5,
    'intake': 1,
    'fiscal_review': 2,
    'finance_review': 3,
    'pmo_consolidation': 4,
    'sponsor_approval': 5,
    'completed': 5
  };
  return stageMap[stage] || 0;
};

const AGENT_INFO = {
  'A1_SPONSOR': {
    name: 'María Rodríguez',
    role: 'Dirección Estratégica',
    color: 'purple',
    initial: 'M',
    bgColor: 'bg-purple-100',
    textColor: 'text-purple-600'
  },
  'A2_PMO': {
    name: 'Carlos Mendoza',
    role: 'PMO',
    color: 'blue',
    initial: 'C',
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-600'
  },
  'A3_FISCAL': {
    name: 'Laura Sánchez',
    role: 'Fiscal',
    color: 'green',
    initial: 'L',
    bgColor: 'bg-green-100',
    textColor: 'text-green-600'
  },
  'A5_FINANZAS': {
    name: 'Roberto Torres',
    role: 'Finanzas',
    color: 'amber',
    initial: 'R',
    bgColor: 'bg-amber-100',
    textColor: 'text-amber-600'
  },
  'LEGAL': {
    name: 'Equipo Legal',
    role: 'Legal',
    color: 'indigo',
    initial: 'EL',
    bgColor: 'bg-indigo-100',
    textColor: 'text-indigo-600'
  },
  'SYSTEM': {
    name: 'Sistema',
    role: 'Sistema Revisar.IA',
    color: 'gray',
    initial: 'S',
    bgColor: 'bg-gray-100',
    textColor: 'text-gray-600'
  }
};

const getAgentInfo = (agentId) => {
  return AGENT_INFO[agentId] || {
    name: agentId,
    role: 'Agente',
    color: 'gray',
    initial: agentId?.charAt(0) || '?',
    bgColor: 'bg-gray-100',
    textColor: 'text-gray-600'
  };
};

function ProtectedRoute({ children, allowDemo = false }) {
  const { isAuthenticated, loading } = useAuth();
  
  const urlParams = new URLSearchParams(window.location.search);
  const isDemoMode = urlParams.get('demo') === 'true';
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">&#8987;</div>
          <p className="text-gray-600">Un momento por favor...</p>
        </div>
      </div>
    );
  }
  
  if (allowDemo && isDemoMode) {
    return (
      <>
        <div className="bg-amber-500 text-white text-center py-2 px-4 text-sm font-medium">
          Modo Demo - Los datos no se guardarán
        </div>
        {children}
      </>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}

function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);

  if (!isAuthenticated) return null;

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center">
              <img src="/logo-revisar.png" alt="Revisar.ia" className="h-6 sm:h-8" />
            </Link>
          </div>

          <div className="flex items-center gap-4">
            <Link
              to="/nuevo-proyecto"
              className="inline-flex items-center justify-center w-10 h-10 bg-[#54ddaf] text-[#021423] rounded-lg hover:bg-[#3bb896] transition-colors"
              title="Iniciar Proyecto"
              aria-label="Iniciar nuevo proyecto"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </Link>

            <Link
              to="/onboarding"
              className="inline-flex items-center justify-center w-10 h-10 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-lg hover:from-emerald-600 hover:to-teal-700 transition-colors"
              title="Onboarding Empresa"
              aria-label="Registrar nueva empresa"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
              </svg>
            </Link>

            {user?.role === 'admin' && (
              <>
                <Link
                  to="/admin"
                  className="inline-flex items-center justify-center w-10 h-10 bg-[#021423] text-white rounded-lg hover:bg-gray-800 transition-colors"
                  title="Panel de Administración"
                  aria-label="Ir al panel de administración"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                </Link>
                <Link
                  to="/admin/documentacion"
                  className="inline-flex items-center justify-center w-10 h-10 bg-gradient-to-r from-slate-700 to-slate-900 text-white rounded-lg hover:from-slate-800 hover:to-slate-950 transition-colors"
                  title="Documentación"
                  aria-label="Ver documentación del sistema"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </Link>
              </>
            )}

            <Link
              to="/metrics"
              className="inline-flex items-center justify-center w-10 h-10 bg-[#54ddaf] text-[#021423] rounded-lg hover:bg-[#3bb896] transition-colors"
              title="Análisis de Rendimiento"
              aria-label="Ver análisis de rendimiento"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </Link>

            <Link
              to="/durezza"
              className="inline-flex items-center justify-center w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-colors"
              title="Revisar.IA"
              aria-label="Ir a Revisar.IA"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </Link>

            <Link
              to="/templates"
              className="inline-flex items-center justify-center w-10 h-10 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-lg hover:from-amber-600 hover:to-orange-600 transition-colors"
              title="Templates RAG"
              aria-label="Ver plantillas RAG"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </Link>

            <Link
              to="/proveedores"
              className="inline-flex items-center justify-center w-10 h-10 bg-gradient-to-r from-purple-500 to-violet-600 text-white rounded-lg hover:from-purple-600 hover:to-violet-700 transition-colors"
              title="Proveedores"
              aria-label="Gestión de proveedores"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </Link>

            <Link
              to="/biblioteca"
              className="inline-flex items-center justify-center w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg hover:from-indigo-600 hover:to-purple-700 transition-colors"
              title="Bibliotecar.IA"
              aria-label="Base de Conocimiento"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </Link>

            <Link
              to="/repositorio"
              className="inline-flex items-center justify-center w-10 h-10 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg hover:from-cyan-600 hover:to-blue-700 transition-colors"
              title="Repositorio de Conocimiento"
              aria-label="Disco Duro Corporativo"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
              </svg>
            </Link>

            <Link
              to="/disenar"
              className="inline-flex items-center justify-center w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-lg hover:from-purple-600 hover:to-pink-700 transition-colors"
              title="Diseñar.IA"
              aria-label="Auditoría de Diseño"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
              </svg>
            </Link>

            <Link
              to="/agent-checklist"
              className="inline-flex items-center justify-center w-10 h-10 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-lg hover:from-emerald-600 hover:to-teal-700 transition-colors"
              title="Checklist de Agentes"
              aria-label="Requerimientos por Agente"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </Link>

            <Link
              to="/"
              className="inline-flex items-center justify-center w-10 h-10 bg-gradient-to-r from-[#7FEDD8] to-[#5BC4AB] text-[#0a0f14] rounded-lg hover:from-[#6ddbc6] hover:to-[#4ab39a] transition-colors"
              title="Acerca de Nosotros"
              aria-label="Acerca de Revisar.IA"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </Link>

            <div className="relative">
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 font-medium">
                  {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
                </div>
                <span className="text-sm text-gray-700 hidden sm:block">{user?.full_name}</span>
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {showDropdown && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                  <div className="px-4 py-3 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                    <p className="text-xs text-gray-500">{user?.email}</p>
                    {user?.company && (
                      <p className="text-xs text-gray-400 mt-1">{user?.company}</p>
                    )}
                  </div>
                  <button
                    onClick={() => {
                      setShowDropdown(false);
                      logout();
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    Cerrar Sesión
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

const calculateDaysElapsed = (project) => {
  const startDate = project.submitted_at || project.created_at;
  if (!startDate) return 0;
  try {
    const start = new Date(startDate);
    const now = new Date();
    const diffTime = Math.abs(now - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  } catch {
    return 0;
  }
};

const getSemaforoInfo = (project) => {
  const status = (project.current_status || project.status)?.toUpperCase();
  const daysElapsed = calculateDaysElapsed(project);
  const stage = project.workflow_state;
  
  if (status === 'APPROVED') {
    return {
      color: 'bg-green-500',
      label: 'Aprobado',
      tooltip: 'Proyecto aprobado por todos los agentes',
      textColor: 'text-green-700'
    };
  }
  
  if (status === 'REJECTED') {
    return {
      color: 'bg-red-500',
      label: 'Rechazado',
      tooltip: 'Proyecto rechazado. Ver detalles de incidencias.',
      textColor: 'text-red-700'
    };
  }
  
  if (daysElapsed > 15) {
    return {
      color: 'bg-red-500',
      label: 'Vencido',
      tooltip: `Más de ${daysElapsed} días en revisión. Pendiente: ${getStageLabel(stage)}`,
      textColor: 'text-red-700'
    };
  }
  
  if (daysElapsed > 7) {
    return {
      color: 'bg-amber-500',
      label: 'En Revisión',
      tooltip: `${daysElapsed} días. Etapa actual: ${getStageLabel(stage)}`,
      textColor: 'text-amber-700'
    };
  }
  
  return {
    color: 'bg-yellow-500',
    label: 'En Revisión',
    tooltip: `Pendiente: ${getStageLabel(stage)} (${daysElapsed} días)`,
    textColor: 'text-yellow-700'
  };
};

const Dashboard = () => {
  const [projects, setProjects] = useState([]);
  const [stats, setStats] = useState({ approved: 0, rejected: 0, in_review: 0, total_amount: 0 });
  const [defenseFiles, setDefenseFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedProjects, setExpandedProjects] = useState({});

  const toggleProjectExpanded = (projectId) => {
    setExpandedProjects(prev => ({
      ...prev,
      [projectId]: !prev[projectId]
    }));
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [projectsRes, statsRes, defenseFilesRes] = await Promise.all([
        api.get('/projects'),
        api.get('/stats'),
        api.get('/defense-files')
      ]);

      setProjects(projectsRes.data.projects || []);
      setStats(statsRes.data || { approved: 0, rejected: 0, in_review: 0, total_amount: 0 });
      setDefenseFiles(defenseFilesRes.data.defense_files || []);
    } catch (error) {
      console.error("Error loading dashboard:", error);
    } finally {
      setLoading(false);
    }
  };

  const getLastReviewer = (project) => {
    if (!project.workflow_state) return '-';
    const stageToAgent = {
      'E1_ESTRATEGIA': 'A1_SPONSOR',
      'E2_FISCAL': 'A3_FISCAL',
      'E3_FINANZAS': 'A5_FINANZAS',
      'E4_LEGAL': 'LEGAL',
      'E5_APROBADO': 'A2_PMO',
      'E5_PMO': 'A2_PMO'
    };
    const agentId = stageToAgent[project.workflow_state];
    if (agentId) {
      const agent = getAgentInfo(agentId);
      return agent.name;
    }
    return '-';
  };

  const getProjectIncidences = () => {
    const incidences = [];
    defenseFiles.forEach(company => {
      (company.months || []).forEach(month => {
        (month.projects || []).forEach(project => {
          const deliberations = project.deliberations || [];
          deliberations.forEach(d => {
            if (['reject', 'rejected', 'request_adjustment', 'request_adjustments', 'abstain'].includes(d.decision?.toLowerCase())) {
              incidences.push({
                projectId: project.project_id,
                projectName: project.project_name || project.project_id,
                companyName: company.company_name,
                month: month.month,
                ...d
              });
            }
          });
        });
      });
    });
    return incidences;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">&#8987;</div>
          <p className="text-gray-600">Preparando tu dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard Ejecutivo</h1>
          <p className="text-sm text-gray-500 mt-1">Sistema de Trazabilidad Multi-Agente - Revisar.ia</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Aprobados</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{stats.approved || 0}</p>
              </div>
              <div className="w-4 h-4 rounded-full bg-green-500"></div>
            </div>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">En Revisión</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{stats.in_review || 0}</p>
              </div>
              <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
            </div>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Rechazados</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{stats.rejected || 0}</p>
              </div>
              <div className="w-4 h-4 rounded-full bg-red-500"></div>
            </div>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Monto Total</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{formatMontoTotal(stats.total_amount)}</p>
              </div>
              <div className="text-2xl">$</div>
            </div>
          </div>
        </div>

        <div className="mb-8">
          <UsageDashboard />
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-100 mb-8 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">Proyectos</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Semáforo
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Proyecto
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Etapa
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Último Revisor
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Puntuación
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Monto
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Días
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {projects.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="px-6 py-12 text-center text-gray-500">
                      <div className="text-4xl mb-2">&#128196;</div>
                      <p className="font-medium">No hay proyectos registrados</p>
                      <p className="text-sm mt-1">Los proyectos aparecerán aquí cuando se creen</p>
                    </td>
                  </tr>
                ) : (
                  projects.map((project) => {
                    const score = project.compliance_score || 0;
                    const scoreColor = score >= 75 ? 'bg-green-100 text-green-700' : 
                                       score >= 50 ? 'bg-yellow-100 text-yellow-700' : 
                                       'bg-red-100 text-red-700';
                    const daysElapsed = calculateDaysElapsed(project);
                    const semaforoInfo = getSemaforoInfo(project);
                    return (
                      <tr key={project.project_id} className="hover:bg-gray-50">
                        <td className="px-4 py-4">
                          <div className="relative group">
                            <div className="flex items-center gap-2 cursor-help">
                              <div className={`w-3 h-3 rounded-full ${semaforoInfo.color}`}></div>
                              <span className={`text-sm ${semaforoInfo.textColor}`}>{semaforoInfo.label}</span>
                            </div>
                            <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50">
                              <div className="bg-gray-900 text-white text-xs rounded-lg py-2 px-3 whitespace-nowrap shadow-lg">
                                {semaforoInfo.tooltip}
                                <div className="absolute top-full left-4 border-4 border-transparent border-t-gray-900"></div>
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          <div>
                            <p className="font-medium text-gray-900 max-w-[200px] truncate">{project.project_name}</p>
                            <p className="text-xs text-gray-500 font-mono">{project.project_id?.substring(0, 12)}...</p>
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                            {getStageLabel(project.workflow_state)}
                          </span>
                        </td>
                        <td className="px-4 py-4">
                          <span className="text-sm text-gray-600">{getLastReviewer(project)}</span>
                        </td>
                        <td className="px-4 py-4">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${scoreColor}`}>
                            {score.toFixed(0)}%
                          </span>
                        </td>
                        <td className="px-4 py-4">
                          <span className="font-medium text-gray-900">{formatMonto(project.budget_estimate)}</span>
                        </td>
                        <td className="px-4 py-4">
                          <span className={`font-medium ${daysElapsed > 15 ? 'text-red-600' : daysElapsed > 7 ? 'text-amber-600' : 'text-gray-600'}`}>
                            {daysElapsed}d
                          </span>
                        </td>
                        <td className="px-4 py-4">
                          <div className="flex items-center gap-2">
                            <Link 
                              to={`/project/${project.project_id}`}
                              className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 font-medium text-sm"
                            >
                              Ver
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                            </Link>
                            <a
                              href={`/api/defense/download/${project.project_id}`}
                              className="inline-flex items-center gap-1 text-green-600 hover:text-green-800 font-medium text-sm"
                              title="Descargar Defense File"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                              ZIP
                            </a>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {getProjectIncidences().length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-100 mb-8 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-2">
              <svg className="w-5 h-5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <h2 className="text-lg font-semibold text-gray-900">Incidencias y Observaciones</h2>
              <span className="ml-auto bg-amber-100 text-amber-700 text-xs font-medium px-2.5 py-0.5 rounded-full">
                {getProjectIncidences().length} pendientes
              </span>
            </div>
            <div className="p-6">
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {getProjectIncidences().map((inc, idx) => {
                  const agent = getAgentInfo(inc.agent_id);
                  const decisionColors = getDecisionColor(inc.decision);
                  const formatDate = (ts) => {
                    if (!ts) return '';
                    try {
                      return new Date(ts).toLocaleDateString('es-MX', { day: '2-digit', month: 'short' });
                    } catch { return ''; }
                  };
                  return (
                    <div key={idx} className={`p-4 rounded-lg border-l-4 ${decisionColors.border} ${decisionColors.bg}`}>
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-full ${agent.bgColor} flex items-center justify-center ${agent.textColor} font-bold text-sm`}>
                            {agent.initial}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">{agent.name}</p>
                            <p className="text-xs text-gray-500">{agent.role}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${decisionColors.bg} ${decisionColors.text}`}>
                            {getDecisionLabel(inc.decision)}
                          </span>
                          <p className="text-xs text-gray-400 mt-1">{formatDate(inc.timestamp)}</p>
                        </div>
                      </div>
                      <div className="mb-2">
                        <Link to={`/project/${inc.projectId}`} className="text-sm font-medium text-blue-600 hover:text-blue-800">
                          {inc.projectName}
                        </Link>
                        <span className="text-xs text-gray-500 ml-2">({getStageLabel(inc.stage)})</span>
                      </div>
                      <p className="text-sm text-gray-700 line-clamp-2">
                        {inc.analysis?.substring(0, 200)}...
                      </p>
                      {inc.requested_adjustments && (
                        <div className="mt-2 p-2 bg-white/60 rounded text-sm">
                          <span className="font-medium text-amber-700">Ajustes requeridos: </span>
                          <span className="text-gray-600">{inc.requested_adjustments}</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              <h2 className="text-lg font-semibold text-gray-900">Repositorio de Defense Files</h2>
            </div>
            <span className="bg-blue-100 text-blue-700 text-xs font-medium px-2.5 py-0.5 rounded-full">
              {defenseFiles.length} empresas
            </span>
          </div>
          <div className="p-6">
            {defenseFiles.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <svg className="w-12 h-12 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
                <p className="font-medium">No hay defense files</p>
                <p className="text-sm mt-1">Los archivos de defensa aparecerán cuando se procesen proyectos</p>
              </div>
            ) : (
              <div className="space-y-4">
                {defenseFiles.map((company) => {
                  const companyKey = `company_${company.company_name}`;
                  const isCompanyExpanded = expandedProjects[companyKey];
                  
                  return (
                    <div key={company.company_name} className="border border-gray-200 rounded-lg overflow-hidden">
                      <button
                        onClick={() => toggleProjectExpanded(companyKey)}
                        className="w-full px-4 py-4 bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 transition-colors flex items-center justify-between text-left"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center text-white">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                            </svg>
                          </div>
                          <div>
                            <p className="font-semibold text-gray-900">{company.company_name}</p>
                            <p className="text-xs text-gray-500">{company.total_projects} proyectos • {formatMontoTotal(company.total_budget)}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="bg-blue-100 text-blue-700 text-xs font-medium px-2.5 py-1 rounded-full">
                            {company.months?.length || 0} meses
                          </span>
                          <svg className={`w-5 h-5 text-gray-400 transform transition-transform ${isCompanyExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </div>
                      </button>
                      
                      {isCompanyExpanded && (
                        <div className="border-t border-gray-200 bg-gray-50">
                          {company.months?.map((month) => {
                            const monthKey = `${companyKey}_${month.month}`;
                            const isMonthExpanded = expandedProjects[monthKey];
                            
                            return (
                              <div key={month.month} className="border-b border-gray-100 last:border-b-0">
                                <button
                                  onClick={() => toggleProjectExpanded(monthKey)}
                                  className="w-full px-6 py-3 hover:bg-gray-100 transition-colors flex items-center justify-between text-left"
                                >
                                  <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center text-amber-600">
                                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                      </svg>
                                    </div>
                                    <div>
                                      <p className="font-medium text-gray-800">{month.month}</p>
                                      <p className="text-xs text-gray-500">{month.project_count} proyectos • {formatMontoTotal(month.total_budget)}</p>
                                    </div>
                                  </div>
                                  <svg className={`w-4 h-4 text-gray-400 transform transition-transform ${isMonthExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                  </svg>
                                </button>
                                
                                {isMonthExpanded && (
                                  <div className="px-6 pb-4 bg-white">
                                    <div className="space-y-3 pt-2">
                                      {month.projects?.map((project) => {
                                        const projectKey = `${monthKey}_${project.project_id}`;
                                        const isProjectExpanded = expandedProjects[projectKey];
                                        const deliberations = project.deliberations || [];
                                        const finalDecisionColors = getDecisionColor(project.final_decision);
                                        
                                        return (
                                          <div key={project.project_id} className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                                            <button
                                              onClick={() => toggleProjectExpanded(projectKey)}
                                              className="w-full px-4 py-3 hover:bg-gray-50 transition-colors flex items-center justify-between text-left"
                                            >
                                              <div className="flex items-center gap-3">
                                                <div className={`w-3 h-3 rounded-full ${project.final_decision === 'approved' ? 'bg-green-500' : project.final_decision === 'rejected' ? 'bg-red-500' : 'bg-yellow-500'}`}></div>
                                                <div>
                                                  <p className="font-medium text-gray-900 text-sm">{project.project_name || project.project_id}</p>
                                                  <p className="text-xs text-gray-500 font-mono">{project.project_id} • {formatMonto(project.budget)}</p>
                                                </div>
                                              </div>
                                              <div className="flex items-center gap-3">
                                                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${finalDecisionColors.bg} ${finalDecisionColors.text}`}>
                                                  {getDecisionLabel(project.final_decision) || 'En Proceso'}
                                                </span>
                                                <span className="text-xs text-gray-400">{deliberations.length} análisis</span>
                                                <svg className={`w-4 h-4 text-gray-400 transform transition-transform ${isProjectExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                </svg>
                                              </div>
                                            </button>
                                            
                                            {isProjectExpanded && (
                                              <div className="px-3 sm:px-4 pb-4 border-t border-gray-100 bg-gray-50">
                                                <div className="pt-4">
                                                  <h5 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3">Deliberaciones</h5>
                                                  <div className="space-y-3">
                                                    {deliberations.map((delib, idx) => {
                                                      const agent = getAgentInfo(delib.agent_id);
                                                      const decisionColors = getDecisionColor(delib.decision);
                                                      
                                                      return (
                                                        <div key={idx} className={`p-3 sm:p-4 rounded-xl border-l-4 bg-white shadow-sm ${decisionColors.border}`}>
                                                          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-2">
                                                            <div className="flex items-center gap-2">
                                                              <div className={`w-8 h-8 rounded-full ${agent.bgColor} flex items-center justify-center ${agent.textColor} font-bold text-xs flex-shrink-0`}>
                                                                {agent.initial}
                                                              </div>
                                                              <div className="min-w-0">
                                                                <span className="font-semibold text-gray-900 text-sm block">{agent.name}</span>
                                                                <span className="text-xs text-gray-500">{getStageLabel(delib.stage)}</span>
                                                              </div>
                                                            </div>
                                                            <span className={`self-start sm:self-auto px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap ${decisionColors.bg} ${decisionColors.text}`}>
                                                              {getDecisionLabel(delib.decision)}
                                                            </span>
                                                          </div>
                                                          <p className="text-sm text-gray-600 line-clamp-2 leading-relaxed">{delib.analysis?.substring(0, 120)}...</p>
                                                          {delib.pcloud_link && (
                                                            <a
                                                              href={delib.pcloud_link}
                                                              target="_blank"
                                                              rel="noopener noreferrer"
                                                              className="inline-flex items-center gap-1.5 mt-3 px-3 py-1.5 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-lg text-xs font-medium transition-colors"
                                                            >
                                                              <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                                              </svg>
                                                              Descargar PDF
                                                            </a>
                                                          )}
                                                        </div>
                                                      );
                                                    })}
                                                  </div>
                                                </div>
                                                
                                                <div className="mt-4 pt-4 border-t border-gray-200">
                                                  <div className="flex flex-wrap items-center gap-2">
                                                    <Link
                                                      to={`/project/${project.project_id}`}
                                                      className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-[#54ddaf] text-[#021423] rounded-lg text-sm font-medium hover:bg-[#45c99f] transition-colors min-h-[44px]"
                                                    >
                                                      <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                                      </svg>
                                                      Ver Detalles
                                                    </Link>
                                                    {project.project_folder_link && (
                                                      <a
                                                        href={project.project_folder_link}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors min-h-[44px]"
                                                      >
                                                        <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                                                        </svg>
                                                        Proyecto
                                                      </a>
                                                    )}
                                                    {project.bitacora_link && (
                                                      <a
                                                        href={project.bitacora_link}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-purple-100 text-purple-700 rounded-lg text-sm font-medium hover:bg-purple-200 transition-colors min-h-[44px]"
                                                      >
                                                        <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                        </svg>
                                                        Bitácora
                                                      </a>
                                                    )}
                                                    {project.defense_file_link && (
                                                      <a
                                                        href={project.defense_file_link}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium hover:bg-blue-200 transition-colors min-h-[44px]"
                                                      >
                                                        <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                                                        </svg>
                                                        Expediente
                                                      </a>
                                                    )}
                                                  </div>
                                                </div>
                                              </div>
                                            )}
                                          </div>
                                        );
                                      })}
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

const WorkflowStageIndicator = ({ currentStage, deliberations = [] }) => {
  const stages = [
    { id: 'E1_ESTRATEGIA', label: 'Estrategia', short: 'E1' },
    { id: 'E2_FISCAL', label: 'Fiscal', short: 'E2' },
    { id: 'E3_FINANZAS', label: 'Finanzas', short: 'E3' },
    { id: 'E4_LEGAL', label: 'Legal', short: 'E4' },
    { id: 'E5_APROBADO', label: 'Aprobación', short: 'E5' }
  ];

  const currentStageNum = getStageNumber(currentStage);
  const safeDeliberations = Array.isArray(deliberations) ? deliberations : [];
  
  const getStageStatus = (stageId) => {
    if (!Array.isArray(safeDeliberations) || safeDeliberations.length === 0) return null;
    const delib = safeDeliberations.find(d => d?.stage === stageId);
    if (!delib) return null;
    return delib.decision?.toLowerCase();
  };

  return (
    <div className="flex items-center justify-between w-full max-w-2xl">
      {stages.map((stage, index) => {
        const stageNum = index + 1;
        const isCompleted = stageNum < currentStageNum;
        const isCurrent = stageNum === currentStageNum;
        const stageDecision = getStageStatus(stage.id);
        
        let bgColor = 'bg-gray-200';
        let textColor = 'text-gray-500';
        let borderColor = 'border-gray-300';
        
        if (isCompleted || isCurrent) {
          if (stageDecision === 'approve' || stageDecision === 'approved') {
            bgColor = 'bg-green-500';
            textColor = 'text-white';
            borderColor = 'border-green-600';
          } else if (stageDecision === 'reject' || stageDecision === 'rejected') {
            bgColor = 'bg-red-500';
            textColor = 'text-white';
            borderColor = 'border-red-600';
          } else if (stageDecision === 'request_adjustment') {
            bgColor = 'bg-amber-500';
            textColor = 'text-white';
            borderColor = 'border-amber-600';
          } else if (isCurrent) {
            bgColor = 'bg-blue-500';
            textColor = 'text-white';
            borderColor = 'border-blue-600';
          }
        }

        return (
          <React.Fragment key={stage.id}>
            <div className="flex flex-col items-center">
              <div className={`w-10 h-10 rounded-full ${bgColor} ${textColor} flex items-center justify-center text-sm font-bold border-2 ${borderColor}`}>
                {stageNum}
              </div>
              <span className="text-xs mt-1 text-gray-600 text-center max-w-[60px]">{stage.label}</span>
            </div>
            {index < stages.length - 1 && (
              <div className={`flex-1 h-1 mx-2 ${stageNum < currentStageNum ? 'bg-green-400' : 'bg-gray-200'}`}></div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

const DeliberationCard = ({ deliberation, documents = [] }) => {
  if (!deliberation) return null;
  
  const agent = getAgentInfo(deliberation.agent_id);
  const decisionColors = getDecisionColor(deliberation.decision);
  const [isExpanded, setIsExpanded] = useState(false);
  
  const safeDocuments = Array.isArray(documents) ? documents : [];
  const relatedDocs = safeDocuments.filter(doc => 
    doc && doc.agent_id === deliberation.agent_id && doc.stage === deliberation.stage
  );

  const formatTimestamp = (ts) => {
    if (!ts) return '';
    try {
      return new Date(ts).toLocaleString('es-MX', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return ts;
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border-l-4 ${decisionColors.border} p-4 mb-4`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-12 h-12 rounded-full ${agent.bgColor} flex items-center justify-center ${agent.textColor} font-bold text-lg`}>
            {agent.initial}
          </div>
          <div>
            <p className="font-semibold text-gray-900">{agent.name}</p>
            <p className="text-sm text-gray-500">{agent.role} • {getStageLabel(deliberation.stage)}</p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${decisionColors.bg} ${decisionColors.text}`}>
            {getDecisionLabel(deliberation.decision)}
          </span>
          <span className="text-xs text-gray-400">{formatTimestamp(deliberation.timestamp)}</span>
        </div>
      </div>

      <div className="mt-4">
        <div className={`text-gray-700 text-sm ${isExpanded ? '' : 'line-clamp-3'}`}>
          {deliberation.analysis?.split('\n').map((line, i) => (
            <p key={i} className="mb-2">{line}</p>
          ))}
        </div>
        {deliberation.analysis?.length > 200 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium mt-2"
          >
            {isExpanded ? 'Ver menos' : 'Ver más'}
          </button>
        )}
      </div>

      {deliberation.risk_assessment && (
        <div className="mt-3 p-3 bg-red-50 rounded-lg border border-red-100">
          <p className="text-sm font-medium text-red-700 flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Evaluación de Riesgos
          </p>
          <p className="text-sm text-red-600 mt-1">{deliberation.risk_assessment}</p>
        </div>
      )}

      {deliberation.requested_adjustments && (
        <div className="mt-3 p-3 bg-amber-50 rounded-lg border border-amber-100">
          <p className="text-sm font-medium text-amber-700 flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Ajustes Solicitados
          </p>
          <p className="text-sm text-amber-600 mt-1">{deliberation.requested_adjustments}</p>
        </div>
      )}

      {relatedDocs.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="text-xs font-medium text-gray-500 mb-2">Documentos Generados:</p>
          <div className="flex flex-wrap gap-2">
            {relatedDocs.map((doc, idx) => (
              <a
                key={idx}
                href={doc.pcloud_link || '#'}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded text-xs text-gray-700 transition-colors"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                {doc.doc_type}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const IncidencePanel = ({ deliberations = [] }) => {
  const safeDeliberations = Array.isArray(deliberations) ? deliberations : [];
  const incidences = safeDeliberations.filter(d => 
    d && ['reject', 'rejected', 'request_adjustment', 'request_adjustments', 'abstain'].includes(d.decision?.toLowerCase())
  );

  if (incidences.length === 0) {
    return (
      <div className="bg-green-50 rounded-lg p-6 text-center">
        <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
          <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <p className="text-green-700 font-medium">Sin Incidencias</p>
        <p className="text-green-600 text-sm mt-1">Todas las deliberaciones fueron aprobadas</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {incidences.map((inc, idx) => {
        const agent = getAgentInfo(inc.agent_id);
        const colors = getDecisionColor(inc.decision);
        
        return (
          <div key={idx} className={`p-4 rounded-lg border ${colors.bg} border-l-4 ${colors.border}`}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className={`${colors.dot} w-2 h-2 rounded-full`}></span>
                <span className="font-medium text-gray-900">{agent.name}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${colors.bg} ${colors.text}`}>
                  {getDecisionLabel(inc.decision)}
                </span>
              </div>
              <span className="text-xs text-gray-500">{getStageLabel(inc.stage)}</span>
            </div>
            <p className="text-sm text-gray-700 line-clamp-2">{inc.analysis?.substring(0, 200)}...</p>
            {inc.requested_adjustments && (
              <div className="mt-2 p-2 bg-white/50 rounded text-sm">
                <span className="font-medium text-gray-700">Ajustes: </span>
                <span className="text-gray-600">{inc.requested_adjustments}</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

const DocumentsSection = ({ documents = [], pcloudDocuments = [], bitacoraLink }) => {
  const allDocs = [...documents, ...pcloudDocuments].filter(doc => doc.pcloud_link);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString('es-MX', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const getDocTypeLabel = (docType) => {
    const types = {
      'reporte_estrategia': 'Reporte Estrategia',
      'reporte_fiscal': 'Reporte Fiscal',
      'reporte_finanzas': 'Reporte Finanzas',
      'reporte_legal': 'Reporte Legal',
      'reporte_consolidacion': 'Consolidación PMO',
      'solicitud_modificacion': 'Solicitud de Modificación',
      'aprobacion_final': 'Aprobación Final'
    };
    return types[docType] || docType;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Documentos y Evidencias</h3>
        {bitacoraLink && (
          <a
            href={bitacoraLink}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#54ddaf] text-[#021423] rounded-lg hover:bg-[#45c99f] text-sm font-medium transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Descargar Bitácora
          </a>
        )}
      </div>
      
      {allDocs.length === 0 ? (
        <div className="p-8 text-center text-gray-500">
          <svg className="w-12 h-12 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="font-medium">No hay documentos disponibles</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agente</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Etapa</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Enlace</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {allDocs.map((doc, idx) => {
                const agent = getAgentInfo(doc.agent_id);
                return (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span className="text-sm font-medium text-gray-900">{getDocTypeLabel(doc.doc_type)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className={`w-6 h-6 rounded-full ${agent.bgColor} flex items-center justify-center ${agent.textColor} text-xs font-bold`}>
                          {agent.initial}
                        </div>
                        <span className="text-sm text-gray-600">{agent.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-600">{getStageLabel(doc.stage)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-500">{formatDate(doc.created_at || doc.uploaded_at)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <a
                        href={doc.pcloud_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 text-sm"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                        Ver en pCloud
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

const ProjectDetails = () => {
  const [projectData, setProjectData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('timeline');
  const projectId = window.location.pathname.split('/').pop();

  useEffect(() => {
    loadProjectDetails();
  }, []);

  const loadProjectDetails = async () => {
    try {
      const response = await api.get(`/projects/${projectId}`);
      const data = response.data;
      
      const normalizedData = {
        project: data.project || {},
        defense_file: data.defense_file || {},
        deliberations: data.defense_file?.deliberations || data.interactions || [],
        documents: data.defense_file?.pcloud_documents || [],
        bitacora_link: data.defense_file?.bitacora_link || null,
        compliance_score: data.project?.compliance_score || data.defense_file?.compliance_score || 0
      };
      
      setProjectData(normalizedData);
    } catch (error) {
      console.error("Error loading project:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">&#8987;</div>
          <p className="text-gray-600">Cargando información del proyecto...</p>
        </div>
      </div>
    );
  }

  if (!projectData) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">&#128269;</div>
          <p className="text-xl text-gray-600">No encontramos este proyecto</p>
          <p className="text-sm text-gray-500 mt-2">Verifica el ID o regresa al dashboard</p>
          <Link to="/" className="mt-4 inline-block text-blue-600 hover:text-blue-800">
            Volver al Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const project = projectData.project || projectData || {};
  const defenseFile = projectData.defense_file || {};
  const deliberations = Array.isArray(projectData.deliberations) 
    ? projectData.deliberations 
    : (Array.isArray(defenseFile.deliberations) ? defenseFile.deliberations : []);
  const documents = Array.isArray(projectData.documents) 
    ? projectData.documents 
    : (Array.isArray(defenseFile.documents) ? defenseFile.documents : []);
  const pcloudDocuments = Array.isArray(defenseFile.pcloud_documents) 
    ? defenseFile.pcloud_documents 
    : [];
  const bitacoraLink = projectData.bitacora_link || defenseFile.bitacora_link || null;
  
  // Calculate compliance score dynamically based on agent deliberations
  const calculateComplianceScore = (deliberations) => {
    if (!deliberations || deliberations.length === 0) return 0;
    
    const approvedCount = deliberations.filter(d => 
      d.decision === 'approve' || d.decision === 'approved'
    ).length;
    
    const totalAgents = deliberations.length;
    return totalAgents > 0 ? Math.round((approvedCount / totalAgents) * 100) : 0;
  };
  
  // Check if any agent requested adjustments
  const hasAdjustmentRequests = deliberations.some(d => 
    d.decision === 'request_adjustment' || 
    d.decision === 'requires_adjustment' ||
    d.decision === 'ajuste'
  );
  
  // Get agents that requested adjustments
  const adjustmentAgents = deliberations.filter(d => 
    d.decision === 'request_adjustment' || 
    d.decision === 'requires_adjustment' ||
    d.decision === 'ajuste'
  );
  
  const complianceScore = deliberations.length > 0 
    ? calculateComplianceScore(deliberations) 
    : (projectData.compliance_score || defenseFile.compliance_score || project.compliance_score || 0);

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link to="/" className="text-blue-600 hover:text-blue-800 text-sm mb-4 inline-flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Volver al Dashboard
        </Link>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mt-4 mb-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-2xl font-bold text-gray-900">{project.project_name}</h1>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  (project.current_status || project.status)?.toUpperCase() === 'APPROVED' ? 'bg-green-100 text-green-700' :
                  (project.current_status || project.status)?.toUpperCase() === 'REJECTED' ? 'bg-red-100 text-red-700' :
                  'bg-yellow-100 text-yellow-700'
                }`}>
                  {getStatusLabel(project.current_status || project.status)}
                </span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  complianceScore >= 75 ? 'bg-green-100 text-green-700' :
                  complianceScore >= 50 ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {complianceScore.toFixed(0)}% Cumplimiento
                </span>
              </div>
              <p className="text-sm text-gray-500 font-mono">ID: {project.project_id}</p>
            </div>
            <div className="flex items-center gap-4">
              <DefenseFileDownload 
                projectId={project.project_id || projectId} 
                projectName={project.project_name} 
              />
              {hasAdjustmentRequests && !defenseFile.final_decision && (
                <Link 
                  to={`/submit?parent=${project.project_id}`}
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white font-semibold rounded-lg transition-colors flex items-center gap-2 shadow-sm"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  Subir Nueva Versión
                </Link>
              )}
              {defenseFile.final_decision && (
                <div className={`px-4 py-2 rounded-lg ${
                  defenseFile.final_decision === 'approved' ? 'bg-green-50 border border-green-200' :
                  defenseFile.final_decision === 'rejected' ? 'bg-red-50 border border-red-200' :
                  'bg-gray-50 border border-gray-200'
                }`}>
                  <p className="text-xs text-gray-500 uppercase">Decisión Final</p>
                  <p className={`font-semibold ${
                    defenseFile.final_decision === 'approved' ? 'text-green-700' :
                    defenseFile.final_decision === 'rejected' ? 'text-red-700' :
                    'text-gray-700'
                  }`}>
                    {getDecisionLabel(defenseFile.final_decision)}
                  </p>
                </div>
              )}
            </div>
          </div>
          
          {hasAdjustmentRequests && !defenseFile.final_decision && (
            <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-amber-800 mb-1">Se requieren ajustes</h3>
                  <p className="text-sm text-amber-700 mb-2">
                    {adjustmentAgents.length === 1 
                      ? `El agente ${adjustmentAgents[0].agent_id} ha solicitado ajustes antes de continuar.`
                      : `${adjustmentAgents.length} agentes han solicitado ajustes antes de continuar.`
                    }
                  </p>
                  <p className="text-xs text-amber-600">
                    Revisa las deliberaciones y sube una nueva versión del proyecto con los ajustes solicitados.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="mb-6">
            <p className="text-sm font-medium text-gray-500 mb-3">Progreso del Flujo de Trabajo</p>
            <WorkflowStageIndicator 
              currentStage={project.workflow_state} 
              deliberations={deliberations}
            />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">Sponsor</p>
              <p className="font-semibold text-gray-900">{project.sponsor_name || '-'}</p>
              <p className="text-xs text-gray-500">{project.sponsor_email || ''}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">Presupuesto</p>
              <p className="font-semibold text-gray-900">{formatMonto(project.budget_estimate || 0)}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">Beneficio Esperado</p>
              <p className="font-semibold text-gray-900">{formatMonto(project.expected_benefit || 0)}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">Deliberaciones</p>
              <p className="font-semibold text-gray-900">{deliberations.length}</p>
            </div>
          </div>

          {project.description && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-500 mb-1">Descripción</p>
              <p className="text-gray-700">{project.description}</p>
            </div>
          )}
        </div>

        <VersionHistoryTimeline 
          projectId={project.project_id} 
          currentProjectId={project.project_id}
        />

        <div className="mb-6">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('timeline')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'timeline' 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Línea de Tiempo
            </button>
            <button
              onClick={() => setActiveTab('incidences')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'incidences' 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Incidencias
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'documents' 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Documentos
            </button>
          </div>
        </div>

        {activeTab === 'timeline' && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Historial de Deliberaciones</h2>
            {deliberations.length === 0 ? (
              <div className="bg-white rounded-lg p-8 text-center text-gray-500 border border-gray-100">
                <svg className="w-12 h-12 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <p className="font-medium">No hay deliberaciones registradas</p>
                <p className="text-sm mt-1">Las deliberaciones de los agentes aparecerán aquí</p>
              </div>
            ) : (
              <div className="space-y-4">
                {deliberations.map((delib, index) => (
                  <DeliberationCard 
                    key={index} 
                    deliberation={delib} 
                    documents={documents}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'incidences' && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Panel de Incidencias</h2>
            <IncidencePanel deliberations={deliberations} />
          </div>
        )}

        {activeTab === 'documents' && (
          <DocumentsSection 
            documents={documents}
            pcloudDocuments={pcloudDocuments}
            bitacoraLink={bitacoraLink}
          />
        )}

        {defenseFile.final_justification && (
          <div className="mt-6 bg-blue-50 rounded-lg p-6 border border-blue-100">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">Justificación Final</h3>
            <p className="text-blue-800">{defenseFile.final_justification}</p>
          </div>
        )}
      </main>
    </div>
  );
};

function AppContent() {
  return (
    <div className="App min-h-screen flex flex-col">
      <Navbar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<LandingPage />} />
        <Route path="/onboarding" element={
          <ProtectedRoute>
            <ChatbotArchivo />
          </ProtectedRoute>
        } />
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="/nuevo-proyecto" element={
          <ProtectedRoute allowDemo={true}>
            <ProjectForm />
          </ProtectedRoute>
        } />
        <Route path="/project/:projectId" element={
          <ProtectedRoute>
            <ProjectDetails />
          </ProtectedRoute>
        } />
        <Route path="/admin" element={
          <ProtectedRoute>
            <AdminPage />
          </ProtectedRoute>
        } />
        <Route path="/admin/documentacion" element={
          <ProtectedRoute>
            <AdminDocumentacion />
          </ProtectedRoute>
        } />
        <Route path="/admin/clientes" element={
          <ProtectedRoute>
            <AdminClientes />
          </ProtectedRoute>
        } />
        <Route path="/metrics" element={
          <ProtectedRoute>
            <MetricsDashboard />
          </ProtectedRoute>
        } />
        <Route path="/costs" element={
          <CostsDashboard />
        } />
        <Route path="/costs-dashboard" element={
          <CostsDashboard />
        } />
        <Route path="/durezza" element={
          <ProtectedRoute>
            <Suspense fallback={<LoadingFallback />}>
              <DurezzaDashboard />
            </Suspense>
          </ProtectedRoute>
        } />
        <Route path="/templates" element={
          <TemplatesPage />
        } />
        <Route path="/empresas" element={
          <ProtectedRoute>
            <ListaEmpresas />
          </ProtectedRoute>
        } />
        <Route path="/empresas/nueva" element={
          <ProtectedRoute>
            <OnboardingEmpresa />
          </ProtectedRoute>
        } />
        <Route path="/empresa/:empresaId/configuracion" element={
          <ProtectedRoute>
            <ConfiguracionEmpresa />
          </ProtectedRoute>
        } />
        <Route path="/proveedores" element={
          <ProtectedRoute>
            <ProveedoresPage />
          </ProtectedRoute>
        } />
        <Route path="/biblioteca" element={
          <ProtectedRoute>
            <BibliotecaChat />
          </ProtectedRoute>
        } />
        <Route path="/estado-acervo" element={
          <ProtectedRoute>
            <EstadoAcervo />
          </ProtectedRoute>
        } />
        <Route path="/disenar" element={
          <ProtectedRoute>
            <DisenarIA />
          </ProtectedRoute>
        } />
        <Route path="/agent-checklist" element={
          <ProtectedRoute>
            <AgentChecklist />
          </ProtectedRoute>
        } />
        <Route path="/repositorio" element={
          <ProtectedRoute>
            <KnowledgeRepository />
          </ProtectedRoute>
        } />
        <Route path="/agentes" element={
          <ProtectedRoute>
            <AgentsDashboard />
          </ProtectedRoute>
        } />
      </Routes>
      <Footer />
      <SupportChatWidget />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
