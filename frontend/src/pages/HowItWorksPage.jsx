import React, { useState } from 'react';
import {
  PlayCircle, ArrowRight, CheckCircle2, AlertTriangle, Lock,
  FileText, Users, Scale, Shield, BarChart3, Briefcase,
  FileCheck, CreditCard, ClipboardCheck, TrendingUp,
  ChevronDown, ChevronUp, Bot, Building2
} from 'lucide-react';

// Datos de las fases F0-F9
const fasesData = [
  {
    id: 'F0',
    nombre: 'Aprobación y BEE',
    descripcion: 'Documentar la razón de negocios y el beneficio económico esperado',
    color: 'bg-blue-500',
    icon: Briefcase,
    candado: false,
    documentos: ['Ficha de Proyecto (SIB)', 'Matriz BEE', 'Justificación Estratégica'],
    agentes: ['A1_ESTRATEGIA', 'A3_FISCAL'],
    detalle: 'El proyecto inicia con una Ficha PO/SIB donde se captura la razón de negocios, el objetivo, el tipo de beneficio económico esperado y su vinculación con los pilares estratégicos de la empresa.'
  },
  {
    id: 'F1',
    nombre: 'SOW / Contrato Base',
    descripcion: 'Establecer alcance, entregables y términos contractuales',
    color: 'bg-indigo-500',
    icon: FileText,
    candado: false,
    documentos: ['Contrato de Servicios', 'SOW Detallado', 'Cronograma'],
    agentes: ['A4_LEGAL', 'A2_PMO'],
    detalle: 'Se genera el SOW/Contrato con objeto, alcance, entregables específicos, metodología, cronograma y esquema de honorarios. El agente Legal (A4) revisa los términos contractuales.'
  },
  {
    id: 'F2',
    nombre: 'Validación Previa',
    descripcion: 'Candado de inicio: presupuesto y revisiones obligatorias',
    color: 'bg-yellow-500',
    icon: Lock,
    candado: true,
    documentos: ['Confirmación Presupuesto', 'VoBo Fiscal Preliminar'],
    agentes: ['A5_FINANZAS', 'A3_FISCAL'],
    detalle: 'CANDADO DE INICIO: No se puede avanzar sin confirmar presupuesto disponible y revisiones humanas obligatorias para operaciones de alto monto o riesgo.'
  },
  {
    id: 'F3',
    nombre: 'Ejecución Inicial',
    descripcion: 'Arranque del proyecto y primeras entregas',
    color: 'bg-green-500',
    icon: PlayCircle,
    candado: false,
    documentos: ['Minuta de Kick-off', 'Primer Borrador (V1)', 'Cronograma Detallado'],
    agentes: ['A2_PMO', 'A6_PROVEEDOR'],
    detalle: 'Se carga la minuta de kick-off, el primer borrador del entregable y el cronograma detallado. El proveedor comienza la ejecución del servicio.'
  },
  {
    id: 'F4',
    nombre: 'Revisión Iterativa',
    descripcion: 'Versiones intermedias y ajustes',
    color: 'bg-teal-500',
    icon: ClipboardCheck,
    candado: false,
    documentos: ['Versiones Intermedias', 'Minutas de Revisión', 'Comentarios/Ajustes'],
    agentes: ['A1_ESTRATEGIA', 'A3_FISCAL', 'A5_FINANZAS'],
    detalle: 'Se generan versiones V1.1, V1.2, etc. donde los diferentes agentes (Estrategia, Fiscal, Finanzas) solicitan ajustes específicos al proveedor.'
  },
  {
    id: 'F5',
    nombre: 'Entrega Final',
    descripcion: 'Aceptación técnica del servicio',
    color: 'bg-emerald-500',
    icon: FileCheck,
    candado: false,
    documentos: ['Informe Final', 'Modelo Paramétrico', 'Manual Metodológico', 'Acta de Aceptación'],
    agentes: ['A1_ESTRATEGIA', 'A2_PMO'],
    detalle: 'El proveedor carga la versión final de todos los entregables. El área usuaria firma el Acta de Aceptación Técnica validando que se cumplió el alcance.'
  },
  {
    id: 'F6',
    nombre: 'VoBo Fiscal/Legal',
    descripcion: 'Candado de aprobación: materialidad y compliance',
    color: 'bg-orange-500',
    icon: Lock,
    candado: true,
    documentos: ['Matriz de Materialidad', 'VoBo Fiscal', 'VoBo Legal', 'Contrato Final'],
    agentes: ['A3_FISCAL', 'A4_LEGAL'],
    detalle: 'CANDADO FISCAL/LEGAL: No se puede facturar sin: Matriz de Materialidad >70%, contrato/anexo coherente, VoBo Fiscal y VoBo Legal aprobados.'
  },
  {
    id: 'F7',
    nombre: 'Auditoría Interna',
    descripcion: 'Verificación de proceso y expediente completo',
    color: 'bg-purple-500',
    icon: Shield,
    candado: false,
    documentos: ['Informe de Auditoría', 'Checklist de Proceso', 'Defense File'],
    agentes: ['A7_DEFENSA', 'A2_PMO'],
    detalle: 'Auditoría interna verifica que se siguió el proceso F0-F6, que el expediente (Defense File) está completo y listo para potenciales revisiones del SAT.'
  },
  {
    id: 'F8',
    nombre: 'CFDI y Pago',
    descripcion: 'Candado de pago: 3-way match y liberación',
    color: 'bg-red-500',
    icon: Lock,
    candado: true,
    documentos: ['CFDI Específico', 'Comprobante de Pago', '3-Way Match'],
    agentes: ['A5_FINANZAS', 'A3_FISCAL'],
    detalle: 'CANDADO DE PAGO: El CFDI debe ser específico (no genérico), y debe existir 3-way match (Contrato = CFDI = Pago). Sin esto, no se libera el pago.'
  },
  {
    id: 'F9',
    nombre: 'Post-Implementación',
    descripcion: 'Seguimiento del BEE y cierre',
    color: 'bg-cyan-500',
    icon: TrendingUp,
    candado: false,
    documentos: ['Reporte de Uso', 'Medición de KPIs', 'BEE Alcanzado vs Esperado'],
    agentes: ['A1_ESTRATEGIA', 'A5_FINANZAS'],
    detalle: 'En 12-24 meses se documenta: cuántas decisiones se apoyaron en el servicio, qué ajustes se hicieron con base en sus resultados, y se compara BEE esperado vs alcanzado.'
  }
];

