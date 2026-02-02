/**
 * SidebarContext.jsx - Context para manejar el estado del sidebar
 *
 * Proporciona estado global para:
 * - Sidebar expandido/colapsado (desktop)
 * - Drawer móvil abierto/cerrado
 * - Grupos de menú expandidos
 */

import React, { createContext, useContext, useState, useCallback } from 'react';
import { useLocalStorage } from '../../hooks/useLocalStorage';

const SidebarContext = createContext(null);

export function SidebarProvider({ children }) {
  // Estado persistente para sidebar expandido/colapsado en desktop
  const [isExpanded, setIsExpanded] = useLocalStorage('sidebar-expanded', true);

  // Estado para drawer móvil
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  // Grupos expandidos (persistido)
  const [expandedGroups, setExpandedGroups] = useLocalStorage('sidebar-groups', {});

  const toggleExpanded = useCallback(() => {
    setIsExpanded((prev) => !prev);
  }, [setIsExpanded]);

  const toggleMobile = useCallback(() => {
    setIsMobileOpen((prev) => !prev);
  }, []);

  const openMobile = useCallback(() => {
    setIsMobileOpen(true);
  }, []);

  const closeMobile = useCallback(() => {
    setIsMobileOpen(false);
  }, []);

  const toggleGroup = useCallback(
    (groupId) => {
      setExpandedGroups((prev) => ({
        ...prev,
        [groupId]: !prev[groupId],
      }));
    },
    [setExpandedGroups]
  );

  const isGroupExpanded = useCallback(
    (groupId) => {
      return expandedGroups[groupId] ?? false;
    },
    [expandedGroups]
  );

  const value = {
    isExpanded,
    isMobileOpen,
    expandedGroups,
    toggleExpanded,
    toggleMobile,
    openMobile,
    closeMobile,
    toggleGroup,
    isGroupExpanded,
  };

  return <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>;
}

export function useSidebar() {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error('useSidebar must be used within SidebarProvider');
  }
  return context;
}

export default SidebarContext;
