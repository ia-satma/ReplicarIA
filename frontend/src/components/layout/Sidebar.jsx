/**
 * Sidebar.jsx - Componente principal del sidebar
 *
 * Sidebar lateral responsivo con:
 * - Logo (completo o icono según estado)
 * - Navegación con grupos colapsables
 * - Toggle para expandir/colapsar
 * - Solo visible en desktop (lg+)
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { PanelLeftClose, PanelLeft } from 'lucide-react';
import { ScrollArea } from '../ui/scroll-area';
import { Separator } from '../ui/separator';
import { Button } from '../ui/button';
import { useSidebar } from './SidebarContext';
import { SidebarGroup } from './SidebarGroup';
import { NAVIGATION_CONFIG } from '../../config/navigation';

export function Sidebar() {
  const { isExpanded, toggleExpanded } = useSidebar();

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 h-screen bg-white dark:bg-gray-900',
        'border-r border-gray-200 dark:border-gray-800',
        'transition-all duration-300 ease-in-out',
        'hidden lg:flex flex-col',
        isExpanded ? 'w-64' : 'w-20'
      )}
    >
      {/* Header */}
      <div
        className={cn(
          'flex items-center h-16 px-4 border-b border-gray-200 dark:border-gray-800',
          isExpanded ? 'justify-between' : 'justify-center'
        )}
      >
        <Link to="/" className="flex items-center">
          {isExpanded ? (
            <img
              src="/logo-revisar.png"
              alt="Revisar.ia"
              className="h-8 object-contain"
            />
          ) : (
            <div className="w-10 h-10 bg-gradient-to-br from-[#54ddaf] to-[#3bb896] rounded-lg flex items-center justify-center text-white font-bold text-lg">
              R
            </div>
          )}
        </Link>

        {isExpanded && (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleExpanded}
            className="text-gray-500 hover:text-gray-700"
          >
            <PanelLeftClose className="w-5 h-5" />
          </Button>
        )}
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 px-3 py-4">
        <nav className="space-y-1">
          {NAVIGATION_CONFIG.map((group, index) => (
            <React.Fragment key={group.id}>
              <SidebarGroup group={group} />
              {index < NAVIGATION_CONFIG.length - 1 && isExpanded && (
                <Separator className="my-3" />
              )}
            </React.Fragment>
          ))}
        </nav>
      </ScrollArea>

      {/* Toggle button (collapsed mode) */}
      {!isExpanded && (
        <div className="p-4 border-t border-gray-200 dark:border-gray-800">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleExpanded}
            className="w-full text-gray-500 hover:text-gray-700"
          >
            <PanelLeft className="w-5 h-5" />
          </Button>
        </div>
      )}
    </aside>
  );
}

export default Sidebar;
