import React, { useState, useEffect } from 'react';

const PLACEHOLDER_LABELS = {
  EMPRESA_NOMBRE: 'Nombre de la Empresa',
  EMPRESA_RFC: 'RFC de la Empresa',
  FECHA_ACTUAL: 'Fecha',
  PROYECTO_NOMBRE: 'Nombre del Proyecto',
  MONTO_CREDITO: 'Monto',
  PROVEEDOR_NOMBRE: 'Nombre del Proveedor',
  PROVEEDOR_RFC: 'RFC del Proveedor',
  DESCRIPCION_SERVICIO: 'Descripción del Servicio',
  FOLIO_PROYECTO: 'Folio del Proyecto',
  RESPONSABLE_PROYECTO: 'Responsable del Proyecto',
  PERIODO_FISCAL: 'Período Fiscal',
  FECHA_INICIO: 'Fecha de Inicio',
  FECHA_FIN: 'Fecha de Fin',
  BENEFICIO_CUANTIFICADO: 'Beneficio Cuantificado',
  OBSERVACIONES_RAZON_NEGOCIOS: 'Observaciones Razón de Negocios',
};

const getPlaceholderLabel = (placeholder) => {
  return PLACEHOLDER_LABELS[placeholder] || placeholder.replace(/_/g, ' ');
};

const getPlaceholderType = (placeholder) => {
  if (placeholder.includes('FECHA')) return 'date';
  if (placeholder.includes('MONTO') || placeholder.includes('BENEFICIO') || placeholder.includes('AHORRO')) return 'number';
  if (placeholder.includes('RFC')) return 'text';
  if (placeholder.includes('DESCRIPCION') || placeholder.includes('OBSERVACIONES')) return 'textarea';
  return 'text';
};

const TemplateCustomizeModal = ({ 
  isOpen, 
  onClose, 
  template, 
  agentId, 
  agentName,
  onGenerate,
  onDownloadOriginal 
}) => {
  const [formData, setFormData] = useState({});
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (template?.placeholders) {
      const initialData = {};
      template.placeholders.forEach(p => {
        if (p.includes('FECHA_ACTUAL')) {
          initialData[p] = new Date().toLocaleDateString('es-MX');
        } else {
          initialData[p] = '';
        }
      });
      setFormData(initialData);
    }
  }, [template]);

  const handleChange = (placeholder, value) => {
    setFormData(prev => ({
      ...prev,
      [placeholder]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsGenerating(true);
    setError(null);
    
    try {
      await onGenerate(agentId, template.template_id, formData);
    } catch (err) {
      setError(err.message || 'Error al generar documento');
    } finally {
      setIsGenerating(false);
    }
  };

  const filledCount = Object.values(formData).filter(v => v && v.trim()).length;
  const totalCount = template?.placeholders?.length || 0;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Personalizar Template</h2>
            <p className="text-blue-100 text-sm">{agentName} - {template?.title || template?.template_id}</p>
          </div>
          <button 
            onClick={onClose}
            className="text-white/80 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="px-6 py-3 bg-slate-50 border-b flex items-center justify-between">
          <span className="text-sm text-slate-600">
            Campos completados: <span className="font-semibold text-blue-600">{filledCount}</span> de {totalCount}
          </span>
          <div className="w-32 bg-slate-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: totalCount > 0 ? `${(filledCount / totalCount) * 100}%` : '0%' }}
            />
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {template?.placeholders?.map((placeholder) => {
              const type = getPlaceholderType(placeholder);
              const label = getPlaceholderLabel(placeholder);
              
              if (type === 'textarea') {
                return (
                  <div key={placeholder} className="md:col-span-2">
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      {label}
                    </label>
                    <textarea
                      value={formData[placeholder] || ''}
                      onChange={(e) => handleChange(placeholder, e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm resize-none"
                      placeholder={`Ingrese ${label.toLowerCase()}`}
                    />
                  </div>
                );
              }
              
              return (
                <div key={placeholder}>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    {label}
                  </label>
                  <input
                    type={type === 'date' ? 'text' : type}
                    value={formData[placeholder] || ''}
                    onChange={(e) => handleChange(placeholder, e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    placeholder={type === 'date' ? 'DD/MM/AAAA' : `Ingrese ${label.toLowerCase()}`}
                  />
                </div>
              );
            })}
          </div>
        </form>

        <div className="px-6 py-4 bg-slate-50 border-t flex gap-3 justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-200 rounded-lg transition-colors"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => onDownloadOriginal(agentId, template.template_id, template.filename)}
            className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-200 hover:bg-slate-300 rounded-lg transition-colors flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Original
          </button>
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={isGenerating || filledCount === 0}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed rounded-lg transition-colors flex items-center gap-1"
          >
            {isGenerating ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generando...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Generar Personalizado
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default TemplateCustomizeModal;