// Caso de ejemplo
const casoEjemplo = {
  nombre: "Estudio Prospectivo Macroeconómico y Regulatorio 2026",
  folio: "PROJ-0D7301D0",
  empresa: "Grupo Inmobiliario Premium",
  monto: "$1,250,000 MXN",
  tipologia: "CONSULTORIA_MACRO_MERCADO",
  proveedor: "Consultora Estratégica S.A.",
  fases: [
    {
      fase: 'F0',
      titulo: 'Razón de Negocios',
      descripcion: 'El estudio permitirá decidir en qué zonas y segmentos de NL y Nayarit concentrar CAPEX 2026-2028, en un entorno de nearshoring y presiones de costos.',
      bee: 'Mitigación de riesgos + optimización de CAPEX. Horizonte: 24-36 meses.',
      status: 'completado'
    },
    {
      fase: 'F1',
      titulo: 'Contrato/SOW',
      descripcion: 'SOW con metodología PESTEL, escenarios, fuentes. Entregables: informe final, modelo paramétrico, dashboard, manual metodológico.',
      status: 'completado'
    },
    {
      fase: 'F2',
      titulo: 'Candado Inicio',
      descripcion: 'Presupuesto confirmado por Finanzas. VoBo preliminar de Fiscal dado el monto ($1.25M).',
      status: 'completado',
      candado: true
    },
    {
      fase: 'F5',
      titulo: 'Entrega Final',
      descripcion: 'Versión V1.2 del estudio tras comentarios de Estrategia y Fiscal. Acta de Aceptación firmada por Dirección.',
      status: 'completado'
    },
    {
      fase: 'F6',
      titulo: 'VoBo Fiscal/Legal',
      descripcion: 'Matriz de Materialidad: 85%. VoBo Fiscal: APROBAR. VoBo Legal: APROBAR. Risk Score: 35 (BAJO).',
      status: 'completado',
      candado: true
    },
    {
      fase: 'F8',
      titulo: '3-Way Match',
      descripcion: 'CFDI específico emitido. 3-way match: Contrato = CFDI = Pago COMPLETO.',
      status: 'completado',
      candado: true
    }
  ]
};

