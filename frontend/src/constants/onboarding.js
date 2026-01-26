export const AGENTS = {
  ARCHIVO: {
    id: 'ARCHIVO',
    name: 'Archivo',
    displayName: 'Asistente de Onboarding',
    avatar: '📁',
    color: '#6366f1',
  },
  A1_ESTRATEGIA: {
    id: 'A1_ESTRATEGIA',
    name: 'María Rodríguez',
    displayName: 'María Rodríguez',
    role: 'Sponsor/Estrategia',
    avatar: '👩‍💼',
    color: '#8b5cf6',
  },
  A3_FISCAL: {
    id: 'A3_FISCAL',
    name: 'Laura Sánchez',
    displayName: 'Laura Sánchez',
    role: 'Especialista Fiscal',
    avatar: '👩‍⚖️',
    color: '#10b981',
  },
  A6_PROVEEDOR: {
    id: 'A6_PROVEEDOR',
    name: 'Ana García',
    displayName: 'Ana García',
    role: 'Verificación Proveedores',
    avatar: '🔍',
    color: '#f59e0b',
  },
};

export const ENTITY_TYPES = {
  CLIENTE: 'cliente',
  PROVEEDOR: 'proveedor',
};

export const FILE_STATUS = {
  PENDING: 'pending',
  ANALYZING: 'analyzing',
  ANALYZED: 'analyzed',
  UPLOADING: 'uploading',
  UPLOADED: 'uploaded',
  ERROR: 'error',
};

export const ALLOWED_FILE_EXTENSIONS = [
  '.pdf',
  '.docx',
  '.xlsx',
  '.txt',
  '.xml',
  '.png',
  '.jpg',
  '.jpeg',
];

export const MAX_FILE_SIZE = 50 * 1024 * 1024;

export const SYSTEM_MESSAGES = {
  WELCOME: '¡Hola! Soy tu asistente de onboarding. ¿Vamos a registrar un cliente o un proveedor?',
  FILE_UPLOADED: 'Archivo recibido. Analizando con IA...',
  ANALYSIS_COMPLETE: 'He extraído la siguiente información del documento. Por favor confirma que es correcta.',
  EFOS_CHECKING: 'Verificando RFC en la Lista 69-B del SAT...',
  EFOS_CLEAR: 'El RFC no aparece en la Lista 69-B. Proveedor verificado.',
  EFOS_WARNING: 'ALERTA: El RFC aparece en la Lista 69-B del SAT.',
  COMPLETE: '¡Listo! La entidad ha sido registrada exitosamente.',
};

export const QUICK_SUGGESTIONS = {
  welcome: [
    { text: 'Registrar cliente', value: 'cliente' },
    { text: 'Registrar proveedor', value: 'proveedor' },
  ],
  documents: [
    { text: 'Subir constancia fiscal', action: 'upload_constancia' },
    { text: 'Subir identificación', action: 'upload_id' },
    { text: 'Subir contrato', action: 'upload_contrato' },
  ],
};

export const ONBOARDING_STEPS = [
  {
    id: 'welcome',
    botMessage: '¡Hola! Soy ARCHIVO, tu archivista digital. Te ayudaré a configurar tu empresa en Revisar.ia para que puedas auditar tus servicios intangibles antes de que lo haga el SAT. ¿Comenzamos?',
    expectsResponse: false,
    nextDelay: 2000
  },
  {
    id: 'company_name',
    botMessage: '¿Cuál es el nombre o razón social de tu empresa?',
    field: 'companyName',
    expectsResponse: true
  },
  {
    id: 'rfc',
    botMessage: 'Perfecto. Ahora necesito el RFC de la empresa.',
    field: 'rfc',
    expectsResponse: true,
    validate: (value) => /^[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}$/i.test(value.trim())
  },
  {
    id: 'industry',
    botMessage: '¿En qué industria opera tu empresa? (ej: Construcción, Tecnología, Servicios Financieros, etc.)',
    field: 'industry',
    expectsResponse: true
  },
  {
    id: 'annual_revenue',
    botMessage: '¿Cuál es la facturación anual aproximada de la empresa? (en millones MXN)',
    field: 'annualRevenue',
    expectsResponse: true
  },
  {
    id: 'main_services',
    botMessage: '¿Cuáles son los principales tipos de servicios intangibles que contratan? (ej: Consultoría, Software, Marketing, etc.)',
    field: 'mainServices',
    expectsResponse: true
  },
  {
    id: 'documents',
    botMessage: 'Excelente. Si tienes documentos de muestra como contratos, facturas o políticas internas, puedes subirlos ahora. Esto me ayudará a personalizar mejor el sistema. Puedes subir archivos o escribir "continuar" para omitir este paso.',
    field: 'documents',
    expectsResponse: true,
    allowFiles: true
  },
  {
    id: 'contact_email',
    botMessage: '¿Cuál es el correo electrónico del responsable fiscal o administrativo?',
    field: 'contactEmail',
    expectsResponse: true,
    validate: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim())
  },
  {
    id: 'complete',
    botMessage: '¡Listo! He registrado toda la información de tu empresa. Tu cuenta está configurada y lista para comenzar a auditar servicios intangibles. ¿Te gustaría crear tu primer proyecto ahora?',
    expectsResponse: false,
    showActions: true
  }
];
