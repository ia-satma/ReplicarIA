import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const VideoCarousel = ({ videos }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);
  const [isVideoPlaying, setIsVideoPlaying] = useState(false);
  const iframeRefs = useRef([]);

  const nextSlide = useCallback(() => {
    setCurrentIndex((prev) => (prev + 1) % videos.length);
  }, [videos.length]);

  const prevSlide = () => {
    setCurrentIndex((prev) => (prev - 1 + videos.length) % videos.length);
  };

  const goToSlide = (index) => {
    setCurrentIndex(index);
    setIsAutoPlaying(false);
    setTimeout(() => setIsAutoPlaying(true), 10000);
  };

  // Listen for Vimeo postMessage events to detect play/pause
  useEffect(() => {
    const handleMessage = (event) => {
      // Check if it's from Vimeo
      if (event.origin && event.origin.includes('vimeo.com')) {
        try {
          const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;

          if (data.event === 'play') {
            setIsVideoPlaying(true);
            setIsAutoPlaying(false);
          } else if (data.event === 'pause' || data.event === 'ended') {
            setIsVideoPlaying(false);
            setIsAutoPlaying(true);
          }
        } catch (e) {
          // Not a JSON message, ignore
        }
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  // Autoplay effect - only run when not playing video
  useEffect(() => {
    if (!isAutoPlaying || isVideoPlaying) return;
    const interval = setInterval(nextSlide, 8000);
    return () => clearInterval(interval);
  }, [isAutoPlaying, isVideoPlaying, nextSlide]);

  return (
    <div className="relative">
      <div className="bg-white/80 backdrop-blur-sm border border-gray-200 shadow-xl p-2 sm:p-3 rounded-2xl sm:rounded-3xl overflow-hidden">
        <div className="relative overflow-hidden rounded-xl sm:rounded-2xl">
          <div
            className="flex transition-transform duration-700 ease-in-out"
            style={{ transform: `translateX(-${currentIndex * 100}%)` }}
          >
            {videos.map((video, index) => (
              <div key={index} className="w-full flex-shrink-0">
                <div className="relative pb-[56.25%] h-0">
                  <iframe
                    ref={(el) => (iframeRefs.current[index] = el)}
                    src={`https://player.vimeo.com/video/${video.id}?badge=0&autopause=0&player_id=0&app_id=58479&api=1`}
                    frameBorder="0"
                    allow="autoplay; fullscreen; picture-in-picture; clipboard-write"
                    className="absolute top-0 left-0 w-full h-full"
                    title={video.title}
                  ></iframe>
                </div>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={prevSlide}
          className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-white/90 hover:bg-white rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-110"
          aria-label="Video anterior"
        >
          <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <button
          onClick={nextSlide}
          className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-white/90 hover:bg-white rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-110"
          aria-label="Video siguiente"
        >
          <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      <div className="flex justify-center gap-2 mt-4">
        {videos.map((video, index) => (
          <button
            key={index}
            onClick={() => goToSlide(index)}
            className={`w-3 h-3 rounded-full transition-all ${index === currentIndex
                ? 'bg-[#7FEDD8] w-8'
                : 'bg-gray-300 hover:bg-gray-400'
              }`}
            aria-label={`Ir a video ${index + 1}`}
          />
        ))}
      </div>

      <p className="text-center text-sm text-gray-500 mt-2">
        {videos[currentIndex]?.title}
        {isVideoPlaying && (
          <span className="ml-2 inline-flex items-center text-red-500">
            <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse mr-1"></span>
            Reproduciendo
          </span>
        )}
      </p>
    </div>
  );
};

const EmbeddedFacturarIA = () => {
  const [showChat, setShowChat] = useState(false);
  const [mensajes, setMensajes] = useState([
    {
      id: 'welcome',
      tipo: 'asistente',
      contenido: '¡Hola! Soy Facturar.IA. ¿Qué servicio necesitas facturar?',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensajes]);

  const handleEnviar = async () => {
    if (!input.trim() || loading) return;

    const userMsg = {
      id: Date.now().toString(),
      tipo: 'usuario',
      contenido: input.trim(),
      timestamp: new Date()
    };
    setMensajes(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/asistente-facturacion/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mensaje: userMsg.contenido, historial: mensajes })
      });
      const data = await response.json();

      setMensajes(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        tipo: 'asistente',
        contenido: data.respuesta || 'Lo siento, no pude procesar tu solicitud.',
        sugerencias: data.sugerencias,
        timestamp: new Date()
      }]);
    } catch (error) {
      setMensajes(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        tipo: 'asistente',
        contenido: 'Error de conexión. Por favor intenta de nuevo.',
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  if (!showChat) {
    return (
      <button
        onClick={() => setShowChat(true)}
        className="w-full bg-white/20 hover:bg-white/30 text-white font-semibold py-4 px-6 rounded-xl transition-all flex items-center justify-center gap-3 group"
      >
        <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <span>Iniciar Chat con Facturar.IA</span>
      </button>
    );
  }

  return (
    <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/20 overflow-hidden">
      <div className="flex items-center justify-between p-3 border-b border-white/10">
        <span className="text-white/90 text-sm font-medium">Chat con Facturar.IA</span>
        <button
          onClick={() => setShowChat(false)}
          className="text-white/60 hover:text-white p-1"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="h-48 overflow-y-auto p-3 space-y-2">
        {mensajes.map(msg => (
          <div key={msg.id} className={`flex ${msg.tipo === 'usuario' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${msg.tipo === 'usuario'
                ? 'bg-blue-600 text-white'
                : 'bg-white/10 text-white/90'
              }`}>
              {msg.contenido}
              {msg.sugerencias?.length > 0 && (
                <div className="mt-2 pt-2 border-t border-white/20">
                  {msg.sugerencias.slice(0, 2).map((s, i) => (
                    <div key={i} className="text-xs text-emerald-300 mt-1">
                      <span className="font-mono">{s.claveSAT}</span> - {s.descripcion}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white/10 rounded-lg px-3 py-2">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-white/50 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-white/50 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-white/50 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-3 border-t border-white/10">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleEnviar()}
            placeholder="Ej: Servicios de marketing digital..."
            className="flex-1 bg-white/10 text-white placeholder-white/40 rounded-lg px-3 py-2 text-sm border border-white/20 focus:border-emerald-400/50 focus:outline-none"
          />
          <button
            onClick={handleEnviar}
            disabled={loading || !input.trim()}
            className="bg-emerald-500 hover:bg-emerald-400 disabled:bg-emerald-500/50 text-white px-4 py-2 rounded-lg transition"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

const ShieldIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const BotIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="10" rx="2" />
    <circle cx="12" cy="5" r="2" />
    <path d="M12 7v4" />
    <line x1="8" y1="16" x2="8" y2="16" />
    <line x1="16" y1="16" x2="16" y2="16" />
  </svg>
);

const LockIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

const ChartIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10" />
    <line x1="12" y1="20" x2="12" y2="4" />
    <line x1="6" y1="20" x2="6" y2="14" />
  </svg>
);

const TargetIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="6" />
    <circle cx="12" cy="12" r="2" />
  </svg>
);

const ScaleIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 3v18" />
    <path d="M1 7l5 5-5 5" />
    <path d="M23 7l-5 5 5 5" />
    <path d="M4 12h16" />
  </svg>
);

const DollarIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="1" x2="12" y2="23" />
    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
  </svg>
);

const SettingsIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);

const FileTextIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <polyline points="10 9 9 9 8 9" />
  </svg>
);

const StarIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
  </svg>
);

const CheckCircleIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </svg>
);

const TagIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" />
    <line x1="7" y1="7" x2="7.01" y2="7" />
  </svg>
);

const EyeIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const LayersIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="12 2 2 7 12 12 22 7 12 2" />
    <polyline points="2 17 12 22 22 17" />
    <polyline points="2 12 12 17 22 12" />
  </svg>
);

const AlertTriangleIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
);

const mainAgents = [
  {
    id: 'A1',
    name: 'A1-Estrategia',
    persona: 'María',
    role: 'Validador Estratégico',
    description: 'Alineación BEE, Razón de Negocios Art. 5-A CFF',
    color: 'from-purple-500 to-violet-600',
    borderColor: 'border-purple-500/30',
    textColor: 'text-purple-600',
    icon: StarIcon
  },
  {
    id: 'A2',
    name: 'A2-PMO',
    persona: 'Carlos',
    role: 'Orquestador Central',
    description: 'Guardián del POE, gestiona estados F0-F9',
    color: 'from-blue-500 to-cyan-600',
    borderColor: 'border-blue-500/30',
    textColor: 'text-blue-600',
    icon: TargetIcon
  },
  {
    id: 'A3',
    name: 'A3-Fiscal',
    persona: 'Laura',
    role: 'Motor de Cumplimiento',
    description: 'Genera SIB, valida materialidad fiscal',
    color: 'from-green-500 to-emerald-600',
    borderColor: 'border-green-500/30',
    textColor: 'text-green-600',
    icon: DollarIcon
  },
  {
    id: 'A4',
    name: 'A4-Legal',
    persona: 'Gestor IA',
    role: 'Validador Contractual',
    description: 'SOW, Fecha Cierta NOM-151',
    color: 'from-amber-500 to-yellow-600',
    borderColor: 'border-amber-500/30',
    textColor: 'text-amber-600',
    icon: ScaleIcon
  },
  {
    id: 'A5',
    name: 'A5-Finanzas',
    persona: 'Roberto',
    role: 'Controlador Financiero',
    description: '3-Way Match (CFDI, SPEI)',
    color: 'from-red-500 to-rose-600',
    borderColor: 'border-red-500/30',
    textColor: 'text-red-600',
    icon: ChartIcon
  },
  {
    id: 'A6',
    name: 'A6-Proveedor',
    persona: 'Ana',
    role: 'Ejecutor del Servicio',
    description: 'Entregables y logs',
    color: 'from-teal-500 to-cyan-600',
    borderColor: 'border-teal-500/30',
    textColor: 'text-teal-600',
    icon: SettingsIcon
  },
  {
    id: 'A7',
    name: 'A7-Defensa',
    persona: 'Sistema',
    role: 'Generador Defense File',
    description: 'Compila expediente defensivo completo',
    color: 'from-indigo-500 to-purple-600',
    borderColor: 'border-indigo-500/30',
    textColor: 'text-indigo-600',
    icon: ShieldIcon
  }
];

const subAgents = [
  {
    id: 'SUB_TIPIFICACION',
    name: 'SUB_TIPIFICACION',
    role: 'Clasificador de Proyectos',
    description: 'Asigna tipología (8 tipos) y checklist',
    color: 'from-sky-400 to-blue-500',
    icon: TagIcon
  },
  {
    id: 'SUB_MATERIALIDAD',
    name: 'SUB_MATERIALIDAD',
    role: 'Monitor de Evidencia',
    description: 'Umbral 80% para VBC, bloquea si incompleto',
    color: 'from-emerald-400 to-green-500',
    icon: EyeIcon
  },
  {
    id: 'SUB_RIESGOS',
    name: 'SUB_RIESGOS_ESPECIALES',
    role: 'Detector de Riesgos',
    description: 'EFOS, partes relacionadas, TP, esquemas',
    color: 'from-orange-400 to-red-500',
    icon: AlertTriangleIcon
  },
  {
    id: 'A7_DEFENSA',
    name: 'A7_DEFENSA',
    role: 'Generador de Defensa',
    description: 'Índice de defendibilidad 0-100',
    color: 'from-violet-400 to-purple-500',
    icon: ShieldIcon
  }
];

const poePhases = [
  { id: 'F0', name: 'Aprobación BEE', hasLock: false },
  { id: 'F1', name: 'Pre-contratación', hasLock: false },
  { id: 'F2', name: 'Validación Inicio', hasLock: true, lockReason: 'No ejecutar sin BEE/SOW/aprobaciones' },
  { id: 'F3', name: 'Ejecución Inicial', hasLock: false },
  { id: 'F4', name: 'Revisión Iterativa', hasLock: false },
  { id: 'F5', name: 'Entrega Final', hasLock: false },
  { id: 'F6', name: 'VBC Fiscal/Legal', hasLock: true, lockReason: 'No emitir CFDI sin VBC y 80%+ materialidad' },
  { id: 'F7', name: 'Auditoría Interna', hasLock: false },
  { id: 'F8', name: 'CFDI y Pago', hasLock: true, lockReason: 'No pagar sin 3-way match' },
  { id: 'F9', name: 'Post-implementación', hasLock: false }
];

const evaluationPillars = [
  {
    name: 'Razón de Negocios',
    article: 'Art. 5-A CFF',
    points: 25,
    description: '¿El servicio tiene motivación económica real?',
    color: 'from-blue-500 to-indigo-600',
    icon: TargetIcon
  },
  {
    name: 'Beneficio Económico Esperado',
    article: 'BEE',
    points: 25,
    description: '¿Qué valor se espera: ahorros, ingresos, mitigación de riesgos?',
    color: 'from-green-500 to-emerald-600',
    icon: ChartIcon
  },
  {
    name: 'Materialidad',
    article: 'Art. 69-B CFF',
    points: 25,
    description: '¿Hay prueba de que el servicio se prestó?',
    color: 'from-purple-500 to-violet-600',
    icon: FileTextIcon
  },
  {
    name: 'Trazabilidad',
    article: 'NOM-151',
    points: 25,
    description: '¿Los documentos están fechados e íntegros?',
    color: 'from-amber-500 to-orange-600',
    icon: LayersIcon
  }
];

const RiskGauge = () => {
  const [hoveredSection, setHoveredSection] = useState(null);

  const sections = [
    { range: '0-29', label: 'BAJO', color: '#10B981', startAngle: -90, endAngle: -45 },
    { range: '30-49', label: 'MODERADO', color: '#F59E0B', startAngle: -45, endAngle: 0 },
    { range: '50-69', label: 'ALTO', color: '#F97316', startAngle: 0, endAngle: 45 },
    { range: '70-100', label: 'CRÍTICO', color: '#EF4444', startAngle: 45, endAngle: 90 }
  ];

  const polarToCartesian = (centerX, centerY, radius, angleInDegrees) => {
    const angleInRadians = (angleInDegrees * Math.PI) / 180.0;
    return {
      x: centerX + radius * Math.cos(angleInRadians),
      y: centerY + radius * Math.sin(angleInRadians)
    };
  };

  const describeArc = (x, y, radius, startAngle, endAngle) => {
    const start = polarToCartesian(x, y, radius, endAngle);
    const end = polarToCartesian(x, y, radius, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';
    return [
      'M', start.x, start.y,
      'A', radius, radius, 0, largeArcFlag, 0, end.x, end.y
    ].join(' ');
  };

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 120" className="w-full max-w-[280px]">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {sections.map((section, index) => (
          <path
            key={section.label}
            d={describeArc(100, 100, 70, section.startAngle, section.endAngle)}
            fill="none"
            stroke={section.color}
            strokeWidth="20"
            strokeLinecap="round"
            className="transition-all duration-300"
            style={{
              opacity: hoveredSection === index ? 1 : 0.8,
              filter: hoveredSection === index ? 'url(#glow)' : 'none'
            }}
            onMouseEnter={() => setHoveredSection(index)}
            onMouseLeave={() => setHoveredSection(null)}
          />
        ))}

        <circle cx="100" cy="100" r="8" fill="#374151" />
        <line x1="100" y1="100" x2="100" y2="45" stroke="#374151" strokeWidth="3" strokeLinecap="round" />
      </svg>

      <div className="grid grid-cols-4 gap-2 mt-4 w-full max-w-sm">
        {sections.map((section) => (
          <div key={section.label} className="text-center">
            <div
              className="h-2 rounded-full mb-1"
              style={{ backgroundColor: section.color }}
            />
            <p className="text-[10px] sm:text-xs font-bold" style={{ color: section.color }}>{section.label}</p>
            <p className="text-[10px] sm:text-xs text-gray-500">{section.range}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

const LandingPage = () => {
  const { isAuthenticated } = useAuth();

  const videos = [
    { id: '1156363021', title: 'VIDEO 1 - REVISAR-IA' },
    { id: '1156363031', title: 'VIDEO 2 - REVISAR-IA' },
    { id: '1156561430', title: 'VIDEO 3 - REVISAR-IA' },
    { id: '1156646666', title: 'VIDEO 4 - REVISAR-IA' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-xl border-b border-gray-200/50 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-14 sm:h-16">
            <div className="flex items-center gap-2 sm:gap-3">
              <img src="/logo-revisar.png" alt="REVISAR.IA" className="h-6 sm:h-8 object-contain" />
              <span className="hidden sm:inline-flex px-2.5 py-1 bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-[10px] sm:text-xs font-bold rounded-full tracking-wide">
                REVISAR.IA
              </span>
            </div>
            <div className="flex items-center gap-3">
              {isAuthenticated ? (
                <Link
                  to="/dashboard"
                  className="px-5 py-2 bg-gradient-to-r from-[#7FEDD8] to-[#5DD5C0] text-gray-900 rounded-lg font-medium text-sm hover:shadow-lg transition-all"
                >
                  Ir al Dashboard
                </Link>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="px-4 py-2 text-gray-600 hover:text-gray-900 text-sm font-medium transition-colors"
                  >
                    Iniciar Sesion
                  </Link>
                  <Link
                    to="/register"
                    className="px-5 py-2 bg-gradient-to-r from-[#7FEDD8] to-[#5DD5C0] text-gray-900 rounded-lg font-medium text-sm hover:shadow-lg transition-all"
                  >
                    Solicitar Acceso
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      <div className="h-14 sm:h-16"></div>

      <section className="py-12 sm:py-16 lg:py-20 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 items-center">
            <div className="text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-100 rounded-full mb-6">
                <ShieldIcon className="w-4 h-4 sm:w-5 sm:h-5 text-indigo-600" />
                <span className="text-xs sm:text-sm font-medium text-indigo-700">Sistema de Auditoría Fiscal Inteligente</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-4 sm:mb-6 leading-[1.1] tracking-tight">
                Audita tus servicios e intangibles
                <span className="block bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mt-1">antes de que lo haga el SAT</span>
              </h1>

              <p className="text-lg sm:text-xl text-gray-500 mb-8 sm:mb-10 leading-relaxed font-light max-w-xl mx-auto lg:mx-0">
                Revisar-IA tipifica tus servicios, aplica checklists fiscales, construye Defense Files y calcula el riesgo fiscal de cada proyecto. Tu equipo decide; la plataforma hace el trabajo pesado.
              </p>

              <div className="flex flex-wrap justify-center lg:justify-start gap-2 sm:gap-3 mb-8">
                <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-2 bg-white border border-blue-100 rounded-xl shadow-sm">
                  <BotIcon className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" />
                  <span className="text-xs sm:text-sm font-semibold text-gray-700 whitespace-nowrap">Agentes IA Especializados</span>
                </div>
                <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-2 bg-white border border-purple-100 rounded-xl shadow-sm">
                  <CheckCircleIcon className="w-4 h-4 sm:w-5 sm:h-5 text-purple-600" />
                  <span className="text-xs sm:text-sm font-semibold text-gray-700 whitespace-nowrap">Checklists Fiscales</span>
                </div>
                <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-2 bg-white border border-emerald-100 rounded-xl shadow-sm">
                  <ShieldIcon className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-600" />
                  <span className="text-xs sm:text-sm font-semibold text-gray-700 whitespace-nowrap">Defense Files</span>
                </div>
              </div>

              <div className="flex flex-wrap justify-center lg:justify-start gap-3 sm:gap-4">
                <Link
                  to="/register"
                  className="px-8 sm:px-10 py-3.5 sm:py-4 text-base sm:text-lg font-semibold bg-gradient-to-r from-[#7FEDD8] to-[#5DD5C0] text-gray-900 rounded-xl shadow-xl hover:shadow-2xl transition-all"
                >
                  Solicitar Acceso
                </Link>
                <a
                  href="#video-demo"
                  className="inline-flex items-center gap-2 px-6 sm:px-8 py-3.5 sm:py-4 text-base sm:text-lg font-semibold text-gray-700 bg-white border-2 border-gray-200 rounded-xl hover:border-indigo-300 hover:text-indigo-600 transition-all duration-300"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Ver Demo
                </a>
              </div>
            </div>

            <div className="flex justify-center lg:justify-end">
              <img
                src="/mascot.webp"
                alt="Revisar.IA Mascota"
                className="w-64 sm:w-80 lg:w-96 h-auto object-contain drop-shadow-2xl"
              />
            </div>
          </div>
        </div>
      </section>

      <section id="video-demo" className="py-12 sm:py-16 px-4 sm:px-6 bg-gradient-to-b from-white to-slate-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-3">
              Explora Revisar.IA
            </h2>
            <p className="text-gray-500">Asistente de facturación y videos demostrativos</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            <div className="bg-gradient-to-br from-emerald-600 to-teal-700 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">Facturar.IA</h3>
                  <p className="text-emerald-100 text-sm">Asistente de Facturación SAT</p>
                </div>
              </div>

              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 mb-4">
                <p className="text-white/90 text-sm leading-relaxed">
                  Habla con nuestro asistente de voz para encontrar la clave SAT correcta para tus facturas.
                  Te ayudará a redactar conceptos deducibles y evitar errores fiscales.
                </p>
              </div>

              <div className="space-y-3 mb-6">
                <div className="flex items-center gap-3 text-white/90">
                  <div className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="text-sm">Encuentra claves SAT por voz o texto</span>
                </div>
                <div className="flex items-center gap-3 text-white/90">
                  <div className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="text-sm">Sugerencias de conceptos deducibles</span>
                </div>
                <div className="flex items-center gap-3 text-white/90">
                  <div className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="text-sm">Análisis de documentos para facturación</span>
                </div>
              </div>

              <EmbeddedFacturarIA />
            </div>

            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">Videos Demostrativos</h3>
                  <p className="text-gray-500 text-sm">Aprende a usar la plataforma</p>
                </div>
              </div>
              <VideoCarousel videos={videos} />
            </div>
          </div>
        </div>
      </section>

      <section className="py-12 sm:py-16 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-full mb-4">
              <BotIcon className="w-4 h-4 sm:w-5 sm:h-5 text-purple-600" />
              <span className="text-xs sm:text-sm font-medium text-purple-700">Sistema Multi-Agente</span>
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-3">
              7 Agentes Principales
            </h2>
            <p className="text-gray-500 max-w-2xl mx-auto">
              Cada agente tiene un rol especializado en el proceso de auditoría fiscal
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-5">
            {mainAgents.map((agent) => {
              const IconComponent = agent.icon;
              return (
                <div
                  key={agent.id}
                  className={`bg-white rounded-2xl p-5 border-2 ${agent.borderColor} hover:shadow-xl transition-all duration-300 group`}
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${agent.color} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
                      <IconComponent className="w-6 h-6 text-white" />
                    </div>
                    <span className={`text-xs font-bold ${agent.textColor} bg-${agent.textColor.replace('text-', '')}/10 px-2 py-1 rounded-full`}>
                      {agent.id}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-gray-900 mb-1">{agent.name}</h3>
                  <p className="text-sm text-gray-500 mb-2">{agent.persona} - {agent.role}</p>
                  <p className="text-xs text-gray-400">{agent.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="py-12 sm:py-16 px-4 sm:px-6 bg-gradient-to-b from-slate-50 to-white">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 rounded-full mb-4">
              <SettingsIcon className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" />
              <span className="text-xs sm:text-sm font-medium text-blue-700">Subagentes Especializados</span>
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-3">
              4 Subagentes
            </h2>
            <p className="text-gray-500">Módulos especializados que complementan a los agentes principales</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5">
            {subAgents.map((agent) => {
              const IconComponent = agent.icon;
              return (
                <div
                  key={agent.id}
                  className="bg-white rounded-2xl p-5 border border-gray-200 hover:shadow-xl transition-all duration-300 group"
                >
                  <div className="flex items-start gap-4">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${agent.color} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform flex-shrink-0`}>
                      <IconComponent className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-gray-900 mb-1">{agent.name}</h3>
                      <p className="text-sm text-gray-600 font-medium mb-1">{agent.role}</p>
                      <p className="text-xs text-gray-400">{agent.description}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="py-12 sm:py-16 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-full mb-4">
              <LockIcon className="w-4 h-4 sm:w-5 sm:h-5 text-amber-600" />
              <span className="text-xs sm:text-sm font-medium text-amber-700">Procedimiento Operativo Estándar</span>
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-3">
              Fases POE F0-F9
            </h2>
            <p className="text-gray-500 max-w-2xl mx-auto">
              10 fases con 3 candados duros que garantizan el cumplimiento obligatorio
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 sm:gap-4">
            {poePhases.map((phase, index) => (
              <div
                key={phase.id}
                className={`relative bg-white rounded-xl p-4 border-2 ${phase.hasLock ? 'border-red-300 bg-red-50/50' : 'border-gray-200'} hover:shadow-lg transition-all group`}
              >
                {phase.hasLock && (
                  <div className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center shadow-lg">
                    <LockIcon className="w-3 h-3 text-white" />
                  </div>
                )}
                <div className={`text-2xl font-bold mb-1 ${phase.hasLock ? 'text-red-600' : 'text-gray-900'}`}>
                  {phase.id}
                </div>
                <p className="text-xs text-gray-600 font-medium">{phase.name}</p>
                {phase.hasLock && phase.lockReason && (
                  <div className="hidden group-hover:block absolute left-0 right-0 -bottom-16 z-10 bg-red-600 text-white text-xs p-2 rounded-lg shadow-lg">
                    {phase.lockReason}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="mt-8 flex justify-center">
            <div className="inline-flex items-center gap-4 px-6 py-3 bg-white rounded-xl border border-gray-200 shadow-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-gray-200 rounded"></div>
                <span className="text-xs text-gray-600">Fase Normal</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-red-200 rounded flex items-center justify-center">
                  <LockIcon className="w-2.5 h-2.5 text-red-600" />
                </div>
                <span className="text-xs text-gray-600">Candado Duro</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-12 sm:py-16 px-4 sm:px-6 bg-gradient-to-b from-white to-slate-50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-full mb-4">
              <CheckCircleIcon className="w-4 h-4 sm:w-5 sm:h-5 text-green-600" />
              <span className="text-xs sm:text-sm font-medium text-green-700">Evaluación Fiscal</span>
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-3">
              4 Pilares de Evaluación
            </h2>
            <p className="text-gray-500">Cada pilar contribuye 25 puntos a la puntuación total de 100</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5">
            {evaluationPillars.map((pillar) => {
              const IconComponent = pillar.icon;
              return (
                <div
                  key={pillar.name}
                  className="bg-white rounded-2xl p-5 border border-gray-200 hover:shadow-xl transition-all duration-300 group"
                >
                  <div className="flex items-start gap-4">
                    <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${pillar.color} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform flex-shrink-0`}>
                      <IconComponent className="w-7 h-7 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <h3 className="text-lg font-bold text-gray-900">{pillar.name}</h3>
                        <span className="text-lg font-bold text-[#7FEDD8]">{pillar.points} pts</span>
                      </div>
                      <p className="text-sm text-indigo-600 font-medium mb-2">{pillar.article}</p>
                      <p className="text-sm text-gray-500">{pillar.description}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="py-12 sm:py-16 px-4 sm:px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-full mb-4">
              <ChartIcon className="w-4 h-4 sm:w-5 sm:h-5 text-red-600" />
              <span className="text-xs sm:text-sm font-medium text-red-700">Medición de Riesgo</span>
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-3">
              Risk Gauge
            </h2>
            <p className="text-gray-500">Indicador visual del nivel de riesgo fiscal de cada proyecto</p>
          </div>

          <div className="bg-white rounded-2xl p-8 border border-gray-200 shadow-lg">
            <RiskGauge />
          </div>
        </div>
      </section>

      <section className="py-12 sm:py-16 px-4 sm:px-6 bg-gradient-to-b from-slate-50 to-slate-100">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
            ¿Listo para Proteger tu Empresa?
          </h2>
          <p className="text-gray-500 mb-8 max-w-2xl mx-auto">
            Solicita acceso a la plataforma y protege tu empresa ante auditorías del SAT con documentación robusta y expedientes de defensa automatizados.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/register"
              className="px-8 py-3.5 bg-gradient-to-r from-[#7FEDD8] to-[#5DD5C0] text-gray-900 rounded-xl font-semibold shadow-xl hover:shadow-2xl transition-all"
            >
              Solicitar Acceso
            </Link>
            <a
              href="mailto:hola@revisar-ia.com"
              className="px-8 py-3.5 border-2 border-gray-300 text-gray-700 rounded-xl font-semibold hover:border-indigo-300 hover:text-indigo-600 transition-all"
            >
              Contactar Ventas
            </a>
          </div>
        </div>
      </section>

      <footer className="bg-[#1A1A1A] text-white py-10 sm:py-12 border-t border-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="sm:col-span-2">
              <div className="flex items-center gap-2 sm:gap-3 mb-4">
                <img src="/logo-revisar-white.png" alt="REVISAR.IA" className="h-6 sm:h-7 object-contain" />
                <span className="px-2 py-0.5 bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-[10px] sm:text-xs font-bold rounded-full">
                  REVISAR.IA
                </span>
              </div>
              <p className="text-gray-400 text-sm mb-4 font-light">
                Cumplimiento fiscal inteligente para tus proyectos intangibles.
              </p>
              <div className="flex flex-wrap gap-2 mb-4">
                <span className="px-2 py-1 bg-gray-800/80 text-gray-400 rounded-lg text-[10px] sm:text-xs">7 Agentes</span>
                <span className="px-2 py-1 bg-gray-800/80 text-gray-400 rounded-lg text-[10px] sm:text-xs">4 Subagentes</span>
                <span className="px-2 py-1 bg-gray-800/80 text-gray-400 rounded-lg text-[10px] sm:text-xs">10 Fases POE</span>
                <span className="px-2 py-1 bg-gray-800/80 text-gray-400 rounded-lg text-[10px] sm:text-xs">3 Candados</span>
              </div>
              <p className="text-xs text-gray-500">
                © 2026 Revisar.IA. Todos los derechos reservados.
              </p>
            </div>

            <div>
              <h4 className="font-semibold mb-4 text-[#7FEDD8] text-sm">Características</h4>
              <ul className="space-y-2 text-gray-400 text-xs sm:text-sm">
                <li><a href="#" className="hover:text-[#7FEDD8] transition-colors">Nuestro Producto</a></li>
                <li><a href="#" className="hover:text-[#7FEDD8] transition-colors">Cómo Funciona</a></li>
                <li><a href="#" className="hover:text-[#7FEDD8] transition-colors">Casos de Uso</a></li>
                <li><a href="#" className="hover:text-[#7FEDD8] transition-colors">Preguntas Frecuentes</a></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold mb-4 text-[#7FEDD8] text-sm">Recursos</h4>
              <ul className="space-y-2 text-gray-400 text-xs sm:text-sm">
                <li><a href="#" className="hover:text-[#7FEDD8] transition-colors">Términos y Condiciones</a></li>
                <li><a href="#" className="hover:text-[#7FEDD8] transition-colors">Tu Privacidad</a></li>
                <li><a href="#" className="hover:text-[#7FEDD8] transition-colors">Compliance SAT</a></li>
                <li><a href="mailto:hola@revisar-ia.com" className="hover:text-[#7FEDD8] transition-colors">Hablemos</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-gray-800/50 mt-8 pt-8 text-center">
            <p className="text-gray-500 text-xs sm:text-sm flex items-center justify-center gap-2">
              Construido con <BotIcon className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-[#7FEDD8]" /> por el equipo de Revisar.IA • Gobernanza Fiscal Inteligente
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
