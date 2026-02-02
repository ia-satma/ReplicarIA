/**
 * navigation.js - Configuración centralizada del menú de navegación
 *
 * Define la estructura de grupos, items, iconos y permisos
 * para el sidebar de la aplicación.
 */

import {
  LayoutDashboard,
  FolderPlus,
  Building2,
  Users,
  BookOpen,
  Database,
  Palette,
  FileText,
  Bot,
  MessageSquare,
  BarChart3,
  DollarSign,
  Shield,
  FileCode,
  UserCog,
  Scale,
  HelpCircle,
  Info,
  Briefcase,
  ListChecks,
} from 'lucide-react';
import { PERMISSIONS } from '../utils/permissions';

export const NAVIGATION_CONFIG = [
  {
    id: 'proyectos',
    label: 'Proyectos',
    icon: LayoutDashboard,
    items: [
      {
        id: 'nuevo-proyecto',
        label: 'Nuevo Proyecto',
        path: '/nuevo-proyecto',
        icon: FolderPlus,
        gradient: 'from-[#34C759] to-[#2CB24E]',
      },
      {
        id: 'dashboard',
        label: 'Dashboard',
        path: '/dashboard',
        icon: LayoutDashboard,
        gradient: 'from-blue-600 to-indigo-600',
      },
    ],
  },
  {
    id: 'empresas',
    label: 'Empresas',
    icon: Building2,
    items: [
      {
        id: 'lista-empresas',
        label: 'Mis Empresas',
        path: '/empresas',
        icon: Building2,
      },
      {
        id: 'nueva-empresa',
        label: 'Nueva Empresa',
        path: '/empresas/nueva',
        icon: FolderPlus,
      },
      {
        id: 'onboarding',
        label: 'Onboarding',
        path: '/onboarding',
        icon: Briefcase,
        gradient: 'from-[#34C759] to-[#249C43]',
      },
    ],
  },
  {
    id: 'proveedores',
    label: 'Proveedores',
    icon: Users,
    path: '/proveedores',
    gradient: 'from-purple-500 to-violet-600',
  },
  {
    id: 'herramientas-ia',
    label: 'Herramientas IA',
    icon: Bot,
    items: [
      {
        id: 'biblioteca',
        label: 'Bibliotecar.IA',
        path: '/biblioteca',
        icon: BookOpen,
        gradient: 'from-indigo-500 to-purple-600',
      },
      {
        id: 'repositorio',
        label: 'Repositorio',
        path: '/repositorio',
        icon: Database,
        gradient: 'from-cyan-500 to-blue-600',
      },
      {
        id: 'disenar',
        label: 'Diseñar.IA',
        path: '/disenar',
        icon: Palette,
        gradient: 'from-purple-500 to-pink-600',
      },
      {
        id: 'templates',
        label: 'Templates RAG',
        path: '/templates',
        icon: FileText,
        gradient: 'from-amber-500 to-orange-500',
      },
    ],
  },
  {
    id: 'agentes',
    label: 'Agentes',
    icon: Bot,
    items: [
      {
        id: 'agentes-dashboard',
        label: 'Panel de Agentes',
        path: '/agentes',
        icon: Bot,
      },
      {
        id: 'agent-checklist',
        label: 'Checklist',
        path: '/agent-checklist',
        icon: ListChecks,
        gradient: 'from-[#34C759] to-[#249C43]',
      },
      {
        id: 'agent-comms',
        label: 'Comunicaciones',
        path: '/agent-comms',
        icon: MessageSquare,
        gradient: 'from-blue-600 to-cyan-500',
        badge: 'live',
      },
    ],
  },
  {
    id: 'analisis',
    label: 'Análisis',
    icon: BarChart3,
    items: [
      {
        id: 'metrics',
        label: 'Métricas',
        path: '/metrics',
        icon: BarChart3,
        gradient: 'from-[#34C759] to-[#2CB24E]',
      },
      {
        id: 'costs',
        label: 'Costos',
        path: '/costs-dashboard',
        icon: DollarSign,
      },
    ],
  },
  {
    id: 'admin',
    label: 'Administración',
    icon: Shield,
    permission: PERMISSIONS.VIEW_ADMIN,
    items: [
      {
        id: 'admin-panel',
        label: 'Panel Admin',
        path: '/admin',
        icon: Shield,
        gradient: 'from-slate-700 to-slate-900',
      },
      {
        id: 'admin-docs',
        label: 'Documentación',
        path: '/admin/documentacion',
        icon: FileCode,
        permission: PERMISSIONS.VIEW_ADMIN_DOCS,
      },
      {
        id: 'admin-clientes',
        label: 'Clientes',
        path: '/admin/clientes',
        icon: UserCog,
        permission: PERMISSIONS.VIEW_ADMIN_CLIENTS,
      },
    ],
  },
  {
    id: 'info',
    label: 'Información',
    icon: Info,
    items: [
      {
        id: 'base-legal',
        label: 'Base Legal',
        path: '/base-legal',
        icon: Scale,
      },
      {
        id: 'faq',
        label: 'FAQ',
        path: '/faq',
        icon: HelpCircle,
      },
      {
        id: 'como-funciona',
        label: 'Cómo Funciona',
        path: '/como-funciona',
        icon: Info,
      },
    ],
  },
];

export default NAVIGATION_CONFIG;
