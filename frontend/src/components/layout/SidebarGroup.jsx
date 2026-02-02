/**
 * SidebarGroup.jsx - Grupo colapsable del menú
 *
 * Renderiza un grupo de navegación con:
 * - Header con icono y chevron
 * - Submenú colapsable
 * - Filtrado por permisos
 * - Popover con items en modo colapsado
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { ChevronRight } from 'lucide-react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '../ui/collapsible';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from '../ui/tooltip';
import { useSidebar } from './SidebarContext';
import { SidebarItem } from './SidebarItem';
import { useAuth } from '../../context/AuthContext';
import { hasPermission } from '../../utils/permissions';

export function SidebarGroup({ group, forceExpanded = false }) {
  const { isExpanded: sidebarExpanded, isGroupExpanded, toggleGroup, closeMobile } =
    useSidebar();
  const { user } = useAuth();
  const isExpanded = forceExpanded || sidebarExpanded;
  const isOpen = isGroupExpanded(group.id);

  const Icon = group.icon;

  // Si el grupo requiere permiso y el usuario no lo tiene, no mostrar
  if (group.permission && !hasPermission(user, group.permission)) {
    return null;
  }

  // Filtrar items por permisos
  const visibleItems = group.items?.filter(
    (item) => !item.permission || hasPermission(user, item.permission)
  );

  // Si no hay items visibles después del filtrado, no mostrar el grupo
  if (group.items && visibleItems?.length === 0) {
    return null;
  }

  // Si el grupo no tiene items (es un enlace directo)
  if (!group.items && group.path) {
    return <SidebarItem item={group} forceExpanded={forceExpanded} />;
  }

  const trigger = (
    <CollapsibleTrigger
      className={cn(
        'flex items-center gap-3 w-full px-3 py-2.5 rounded-lg transition-all duration-200',
        'hover:bg-gray-100 dark:hover:bg-gray-800',
        !isExpanded && 'justify-center px-2'
      )}
      onClick={(e) => {
        if (isExpanded) {
          toggleGroup(group.id);
        }
      }}
    >
      <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gray-100 dark:bg-gray-800 flex-shrink-0">
        <Icon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
      </div>

      {isExpanded && (
        <>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate flex-1 text-left">
            {group.label}
          </span>
          <ChevronRight
            className={cn(
              'w-4 h-4 text-gray-400 transition-transform duration-200',
              isOpen && 'rotate-90'
            )}
          />
        </>
      )}
    </CollapsibleTrigger>
  );

  // En modo colapsado, mostrar popover con items
  if (!isExpanded) {
    return (
      <TooltipProvider delayDuration={0}>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="cursor-pointer">{trigger}</div>
          </TooltipTrigger>
          <TooltipContent
            side="right"
            className="p-2 w-48"
            sideOffset={10}
          >
            <div className="font-medium text-sm mb-2 px-2 text-gray-900 dark:text-gray-100">
              {group.label}
            </div>
            <div className="space-y-1">
              {visibleItems?.map((item) => (
                <Link
                  key={item.id}
                  to={item.path}
                  onClick={closeMobile}
                  className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-sm text-gray-700 dark:text-gray-300"
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                  {item.badge && (
                    <span className="ml-auto px-1.5 py-0.5 text-xs rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                      {item.badge}
                    </span>
                  )}
                </Link>
              ))}
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <Collapsible open={isOpen} onOpenChange={() => toggleGroup(group.id)}>
      {trigger}
      <CollapsibleContent>
        <div className="space-y-1 mt-1">
          {visibleItems?.map((item) => (
            <SidebarItem
              key={item.id}
              item={item}
              isNested
              forceExpanded={forceExpanded}
            />
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

export default SidebarGroup;
