import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { empresaService } from '../../services/empresaService';

const TIPOLOGIAS_DISPONIBLES = [
  { id: 'consultoria_macro_mercado', nombre: 'Consultoría Macro/Mercado', descripcion: 'Servicios de consultoría estratégica y análisis de mercado' },
  { id: 'intragrupo_management_fee', nombre: 'Intragrupo/Management Fee', descripcion: 'Servicios de gestión entre empresas del mismo grupo' },
  { id: 'software_saas_desarrollo', nombre: 'Software/SaaS/Desarrollo', descripcion: 'Desarrollo de software y servicios en la nube' },
  { id: 'marketing_publicidad', nombre: 'Marketing/Publicidad', descripcion: 'Servicios de marketing y campañas publicitarias' },
  { id: 'legal_fiscal', nombre: 'Legal/Fiscal', descripcion: 'Asesoría legal y fiscal especializada' },
  { id: 'rrhh_capacitacion', nombre: 'RRHH/Capacitación', descripcion: 'Servicios de recursos humanos y formación' }
];

const TabButton = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-all ${
      active 
        ? 'bg-white text-blue-600 border-b-2 border-blue-600' 
        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
    }`}
  >
    {children}
  </button>
);

const InputField = ({ label, value, onChange, type = 'text', placeholder, disabled = false }) => (
  <div className="mb-4">
    <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
    <input
      type={type}
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      disabled={disabled}
      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
    />
  </div>
);

const TextAreaField = ({ label, value, onChange, placeholder, rows = 3 }) => (
  <div className="mb-4">
    <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
    <textarea
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={rows}
      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
    />
  </div>
);

const TabPerfil = ({ empresa, onUpdate, saving }) => {
  const [formData, setFormData] = useState({
    nombre: empresa?.nombre || '',
    rfc: empresa?.rfc || '',
    industria: empresa?.industria || '',
    direccion: empresa?.direccion || '',
    telefono: empresa?.telefono || '',
    email: empresa?.email || ''
  });

  useEffect(() => {
    if (empresa) {
      setFormData({
        nombre: empresa.nombre || '',
        rfc: empresa.rfc || '',
        industria: empresa.industria || '',
        direccion: empresa.direccion || '',
        telefono: empresa.telefono || '',
        email: empresa.email || ''
      });
    }
  }, [empresa]);

  const handleSave = () => {
    onUpdate(formData);
  };

  return (
    <div className="p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Información de la Empresa</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <InputField 
          label="Nombre de la Empresa" 
          value={formData.nombre} 
          onChange={(v) => setFormData({...formData, nombre: v})} 
          placeholder="Ingrese el nombre"
        />
        <InputField 
          label="RFC" 
          value={formData.rfc} 
          onChange={(v) => setFormData({...formData, rfc: v})} 
          placeholder="RFC de la empresa"
        />
        <InputField 
          label="Industria" 
          value={formData.industria} 
          onChange={(v) => setFormData({...formData, industria: v})} 
          placeholder="Sector o industria"
        />
        <InputField 
          label="Teléfono" 
          value={formData.telefono} 
          onChange={(v) => setFormData({...formData, telefono: v})} 
          placeholder="Teléfono de contacto"
        />
        <InputField 
          label="Email" 
          value={formData.email} 
          onChange={(v) => setFormData({...formData, email: v})} 
          placeholder="Email de contacto"
          type="email"
        />
        <InputField 
          label="Dirección" 
          value={formData.direccion} 
          onChange={(v) => setFormData({...formData, direccion: v})} 
          placeholder="Dirección fiscal"
        />
      </div>
      <div className="mt-6 flex justify-end">
        <button 
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {saving ? 'Guardando...' : 'Guardar Cambios'}
        </button>
      </div>
    </div>
  );
};

const TabEstrategia = ({ empresa, onUpdateVisionMision, onUpdatePilares, saving }) => {
  const [vision, setVision] = useState(empresa?.vision || '');
  const [mision, setMision] = useState(empresa?.mision || '');
  const [pilares, setPilares] = useState(empresa?.pilares_estrategicos || []);
  const [nuevoPilar, setNuevoPilar] = useState('');

  useEffect(() => {
    if (empresa) {
      setVision(empresa.vision || '');
      setMision(empresa.mision || '');
      setPilares(empresa.pilares_estrategicos || []);
    }
  }, [empresa]);

  const handleAddPilar = () => {
    if (nuevoPilar.trim()) {
      setPilares([...pilares, nuevoPilar.trim()]);
      setNuevoPilar('');
    }
  };

  const handleRemovePilar = (index) => {
    setPilares(pilares.filter((_, i) => i !== index));
  };

  const handleSaveVisionMision = () => {
    onUpdateVisionMision(vision, mision);
  };

  const handleSavePilares = () => {
    onUpdatePilares(pilares);
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Visión y Misión</h3>
        <TextAreaField 
          label="Visión" 
          value={vision} 
          onChange={setVision} 
          placeholder="Describa la visión de la empresa..."
          rows={4}
        />
        <TextAreaField 
          label="Misión" 
          value={mision} 
          onChange={setMision} 
          placeholder="Describa la misión de la empresa..."
          rows={4}
        />
        <div className="flex justify-end">
          <button 
            onClick={handleSaveVisionMision}
            disabled={saving}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {saving ? 'Guardando...' : 'Guardar Visión y Misión'}
          </button>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Pilares Estratégicos</h3>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={nuevoPilar}
            onChange={(e) => setNuevoPilar(e.target.value)}
            placeholder="Nuevo pilar estratégico..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            onKeyPress={(e) => e.key === 'Enter' && handleAddPilar()}
          />
          <button 
            onClick={handleAddPilar}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            Agregar
          </button>
        </div>
        <div className="space-y-2 mb-4">
          {pilares.map((pilar, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-700">{pilar}</span>
              <button 
                onClick={() => handleRemovePilar(index)}
                className="text-red-500 hover:text-red-700"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
          {pilares.length === 0 && (
            <p className="text-gray-500 text-sm italic">No hay pilares estratégicos definidos</p>
          )}
        </div>
        <div className="flex justify-end">
          <button 
            onClick={handleSavePilares}
            disabled={saving}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {saving ? 'Guardando...' : 'Guardar Pilares'}
          </button>
        </div>
      </div>
    </div>
  );
};

const TabOKRs = ({ empresa, onUpdateOKRs, saving }) => {
  const [okrs, setOkrs] = useState(empresa?.okrs || []);

  useEffect(() => {
    if (empresa?.okrs) {
      setOkrs(empresa.okrs);
    }
  }, [empresa]);

  const handleAddOKR = () => {
    setOkrs([...okrs, { objetivo: '', resultados_clave: [''] }]);
  };

  const handleUpdateObjetivo = (index, value) => {
    const newOkrs = [...okrs];
    newOkrs[index].objetivo = value;
    setOkrs(newOkrs);
  };

  const handleAddResultado = (okrIndex) => {
    const newOkrs = [...okrs];
    newOkrs[okrIndex].resultados_clave.push('');
    setOkrs(newOkrs);
  };

  const handleUpdateResultado = (okrIndex, resultadoIndex, value) => {
    const newOkrs = [...okrs];
    newOkrs[okrIndex].resultados_clave[resultadoIndex] = value;
    setOkrs(newOkrs);
  };

  const handleRemoveResultado = (okrIndex, resultadoIndex) => {
    const newOkrs = [...okrs];
    newOkrs[okrIndex].resultados_clave = newOkrs[okrIndex].resultados_clave.filter((_, i) => i !== resultadoIndex);
    setOkrs(newOkrs);
  };

  const handleRemoveOKR = (index) => {
    setOkrs(okrs.filter((_, i) => i !== index));
  };

  const handleSave = () => {
    const filteredOkrs = okrs
      .filter(okr => okr.objetivo.trim())
      .map(okr => ({
        ...okr,
        resultados_clave: okr.resultados_clave.filter(r => r.trim())
      }));
    onUpdateOKRs(filteredOkrs);
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Objetivos y Resultados Clave (OKRs)</h3>
        <button 
          onClick={handleAddOKR}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
        >
          + Nuevo OKR
        </button>
      </div>

      <div className="space-y-6">
        {okrs.map((okr, okrIndex) => (
          <div key={okrIndex} className="p-4 border border-gray-200 rounded-lg bg-gray-50">
            <div className="flex justify-between items-start mb-3">
              <div className="flex-1 mr-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Objetivo {okrIndex + 1}</label>
                <input
                  type="text"
                  value={okr.objetivo}
                  onChange={(e) => handleUpdateObjetivo(okrIndex, e.target.value)}
                  placeholder="Describa el objetivo..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <button 
                onClick={() => handleRemoveOKR(okrIndex)}
                className="text-red-500 hover:text-red-700 mt-6"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
            <div className="ml-4">
              <label className="block text-sm font-medium text-gray-600 mb-2">Resultados Clave</label>
              {okr.resultados_clave.map((resultado, resultadoIndex) => (
                <div key={resultadoIndex} className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={resultado}
                    onChange={(e) => handleUpdateResultado(okrIndex, resultadoIndex, e.target.value)}
                    placeholder={`Resultado clave ${resultadoIndex + 1}...`}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                  />
                  <button 
                    onClick={() => handleRemoveResultado(okrIndex, resultadoIndex)}
                    className="text-red-400 hover:text-red-600"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}
              <button 
                onClick={() => handleAddResultado(okrIndex)}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                + Agregar resultado clave
              </button>
            </div>
          </div>
        ))}
        {okrs.length === 0 && (
          <p className="text-gray-500 text-center py-8 italic">No hay OKRs definidos. Haga clic en "Nuevo OKR" para comenzar.</p>
        )}
      </div>

      <div className="mt-6 flex justify-end">
        <button 
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {saving ? 'Guardando...' : 'Guardar OKRs'}
        </button>
      </div>
    </div>
  );
};

const TabTipologias = ({ empresa, onUpdateTipologias, saving }) => {
  const [tipologiasActivas, setTipologiasActivas] = useState(empresa?.tipologias_activas || []);

  useEffect(() => {
    if (empresa?.tipologias_activas) {
      setTipologiasActivas(empresa.tipologias_activas);
    }
  }, [empresa]);

  const handleToggle = (tipologiaId) => {
    if (tipologiasActivas.includes(tipologiaId)) {
      setTipologiasActivas(tipologiasActivas.filter(id => id !== tipologiaId));
    } else {
      setTipologiasActivas([...tipologiasActivas, tipologiaId]);
    }
  };

  const handleSave = () => {
    onUpdateTipologias(tipologiasActivas);
  };

  return (
    <div className="p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Tipologías de Servicio Activas</h3>
      <p className="text-gray-600 text-sm mb-6">Seleccione las tipologías de servicio que aplican a su empresa para habilitar los checklists correspondientes.</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {TIPOLOGIAS_DISPONIBLES.map((tipologia) => (
          <div 
            key={tipologia.id}
            onClick={() => handleToggle(tipologia.id)}
            className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
              tipologiasActivas.includes(tipologia.id)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className={`w-5 h-5 rounded flex-shrink-0 border-2 flex items-center justify-center mt-0.5 ${
                tipologiasActivas.includes(tipologia.id)
                  ? 'bg-blue-500 border-blue-500'
                  : 'border-gray-300'
              }`}>
                {tipologiasActivas.includes(tipologia.id) && (
                  <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </div>
              <div>
                <h4 className="font-medium text-gray-800">{tipologia.nombre}</h4>
                <p className="text-sm text-gray-500 mt-1">{tipologia.descripcion}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 flex justify-end">
        <button 
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {saving ? 'Guardando...' : 'Guardar Tipologías'}
        </button>
      </div>
    </div>
  );
};

const TabBaseConocimiento = ({ empresa }) => {
  const [plantillas, setPlantillas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [documentos, setDocumentos] = useState([]);
  const [stats, setStats] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const API_BASE = process.env.REACT_APP_BACKEND_URL
    ? `${process.env.REACT_APP_BACKEND_URL}/api`
    : '/api';

  useEffect(() => {
    loadPlantillas();
    if (empresa?.id) {
      loadKBData();
    }
  }, [empresa?.id]);

  const loadKBData = async () => {
    try {
      // Load KB stats for this empresa
      const statsRes = await fetch(`${API_BASE}/biblioteca/stats?empresa_id=${empresa.id}`);
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      // Load chunks/documents for this empresa
      const chunksRes = await fetch(`${API_BASE}/biblioteca/chunks?empresa_id=${empresa.id}&limit=50`);
      if (chunksRes.ok) {
        const chunksData = await chunksRes.json();
        // Group by document
        const docsMap = {};
        (chunksData.chunks || []).forEach(chunk => {
          if (!docsMap[chunk.documento_id]) {
            docsMap[chunk.documento_id] = {
              id: chunk.documento_id,
              nombre: chunk.documento_nombre,
              chunks: 0,
              agentes: new Set()
            };
          }
          docsMap[chunk.documento_id].chunks++;
          (chunk.agentes_asignados || []).forEach(a => docsMap[chunk.documento_id].agentes.add(a));
        });
        setDocumentos(Object.values(docsMap).map(d => ({...d, agentes: Array.from(d.agentes)})));
      }
    } catch (err) {
      console.error('Error loading KB data:', err);
    }
  };

  const loadPlantillas = async () => {
    try {
      const response = await fetch('/api/templates/');
      const data = await response.json();
      setPlantillas(data);
    } catch (err) {
      console.error('Error loading templates:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0 || !empresa?.id) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append('files', files[i]);
        formData.append('categoria', 'informacion_empresa');
        formData.append('empresa_id', empresa.id);

        const response = await fetch(`${API_BASE}/biblioteca/upload`, {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || 'Error al subir archivo');
        }

        setUploadProgress(Math.round(((i + 1) / files.length) * 100));
      }

      // Reload data
      await loadKBData();
      alert('Documentos subidos exitosamente');
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setUploading(false);
      setUploadProgress(0);
      e.target.value = '';
    }
  };

  const totalDocs = plantillas.reduce((sum, g) => sum + (g.plantillas?.length || 0), 0);
  
  const agentColors = {
    'A1_ESTRATEGIA': 'from-blue-500 to-blue-600',
    'A2_PMO': 'from-green-500 to-green-600',
    'A3_FISCAL': 'from-red-500 to-red-600',
    'A4_LEGAL': 'from-purple-500 to-purple-600',
    'A5_FINANZAS': 'from-yellow-500 to-yellow-600',
    'A6_PROVEEDOR': 'from-orange-500 to-orange-600',
    'A7_DEFENSA': 'from-indigo-500 to-indigo-600',
    'KNOWLEDGE_BASE': 'from-gray-600 to-gray-700'
  };

  return (
    <div className="p-6 space-y-8">
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-6 text-white mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold mb-1">Oráculo de Conocimiento - {empresa?.nombre || 'Empresa'}</h3>
            <p className="text-blue-100 text-sm">
              Documentos de contexto para que los agentes IA entiendan su empresa
            </p>
          </div>
          <div className="flex gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold">{stats?.total_documentos || 0}</div>
              <div className="text-xs text-blue-200">Documentos</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold">{stats?.total_chunks || 0}</div>
              <div className="text-xs text-blue-200">Chunks RAG</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold">{Object.keys(stats?.por_agente || {}).length}</div>
              <div className="text-xs text-blue-200">Agentes</div>
            </div>
          </div>
        </div>
        {stats?.por_agente && Object.keys(stats.por_agente).length > 0 && (
          <div className="mt-4 pt-4 border-t border-white/20">
            <p className="text-xs text-blue-200 mb-2">Distribución por Agente:</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(stats.por_agente).map(([agente, chunks]) => (
                <span key={agente} className="px-2 py-1 bg-white/20 rounded text-xs">
                  {agente}: {chunks} chunks
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-2">Plantillas de Documentos por Agente</h3>
        <p className="text-gray-500 text-sm mb-4">
          Descargue estas plantillas, complételas con información de su empresa, y súbalas para personalizar el contexto de cada agente IA.
        </p>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="w-8 h-8 border-4 border-blue-200 rounded-full animate-spin border-t-blue-600 mx-auto"></div>
          </div>
        ) : (
          <div className="space-y-6">
            {plantillas.map((grupo) => (
              <div key={grupo.agente} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h4 className="font-medium text-gray-700 mb-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-8 h-8 bg-gradient-to-r ${agentColors[grupo.agente] || 'from-gray-500 to-gray-600'} text-white rounded-lg flex items-center justify-center text-xs font-bold shadow-sm`}>
                      {grupo.agente?.substring(0, 2) || '?'}
                    </span>
                    <div>
                      <span className="font-semibold">{grupo.agente_nombre || grupo.agente}</span>
                      <span className="text-xs text-gray-500 ml-2">({grupo.plantillas?.length || 0} docs)</span>
                    </div>
                  </div>
                  {grupo.agente === 'KNOWLEDGE_BASE' && (
                    <span className="px-2 py-1 bg-gray-200 text-gray-600 text-xs rounded-full">Universal</span>
                  )}
                </h4>
                <div className="grid gap-3">
                  {grupo.plantillas.map((plantilla) => (
                    <div 
                      key={plantilla.id}
                      className="bg-white rounded-lg p-3 border border-gray-200 flex items-center justify-between hover:border-blue-300 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <div>
                          <p className="font-medium text-gray-800 text-sm">{plantilla.nombre}</p>
                          <p className="text-xs text-gray-500">{plantilla.descripcion}</p>
                        </div>
                      </div>
                      <a
                        href={`/api/templates/${grupo.agente}/${plantilla.id}/download`}
                        download
                        className="px-3 py-1.5 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium flex items-center gap-1"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        Descargar
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-gray-200 pt-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">Documentos del Acervo</h3>
        <p className="text-gray-500 text-sm mb-4">
          Suba documentos para que los agentes conozcan mejor a su empresa: informes, contratos, políticas, etc.
        </p>

        {uploading && (
          <div className="mb-4 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-blue-700 text-sm">Subiendo documentos...</span>
              <span className="text-blue-700 text-sm font-medium">{uploadProgress}%</span>
            </div>
            <div className="h-2 bg-blue-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-600 transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        <div className="text-center py-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 hover:border-blue-400 transition-colors">
          <svg className="w-10 h-10 text-gray-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p className="text-gray-500 text-sm mb-2">Arrastre archivos aquí o</p>
          <label className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm cursor-pointer inline-block">
            Seleccionar Archivos
            <input
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt,.md"
              className="hidden"
              onChange={handleFileUpload}
              disabled={uploading}
            />
          </label>
          <p className="text-xs text-gray-400 mt-2">PDF, Word, TXT, Markdown. Máx 10MB</p>
        </div>

        {documentos.length > 0 ? (
          <div className="mt-6">
            <h4 className="text-md font-medium text-gray-700 mb-3">Documentos Cargados ({documentos.length})</h4>
            <div className="space-y-3">
              {documentos.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-300 transition-colors">
                  <div className="flex items-center gap-3">
                    <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <div>
                      <p className="font-medium text-gray-800">{doc.nombre}</p>
                      <p className="text-xs text-gray-500">{doc.chunks} chunks • Agentes: {doc.agentes.join(', ')}</p>
                    </div>
                  </div>
                  <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                    Indexado
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-center text-gray-400 text-sm mt-4">
            No hay documentos cargados aún. Suba documentos para que los agentes conozcan a su empresa.
          </p>
        )}
      </div>
    </div>
  );
};

export default function ConfiguracionEmpresa() {
  const { empresaId } = useParams();
  const navigate = useNavigate();
  const [empresa, setEmpresa] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('perfil');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    loadEmpresa();
  }, [empresaId]);

  const loadEmpresa = async () => {
    try {
      setLoading(true);
      const data = await empresaService.obtener(empresaId);
      setEmpresa(data);
      setError(null);
    } catch (err) {
      setError('Error al cargar la información de la empresa');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const showSuccess = (message) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(''), 3000);
  };

  const handleUpdatePerfil = async (data) => {
    try {
      setSaving(true);
      await empresaService.actualizar(empresaId, data);
      await loadEmpresa();
      showSuccess('Perfil actualizado correctamente');
    } catch (err) {
      setError('Error al actualizar el perfil');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateVisionMision = async (vision, mision) => {
    try {
      setSaving(true);
      await empresaService.actualizarVisionMision(empresaId, vision, mision);
      await loadEmpresa();
      showSuccess('Visión y misión actualizadas correctamente');
    } catch (err) {
      setError('Error al actualizar visión y misión');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdatePilares = async (pilares) => {
    try {
      setSaving(true);
      await empresaService.actualizarPilares(empresaId, pilares);
      await loadEmpresa();
      showSuccess('Pilares estratégicos actualizados correctamente');
    } catch (err) {
      setError('Error al actualizar pilares');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateOKRs = async (okrs) => {
    try {
      setSaving(true);
      await empresaService.actualizarOKRs(empresaId, okrs);
      await loadEmpresa();
      showSuccess('OKRs actualizados correctamente');
    } catch (err) {
      setError('Error al actualizar OKRs');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateTipologias = async (tipologias) => {
    try {
      setSaving(true);
      await empresaService.configurarTipologias(empresaId, tipologias);
      await loadEmpresa();
      showSuccess('Tipologías actualizadas correctamente');
    } catch (err) {
      setError('Error al actualizar tipologías');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-200 rounded-full animate-spin border-t-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando configuración...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-5xl mx-auto px-4">
        <div className="flex items-center justify-between mb-6">
          <div>
            <button 
              onClick={() => navigate('/empresas')}
              className="text-gray-500 hover:text-gray-700 mb-2 flex items-center gap-1 text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Volver a empresas
            </button>
            <h1 className="text-2xl font-bold text-gray-800">Configuración de Empresa</h1>
            <p className="text-gray-600">{empresa?.nombre || 'Empresa'}</p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
            {successMessage}
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="border-b border-gray-200 bg-gray-50 px-4 pt-4">
            <div className="flex gap-2 overflow-x-auto">
              <TabButton active={activeTab === 'perfil'} onClick={() => setActiveTab('perfil')}>
                Perfil
              </TabButton>
              <TabButton active={activeTab === 'estrategia'} onClick={() => setActiveTab('estrategia')}>
                Estrategia
              </TabButton>
              <TabButton active={activeTab === 'okrs'} onClick={() => setActiveTab('okrs')}>
                OKRs
              </TabButton>
              <TabButton active={activeTab === 'tipologias'} onClick={() => setActiveTab('tipologias')}>
                Tipologías
              </TabButton>
              <TabButton active={activeTab === 'conocimiento'} onClick={() => setActiveTab('conocimiento')}>
                Base de Conocimiento
              </TabButton>
            </div>
          </div>

          {activeTab === 'perfil' && (
            <TabPerfil empresa={empresa} onUpdate={handleUpdatePerfil} saving={saving} />
          )}
          {activeTab === 'estrategia' && (
            <TabEstrategia 
              empresa={empresa} 
              onUpdateVisionMision={handleUpdateVisionMision} 
              onUpdatePilares={handleUpdatePilares}
              saving={saving} 
            />
          )}
          {activeTab === 'okrs' && (
            <TabOKRs empresa={empresa} onUpdateOKRs={handleUpdateOKRs} saving={saving} />
          )}
          {activeTab === 'tipologias' && (
            <TabTipologias empresa={empresa} onUpdateTipologias={handleUpdateTipologias} saving={saving} />
          )}
          {activeTab === 'conocimiento' && (
            <TabBaseConocimiento empresa={empresa} />
          )}
        </div>
      </div>
    </div>
  );
}
