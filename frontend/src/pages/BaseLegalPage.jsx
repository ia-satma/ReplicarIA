import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Scale, BookOpen, FileText, Gavel, Shield, Search,
  ChevronDown, ChevronRight, ExternalLink, AlertCircle, CheckCircle2
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || '';

// Componente de icono por tipo
const TipoIcon = ({ tipo }) => {
  const iconMap = {
    articulo_cff: <Scale className="w-5 h-5 text-blue-500" />,
    articulo_lisr: <Scale className="w-5 h-5 text-indigo-500" />,
    jurisprudencia: <Gavel className="w-5 h-5 text-purple-500" />,
    norma_oficial: <FileText className="w-5 h-5 text-green-500" />,
    criterio_sat: <AlertCircle className="w-5 h-5 text-orange-500" />,
    criterio_interno: <Shield className="w-5 h-5 text-teal-500" />
  };
  return iconMap[tipo] || <BookOpen className="w-5 h-5 text-gray-500" />;
};

// Badge de pilar
const PilarBadge = ({ pilar }) => {
  const colores = {
    razon_negocios: 'bg-blue-100 text-blue-800',
    bee: 'bg-green-100 text-green-800',
    materialidad: 'bg-purple-100 text-purple-800',
    trazabilidad: 'bg-orange-100 text-orange-800',
    uso_ia: 'bg-teal-100 text-teal-800'
  };
  const nombres = {
    razon_negocios: 'Razón de Negocios',
    bee: 'BEE',
    materialidad: 'Materialidad',
    trazabilidad: 'Trazabilidad',
    uso_ia: 'Uso de IA'
  };
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colores[pilar] || 'bg-gray-100 text-gray-800'}`}>
      {nombres[pilar] || pilar}
    </span>
  );
};

// Card de artículo expandible
const ArticuloCard = ({ articulo, isExpanded, onToggle }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <TipoIcon tipo={articulo.tipo} />
            <div>
              <div className="flex items-center gap-2 mb-1">
                {articulo.numero_referencia && (
                  <span className="text-sm font-mono text-gray-500">
                    {articulo.numero_referencia}
                  </span>
                )}
                {articulo.registro_digital && (
                  <span className="text-xs text-gray-400">
                    Reg. {articulo.registro_digital}
                  </span>
                )}
              </div>
              <h3 className="font-medium text-gray-900">{articulo.titulo}</h3>
              {articulo.resumen_ejecutivo && (
                <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                  {articulo.resumen_ejecutivo}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {articulo.es_vigente && (
              <CheckCircle2 className="w-4 h-4 text-green-500" />
            )}
            {isExpanded ? (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>

        {/* Pills de pilares */}
        {articulo.aplica_a_pilares && articulo.aplica_a_pilares.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {articulo.aplica_a_pilares.map((pilar) => (
              <PilarBadge key={pilar} pilar={pilar} />
            ))}
          </div>
        )}
      </div>

      {/* Contenido expandido */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-0 border-t border-gray-100">
          <div className="mt-4 prose prose-sm max-w-none">
            <div className="bg-gray-50 rounded-lg p-4 text-gray-700 whitespace-pre-wrap text-sm">
              {articulo.contenido_completo}
            </div>
          </div>

          {/* Fases aplicables */}
          {articulo.aplica_a_fases && articulo.aplica_a_fases.length > 0 && (
            <div className="mt-4">
              <span className="text-xs font-medium text-gray-500 uppercase">
                Aplica en fases:
              </span>
              <div className="flex gap-1 mt-1">
                {articulo.aplica_a_fases.map((fase) => (
                  <span
                    key={fase}
                    className="px-2 py-0.5 bg-gray-200 text-gray-700 rounded text-xs font-mono"
                  >
                    {fase}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Fuente */}
          {articulo.fuente && (
            <div className="mt-4 flex items-center gap-2 text-sm text-blue-600">
              <ExternalLink className="w-4 h-4" />
              <a href={articulo.fuente} target="_blank" rel="noopener noreferrer">
                Ver fuente original
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Componente principal
const BaseLegalPage = () => {
  const { token } = useAuth();
  const [articulos, setArticulos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  // Filtros
  const [filtroTipo, setFiltroTipo] = useState('');
  const [filtroCategoria, setFiltroCategoria] = useState('');
  const [filtroPilar, setFiltroPilar] = useState('');
  const [busqueda, setBusqueda] = useState('');

  // Opciones de filtros
  const [tipos, setTipos] = useState([]);
  const [categorias, setCategorias] = useState([]);

  // Cargar datos
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Cargar tipos y categorías
        const [tiposRes, categoriasRes] = await Promise.all([
          fetch(`${API_BASE}/api/legal-base/tipos`),
          fetch(`${API_BASE}/api/legal-base/categorias`)
        ]);

        if (tiposRes.ok) {
          const tiposData = await tiposRes.json();
          setTipos(tiposData);
        }
        if (categoriasRes.ok) {
          const categoriasData = await categoriasRes.json();
          setCategorias(categoriasData);
        }

        // Cargar artículos
        await fetchArticulos();
      } catch (err) {
        console.error('Error cargando datos:', err);
        setError('Error al cargar la base jurídica');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const fetchArticulos = async () => {
    try {
      const params = new URLSearchParams();
      if (filtroTipo) params.append('tipo', filtroTipo);
      if (filtroCategoria) params.append('categoria', filtroCategoria);
      if (filtroPilar) params.append('pilar', filtroPilar);
      if (busqueda) params.append('busqueda', busqueda);

      const res = await fetch(`${API_BASE}/api/legal-base?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setArticulos(data.items || []);
      }
    } catch (err) {
      console.error('Error cargando artículos:', err);
    }
  };

  // Recargar cuando cambien filtros
  useEffect(() => {
    fetchArticulos();
  }, [filtroTipo, filtroCategoria, filtroPilar, busqueda]);

  const toggleExpanded = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

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
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/10 rounded-xl">
              <Scale className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Base Jurídica</h1>
              <p className="text-blue-100 mt-1">
                Fundamentación legal de REVISAR.IA
              </p>
            </div>
          </div>

          {/* Descripción */}
          <div className="mt-6 bg-white/10 rounded-xl p-4">
            <p className="text-sm text-blue-100">
              Esta sección contiene la fundamentación normativa que sustenta el funcionamiento
              de REVISAR.IA, incluyendo artículos del CFF, LISR, normas oficiales como la NOM-151,
              y jurisprudencia relevante como la Tesis II.2o.C. J/1 K (12a.) que avala el uso
              de inteligencia artificial como herramienta auxiliar.
            </p>
          </div>
        </div>
      </div>

      {/* Filtros */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6">
        <div className="bg-white rounded-xl shadow-sm p-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {/* Búsqueda */}
            <div className="md:col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Buscar en título o contenido..."
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Filtro por tipo */}
            <select
              value={filtroTipo}
              onChange={(e) => setFiltroTipo(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos los tipos</option>
              {tipos.map((tipo) => (
                <option key={tipo.codigo} value={tipo.codigo}>
                  {tipo.nombre}
                </option>
              ))}
            </select>

            {/* Filtro por categoría */}
            <select
              value={filtroCategoria}
              onChange={(e) => setFiltroCategoria(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todas las categorías</option>
              {categorias.map((cat) => (
                <option key={cat.codigo} value={cat.codigo}>
                  {cat.nombre}
                </option>
              ))}
            </select>

            {/* Filtro por pilar */}
            <select
              value={filtroPilar}
              onChange={(e) => setFiltroPilar(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos los pilares</option>
              <option value="razon_negocios">Razón de Negocios</option>
              <option value="bee">Beneficio Económico (BEE)</option>
              <option value="materialidad">Materialidad</option>
              <option value="trazabilidad">Trazabilidad</option>
              <option value="uso_ia">Uso de IA</option>
            </select>
          </div>
        </div>
      </div>

      {/* Lista de artículos */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        ) : articulos.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-8 text-center">
            <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No se encontraron artículos con los filtros seleccionados.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Resumen */}
            <div className="text-sm text-gray-500 mb-4">
              Mostrando {articulos.length} artículo(s)
            </div>

            {articulos.map((articulo) => (
              <ArticuloCard
                key={articulo.id}
                articulo={articulo}
                isExpanded={expandedId === articulo.id}
                onToggle={() => toggleExpanded(articulo.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Sección destacada: Jurisprudencia IA */}
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <Gavel className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  Jurisprudencia sobre Uso de IA
                </h2>
                <p className="text-sm text-purple-600 font-mono mt-1">
                  Tesis: II.2o.C. J/1 K (12a.) | Registro: 2031639
                </p>
                <div className="mt-4 prose prose-sm text-gray-600">
                  <p>
                    La Suprema Corte de Justicia de la Nación ha reconocido expresamente que
                    las herramientas de <strong>inteligencia artificial pueden emplearse válidamente</strong> en
                    procesos jurisdiccionales para tareas auxiliares.
                  </p>
                  <p className="mt-2">
                    La jurisprudencia destaca que la IA:
                  </p>
                  <ul className="list-disc pl-5 mt-2 space-y-1">
                    <li>Reduce errores humanos en cálculos complejos</li>
                    <li>Aporta transparencia y trazabilidad</li>
                    <li>Genera consistencia y estandarización de criterios</li>
                    <li>Mejora la eficiencia, liberando tiempo para análisis sustantivo</li>
                  </ul>
                  <p className="mt-3 bg-purple-50 p-3 rounded-lg border-l-4 border-purple-500">
                    <strong>REVISAR.IA</strong> aplica esta misma lógica: la IA se usa como herramienta auxiliar
                    para calcular risk_scores, aplicar checklists y organizar Defense Files.
                    Las decisiones con efectos jurídicos siempre las toman personas.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BaseLegalPage;