// Componente de fase en timeline
const FaseTimeline = ({ fase, isLast, isExpanded, onToggle }) => {
  const Icon = fase.icon;

  return (
    <div className="relative">
      {/* Línea conectora */}
      {!isLast && (
        <div className="absolute left-5 top-12 w-0.5 h-full bg-gray-200"></div>
      )}

      <div className="flex gap-4">
        {/* Círculo */}
        <div className={`relative z-10 flex-shrink-0 w-10 h-10 rounded-full ${fase.color} flex items-center justify-center text-white`}>
          {fase.candado ? <Lock className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
        </div>

        {/* Contenido */}
        <div className="flex-1 pb-8">
          <button
            onClick={onToggle}
            className="w-full text-left focus:outline-none"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm text-gray-500">{fase.id}</span>
                  {fase.candado && (
                    <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">
                      Candado
                    </span>
                  )}
                </div>
                <h3 className="font-medium text-gray-900">{fase.nombre}</h3>
                <p className="text-sm text-gray-500">{fase.descripcion}</p>
              </div>
              {isExpanded ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </div>
          </button>

          {isExpanded && (
            <div className="mt-4 bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-700 mb-4">{fase.detalle}</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Documentos */}
                <div>
                  <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">
                    Documentos Requeridos
                  </h4>
                  <ul className="space-y-1">
                    {fase.documentos.map((doc, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-gray-700">
                        <FileText className="w-4 h-4 text-gray-400" />
                        {doc}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Agentes */}
                <div>
                  <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">
                    Agentes Responsables
                  </h4>
                  <ul className="space-y-1">
                    {fase.agentes.map((agente, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-gray-700">
                        <Bot className="w-4 h-4 text-blue-500" />
                        {agente}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Componente principal
const HowItWorksPage = () => {
  const [expandedFase, setExpandedFase] = useState(null);
  const [showCasoEjemplo, setShowCasoEjemplo] = useState(false);

  const toggleFase = (id) => {
    setExpandedFase(expandedFase === id ? null : id);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <h1 className="text-4xl font-bold mb-4">¿Cómo Funciona REVISAR.IA?</h1>
            <p className="text-xl text-indigo-100 max-w-3xl mx-auto">
              Sistema de auditoría preventiva que asegura la materialidad y defendibilidad
              de tus servicios e intangibles a través del flujo F0-F9.
            </p>
          </div>
        </div>
      </div>

      {/* Los 4 Pilares */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { nombre: 'Razón de Negocios', icon: Briefcase, articulo: 'Art. 5-A CFF', color: 'bg-blue-500' },
            { nombre: 'Beneficio Económico', icon: BarChart3, articulo: 'Art. 5-A CFF', color: 'bg-green-500' },
            { nombre: 'Materialidad', icon: FileCheck, articulo: 'Art. 69-B CFF', color: 'bg-purple-500' },
            { nombre: 'Trazabilidad', icon: Shield, articulo: 'NOM-151', color: 'bg-orange-500' }
          ].map((pilar, idx) => (
            <div key={idx} className="bg-white rounded-xl shadow-lg p-6">
              <div className={`w-12 h-12 ${pilar.color} rounded-lg flex items-center justify-center mb-4`}>
                <pilar.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="font-semibold text-gray-900">{pilar.nombre}</h3>
              <p className="text-sm text-gray-500 mt-1">{pilar.articulo}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Flujo F0-F9 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Flujo de Validación F0-F9
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Cada proyecto pasa por 10 fases, incluyendo 3 candados obligatorios (F2, F6, F8)
            que requieren validación humana antes de continuar.
          </p>
        </div>

        {/* Timeline */}
        <div className="max-w-3xl mx-auto">
          {fasesData.map((fase, idx) => (
            <FaseTimeline
              key={fase.id}
              fase={fase}
              isLast={idx === fasesData.length - 1}
              isExpanded={expandedFase === fase.id}
              onToggle={() => toggleFase(fase.id)}
            />
          ))}
        </div>
      </div>

      {/* Caso de Ejemplo */}
      <div className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Caso de Ejemplo Completo
            </h2>
            <p className="text-gray-600">
              Mira cómo un proyecto real recorre todas las fases de REVISAR.IA
            </p>
          </div>

          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl p-8">
            {/* Header del caso */}
            <div className="flex items-start gap-6 mb-8">
              <div className="p-4 bg-white rounded-xl shadow-sm">
                <Building2 className="w-8 h-8 text-indigo-600" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900">{casoEjemplo.nombre}</h3>
                <div className="flex flex-wrap gap-4 mt-2 text-sm text-gray-600">
                  <span className="flex items-center gap-1">
                    <span className="font-mono text-xs bg-gray-200 px-2 py-0.5 rounded">
                      {casoEjemplo.folio}
                    </span>
                  </span>
                  <span>{casoEjemplo.empresa}</span>
                  <span className="font-medium text-indigo-600">{casoEjemplo.monto}</span>
                </div>
                <div className="mt-2">
                  <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm">
                    {casoEjemplo.tipologia}
                  </span>
                </div>
              </div>
            </div>

            {/* Toggle caso */}
            <button
              onClick={() => setShowCasoEjemplo(!showCasoEjemplo)}
              className="w-full flex items-center justify-center gap-2 py-3 bg-white rounded-lg shadow-sm hover:bg-gray-50 transition-colors"
            >
              {showCasoEjemplo ? (
                <>
                  <ChevronUp className="w-5 h-5" />
                  Ocultar detalles
                </>
              ) : (
                <>
                  <ChevronDown className="w-5 h-5" />
                  Ver recorrido completo F0-F9
                </>
              )}
            </button>

            {showCasoEjemplo && (
              <div className="mt-6 space-y-4">
                {casoEjemplo.fases.map((fase, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-lg ${
                      fase.status === 'completado' ? 'bg-green-50 border border-green-200' : 'bg-white border border-gray-200'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {fase.status === 'completado' ? (
                        <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      ) : (
                        <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm text-gray-500">{fase.fase}</span>
                          <h4 className="font-medium text-gray-900">{fase.titulo}</h4>
                          {fase.candado && (
                            <Lock className="w-4 h-4 text-orange-500" />
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{fase.descripcion}</p>
                        {fase.bee && (
                          <p className="text-sm text-indigo-600 mt-2 bg-indigo-50 px-3 py-1 rounded inline-block">
                            <strong>BEE:</strong> {fase.bee}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}

                {/* Defense File final */}
                <div className="mt-6 p-6 bg-gradient-to-r from-green-500 to-teal-500 rounded-xl text-white">
                  <div className="flex items-center gap-4">
                    <Shield className="w-10 h-10" />
                    <div>
                      <h4 className="font-bold text-lg">Defense File Completado</h4>
                      <p className="text-green-100">
                        Índice de Defendibilidad: <span className="font-bold">85.5%</span>
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div className="bg-white/20 rounded-lg p-3">
                      <div className="text-2xl font-bold">90%</div>
                      <div className="text-xs text-green-100">Razón Negocios</div>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3">
                      <div className="text-2xl font-bold">80%</div>
                      <div className="text-xs text-green-100">BEE</div>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3">
                      <div className="text-2xl font-bold">85%</div>
                      <div className="text-xs text-green-100">Materialidad</div>
                    </div>
                    <div className="bg-white/20 rounded-lg p-3">
                      <div className="text-2xl font-bold">88%</div>
                      <div className="text-xs text-green-100">Trazabilidad</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Rol de la IA */}
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <Bot className="w-8 h-8 text-teal-400" />
                <h2 className="text-3xl font-bold">El Rol de la IA</h2>
              </div>
              <p className="text-gray-300 mb-6">
                REVISAR.IA utiliza inteligencia artificial como <strong>herramienta auxiliar</strong>,
                no como sustituto del criterio humano. La IA se encarga de:
              </p>
              <ul className="space-y-3">
                {[
                  'Calcular risk_scores objetivos y reproducibles',
                  'Aplicar checklists normativos automáticamente',
                  'Construir Matrices de Materialidad',
                  'Organizar Defense Files estructurados',
                  'Detectar señales de riesgo EFOS/69-B'
                ].map((item, idx) => (
                  <li key={idx} className="flex items-center gap-3">
                    <CheckCircle2 className="w-5 h-5 text-teal-400 flex-shrink-0" />
                    <span className="text-gray-200">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-white/10 rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <Scale className="w-6 h-6 text-purple-400" />
                <span className="text-purple-300 text-sm">Jurisprudencia SCJN</span>
              </div>
              <blockquote className="text-lg text-gray-100 italic">
                "La inteligencia artificial puede emplearse válidamente como herramienta auxiliar,
                siempre que el núcleo decisorio permanezca en manos humanas."
              </blockquote>
              <div className="mt-4 text-sm text-gray-400">
                Tesis II.2o.C. J/1 K (12a.) | Registro: 2031639
              </div>
              <div className="mt-6 p-4 bg-purple-500/20 rounded-lg">
                <p className="text-sm text-purple-200">
                  Las decisiones fiscales y legales (aprobar, pagar, deducir) siempre las toman
                  personas: Dirección, Fiscal, Legal, Finanzas.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            ¿Listo para comenzar?
          </h2>
          <p className="text-indigo-100 mb-8 max-w-2xl mx-auto">
            Empieza a proteger tus deducciones con el sistema de auditoría preventiva
            más avanzado de México.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/nuevo-proyecto"
              className="inline-flex items-center justify-center gap-2 px-8 py-3 bg-white text-indigo-600 rounded-lg font-medium hover:bg-indigo-50 transition-colors"
            >
              Crear nuevo proyecto
              <ArrowRight className="w-5 h-5" />
            </a>
            <a
              href="/base-legal"
              className="inline-flex items-center justify-center gap-2 px-8 py-3 border-2 border-white text-white rounded-lg font-medium hover:bg-white/10 transition-colors"
            >
              Ver base jurídica
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HowItWorksPage;
