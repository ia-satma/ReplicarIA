import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  HelpCircle, Search, ChevronDown, ChevronRight,
  Bot, FileCheck, Briefcase, Shield, GitBranch,
  Scale, MessageCircle, ThumbsUp
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || '';

// Iconos por categoría
const CategoriaIcon = ({ categoria, className = "w-5 h-5" }) => {
  const iconMap = {
    uso_ia: <Bot className={className} />,
    materialidad: <FileCheck className={className} />,
    razon_negocios: <Briefcase className={className} />,
    defensa: <Shield className={className} />,
    flujo: <GitBranch className={className} />,
    fiscal: <Scale className={className} />,
    legal: <MessageCircle className={className} />
  };
  return iconMap[categoria] || <HelpCircle className={className} />;
};

// Colores por categoría
const getCategoriaColor = (categoria) => {
  const colores = {
    uso_ia: 'bg-teal-500',
    materialidad: 'bg-purple-500',
    razon_negocios: 'bg-blue-500',
    defensa: 'bg-red-500',
    flujo: 'bg-orange-500',
    fiscal: 'bg-indigo-500',
    legal: 'bg-green-500'
  };
  return colores[categoria] || 'bg-gray-500';
};

// Componente de pregunta expandible
const FAQItem = ({ faq, isExpanded, onToggle }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full px-6 py-4 text-left hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1">
            <div className={`p-2 rounded-lg ${getCategoriaColor(faq.categoria)} bg-opacity-10`}>
              <CategoriaIcon
                categoria={faq.categoria}
                className={`w-5 h-5 ${getCategoriaColor(faq.categoria).replace('bg-', 'text-')}`}
              />
            </div>
            <div className="flex-1">
              <h3 className="font-medium text-gray-900 text-left">
                {faq.pregunta}
              </h3>
              {!isExpanded && faq.respuesta_corta && (
                <p className="text-sm text-gray-500 mt-1 line-clamp-1">
                  {faq.respuesta_corta}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {faq.es_destacada && (
              <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                Destacada
              </span>
            )}
            {isExpanded ? (
              <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
            )}
          </div>
        </div>
      </button>

      {isExpanded && (
        <div className="px-6 pb-6 pt-0">
          <div className="ml-10 prose prose-sm max-w-none">
            <div className="bg-gray-50 rounded-lg p-4 text-gray-700 whitespace-pre-wrap">
              {faq.respuesta}
            </div>

            {/* Votos útil */}
            <div className="mt-4 flex items-center gap-4 text-sm">
              <span className="text-gray-500">¿Te fue útil?</span>
              <button className="flex items-center gap-1 text-gray-500 hover:text-green-600 transition-colors">
                <ThumbsUp className="w-4 h-4" />
                <span>Sí</span>
              </button>
            </div>

            {/* Visitas */}
            {faq.visitas && (
              <div className="mt-2 text-xs text-gray-400">
                Vista {faq.visitas.toLocaleString()} veces
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Componente de categoría sidebar
const CategoriaSidebar = ({ categorias, categoriaActiva, onSelect }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <h3 className="font-medium text-gray-900 mb-4">Categorías</h3>
      <div className="space-y-1">
        <button
          onClick={() => onSelect('')}
          className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
            categoriaActiva === '' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <HelpCircle className="w-5 h-5" />
          <span>Todas las preguntas</span>
        </button>
        {categorias.map((cat) => (
          <button
            key={cat.codigo}
            onClick={() => onSelect(cat.codigo)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
              categoriaActiva === cat.codigo ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <CategoriaIcon categoria={cat.codigo} />
            <span className="flex-1">{cat.nombre}</span>
            {cat.count && (
              <span className="text-xs bg-gray-100 px-2 py-0.5 rounded-full">
                {cat.count}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};

// Componente principal
const FAQPage = () => {
  const { token } = useAuth();
  const [faqs, setFaqs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  // Filtros
  const [categoriaActiva, setCategoriaActiva] = useState('');
  const [busqueda, setBusqueda] = useState('');

  // Categorías
  const [categorias, setCategorias] = useState([]);

  // Cargar datos
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Cargar categorías
        const catRes = await fetch(`${API_BASE}/api/faqs/categorias`);
        if (catRes.ok) {
          const catData = await catRes.json();
          setCategorias(catData);
        }

        // Cargar FAQs
        await fetchFAQs();
      } catch (err) {
        console.error('Error cargando datos:', err);
        setError('Error al cargar las preguntas frecuentes');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const fetchFAQs = async () => {
    try {
      const params = new URLSearchParams();
      if (categoriaActiva) params.append('categoria', categoriaActiva);
      if (busqueda) params.append('busqueda', busqueda);

      const res = await fetch(`${API_BASE}/api/faqs?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setFaqs(data.items || []);
      }
    } catch (err) {
      console.error('Error cargando FAQs:', err);
    }
  };

  // Recargar cuando cambien filtros
  useEffect(() => {
    fetchFAQs();
  }, [categoriaActiva, busqueda]);

  const toggleExpanded = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  // Agrupar FAQs por categoría (para vista sin filtro)
  const faqsAgrupadas = faqs.reduce((acc, faq) => {
    const cat = faq.categoria;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(faq);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-teal-600 to-cyan-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/10 rounded-xl">
              <HelpCircle className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Preguntas Frecuentes</h1>
              <p className="text-teal-100 mt-1">
                Resuelve tus dudas sobre REVISAR.IA
              </p>
            </div>
          </div>

          {/* Búsqueda */}
          <div className="mt-6">
            <div className="relative max-w-xl">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Buscar en preguntas y respuestas..."
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-white rounded-xl text-gray-900 placeholder-gray-400 shadow-lg focus:ring-2 focus:ring-white/50 focus:outline-none"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Contenido */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar de categorías */}
          <div className="lg:col-span-1">
            <CategoriaSidebar
              categorias={categorias}
              categoriaActiva={categoriaActiva}
              onSelect={setCategoriaActiva}
            />
          </div>

          {/* Lista de FAQs */}
          <div className="lg:col-span-3">
            {error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                {error}
              </div>
            ) : faqs.length === 0 ? (
              <div className="bg-white rounded-lg shadow-sm p-8 text-center">
                <HelpCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No se encontraron preguntas con los filtros seleccionados.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Resumen */}
                <div className="text-sm text-gray-500 mb-4">
                  {categoriaActiva ? (
                    <>Mostrando {faqs.length} pregunta(s) en esta categoría</>
                  ) : (
                    <>Mostrando todas las preguntas ({faqs.length})</>
                  )}
                </div>

                {faqs.map((faq) => (
                  <FAQItem
                    key={faq.id}
                    faq={faq}
                    isExpanded={expandedId === faq.id}
                    onToggle={() => toggleExpanded(faq.id)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-gray-100 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            ¿No encontraste lo que buscabas?
          </h2>
          <p className="text-gray-600 mb-6">
            Contáctanos y te ayudaremos con tu consulta específica.
          </p>
          <a
            href="mailto:soporte@revisar-ia.com"
            className="inline-flex items-center gap-2 px-6 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors"
          >
            <MessageCircle className="w-5 h-5" />
            Contactar soporte
          </a>
        </div>
      </div>
    </div>
  );
};

export default FAQPage;
