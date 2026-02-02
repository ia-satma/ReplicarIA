/**
 * SidebarItem.jsx - Item individual del menú
 *
 * Renderiza un enlace de navegación con:
 * - Icono con gradiente opcional
 * - Label (visible cuando está expandido)
 * - Tooltip (cuando está colapsado)
 * - Estado activo basado en ruta
 * - Badge opcional
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from '../ui/tooltip';
import { useSidebar } from './SidebarContext';

export function SidebarItem({ item, isNested = false, forceExpanded = false }) {
  const location = useLocation();
  const { isExpanded: sidebarExpanded, closeMobile } = useSidebar();
  const isExpanded = forceExpanded || sidebarExpanded;
  const isActive = location.pathname === item.path;

  const Icon = item.icon;

  const content = (
    <Link
      to={item.path}
      onClick={closeMobile}
      className={cn(
        'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
        'hover:bg-gray-100 dark:hover:bg-gray-800',
        isActive && 'bg-primary/10 text-primary font-medium',
        isNested && 'ml-4',
        !isExpanded && 'justify-center px-2'
      )}
    >
      <div
        className={cn(
          'flex items-center justify-center w-8 h-8 rounded-lg flex-shrink-0 transition-all',
          item.gradient
            ? `bg-gradient-to-r ${item.gradient} text-white`
            : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
        )}
      >
        <Icon className="w-4 h-4" />
      </div>

      {isExpanded && (
        <span className="text-sm truncate flex-1">{item.label}</span>
      )}

      {isExpanded && item.badge && (
        <span className="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 animate-pulse">
          {item.badge}
        </span>
      )}
    </Link>
  );

  // En modo colapsado, mostrar tooltip
  if (!isExpanded) {
    return (
      <TooltipProvider delayDuration={0}>
        <Tooltip>
          <TooltipTrigger asChild>{content}</TooltipTrigger>
          <TooltipContent side="right" className="font-medium">
            <div className="flex items-center gap-2">
              {item.label}
              {item.badge && (
                <span className="px-1.5 py-0.5 text-xs rounded bg-green-100 text-green-700">
                  {item.badge}
                </span>
              )}
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return content;
}

export default SidebarItem;
