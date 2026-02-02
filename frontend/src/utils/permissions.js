/**
 * permissions.js - Sistema de permisos centralizado
 *
 * Proporciona helpers para verificar roles y permisos de usuario
 * de forma consistente en toda la aplicación.
 */

// Roles del sistema
export const ROLES = {
  USER: 'user',
  ADMIN: 'admin',
  SUPER_ADMIN: 'super_admin',
};

// Permisos granulares
export const PERMISSIONS = {
  VIEW_ADMIN: 'view_admin',
  VIEW_ADMIN_DOCS: 'view_admin_docs',
  VIEW_ADMIN_CLIENTS: 'view_admin_clients',
  MANAGE_EMPRESAS: 'manage_empresas',
  VIEW_METRICS: 'view_metrics',
  CREATE_PROJECTS: 'create_projects',
  VIEW_PROVEEDORES: 'view_proveedores',
  VIEW_BIBLIOTECA: 'view_biblioteca',
  VIEW_AGENTES: 'view_agentes',
};

// Mapeo de roles a permisos
const ROLE_PERMISSIONS = {
  [ROLES.USER]: [
    PERMISSIONS.CREATE_PROJECTS,
    PERMISSIONS.VIEW_METRICS,
    PERMISSIONS.VIEW_PROVEEDORES,
    PERMISSIONS.VIEW_BIBLIOTECA,
    PERMISSIONS.VIEW_AGENTES,
  ],
  [ROLES.ADMIN]: [
    PERMISSIONS.VIEW_ADMIN,
    PERMISSIONS.VIEW_ADMIN_DOCS,
    PERMISSIONS.MANAGE_EMPRESAS,
  ],
  [ROLES.SUPER_ADMIN]: Object.values(PERMISSIONS),
};

/**
 * Verifica si el usuario es super admin
 * @param {Object} user - Objeto de usuario
 * @returns {boolean}
 */
export const isSuperAdmin = (user) => {
  if (!user) return false;
  return user.role === ROLES.SUPER_ADMIN || user.is_superadmin === true;
};

/**
 * Verifica si el usuario es admin o super admin
 * @param {Object} user - Objeto de usuario
 * @returns {boolean}
 */
export const isAdmin = (user) => {
  if (!user) return false;
  return (
    user.role === ROLES.ADMIN ||
    user.role === ROLES.SUPER_ADMIN ||
    user.is_superadmin === true
  );
};

/**
 * Verifica si el usuario tiene un permiso específico
 * @param {Object} user - Objeto de usuario
 * @param {string} permission - Permiso a verificar
 * @returns {boolean}
 */
export function hasPermission(user, permission) {
  if (!user) return false;

  // Super admin tiene todos los permisos
  if (isSuperAdmin(user)) return true;

  const userRole = user.role || ROLES.USER;

  // Obtener permisos del rol
  let permissions = ROLE_PERMISSIONS[userRole] || [];

  // Admin hereda permisos de user
  if (userRole === ROLES.ADMIN) {
    permissions = [...ROLE_PERMISSIONS[ROLES.USER], ...permissions];
  }

  return permissions.includes(permission);
}

/**
 * Obtiene el rol normalizado del usuario
 * @param {Object} user - Objeto de usuario
 * @returns {string}
 */
export const getUserRole = (user) => {
  if (!user) return null;
  if (user.is_superadmin) return ROLES.SUPER_ADMIN;
  return user.role || ROLES.USER;
};

export default {
  ROLES,
  PERMISSIONS,
  isAdmin,
  isSuperAdmin,
  hasPermission,
  getUserRole,
};
