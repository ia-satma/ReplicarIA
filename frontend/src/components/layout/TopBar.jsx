/**
 * TopBar.jsx - Barra superior minimalista
 *
 * Contiene:
 * - Logo y hamburguesa (solo móvil)
 * - Dropdown de usuario (perfil + logout)
 * - Se ajusta al ancho del sidebar
 */

import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LogOut, User, ChevronDown, Building2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '../../context/AuthContext';
import { MobileNav } from './MobileNav';
import { useSidebar } from './SidebarContext';

export function TopBar() {
  const { user, logout, isAuthenticated } = useAuth();
  const { isExpanded } = useSidebar();
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  // Cerrar dropdown al hacer click fuera
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!isAuthenticated) return null;

  const handleLogout = () => {
    setShowDropdown(false);
    logout();
    navigate('/login');
  };

  return (
    <header
      className={cn(
        'fixed top-0 right-0 z-30 h-16 bg-white dark:bg-gray-900',
        'border-b border-gray-200 dark:border-gray-800',
        'transition-all duration-300',
        // En desktop, ajustar al ancho del sidebar
        isExpanded ? 'lg:left-64' : 'lg:left-20',
        // En móvil, ocupar todo el ancho
        'left-0'
      )}
    >
      <div className="flex items-center justify-between h-full px-4">
        {/* Logo y hamburguesa para móvil */}
        <div className="flex items-center gap-3 lg:hidden">
          <MobileNav />
          <Link to="/">
            <img
              src="/logo-revisar.png"
              alt="Revisar.ia"
              className="h-6 object-contain"
            />
          </Link>
        </div>

        {/* Spacer para desktop */}
        <div className="hidden lg:block" />

        {/* User menu */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <div className="w-8 h-8 bg-gradient-to-br from-[#3CD366] to-[#34C759] rounded-full flex items-center justify-center text-white font-medium text-sm shadow-sm">
              {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <span className="text-sm text-gray-700 dark:text-gray-300 hidden sm:block max-w-[120px] truncate">
              {user?.full_name}
            </span>
            <ChevronDown
              className={cn(
                'w-4 h-4 text-gray-500 transition-transform duration-200',
                showDropdown && 'rotate-180'
              )}
            />
          </button>

          {/* Dropdown */}
          {showDropdown && (
            <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50">
              {/* User info */}
              <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                  {user?.full_name}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {user?.email}
                </p>
                {user?.company && (
                  <div className="flex items-center gap-1 mt-1">
                    <Building2 className="w-3 h-3 text-gray-400" />
                    <p className="text-xs text-gray-400 truncate">
                      {user?.company}
                    </p>
                  </div>
                )}
                {user?.role && (
                  <span className="inline-block mt-2 px-2 py-0.5 text-xs rounded-full bg-primary/10 text-primary">
                    {user?.role === 'super_admin'
                      ? 'Super Admin'
                      : user?.role === 'admin'
                      ? 'Administrador'
                      : 'Usuario'}
                  </span>
                )}
              </div>

              {/* Profile link */}
              <Link
                to="/perfil"
                onClick={() => setShowDropdown(false)}
                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <User className="w-4 h-4" />
                Mi Perfil
              </Link>

              {/* Logout */}
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Cerrar Sesión
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default TopBar;
