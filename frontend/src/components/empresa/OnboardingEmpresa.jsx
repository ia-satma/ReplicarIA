import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { empresaService } from '../../services/empresaService';

const TIPOLOGIAS_DISPONIBLES = [
  { id: 'consultoria_macro_mercado', nombre: 'Consultoría Macro/Mercado', descripcion: 'Servicios de consultoría estratégica y análisis de mercado' },
  { id: 'intragrupo_management_fee', nombre: 'Intragrupo/Management Fee', descripcion: 'Servicios de gestión entre empresas del mismo grupo' },
  { id: 'software_saas_desarrollo', nombre: 'Software/SaaS/Desarrollo', descripcion: 'Desarrollo de software y servicios en la nube' },
  { id: 'marketing_publicidad', nombre: 'Marketing/Publicidad', descripcion: 'Servicios de marketing y campañas publicitarias' },
  { id: 'legal_fiscal', nombre: 'Legal/Fiscal', descripcion: 'Asesoría legal y fiscal especializada' },
  { id: 'rrhh_capacitacion', nombre: 'RRHH/Capacitación', descripcion: 'Servicios de recursos humanos y formación' }
];

const INDUSTRIAS = [
  { value: 'tecnologia', label: 'Tecnología' },
  { value: 'servicios_profesionales', label: 'Servicios Profesionales' },
  { value: 'manufactura', label: 'Manufactura' },
  { value: 'comercio', label: 'Comercio / Retail' },
  { value: 'construccion', label: 'Construcción' },
  { value: 'salud', label: 'Salud' },
  { value: 'educacion', label: 'Educación' },
  { value: 'hoteleria_restaurantes', label: 'Hotelería y Restaurantes' },
  { value: 'transporte_logistica', label: 'Transporte y Logística' },
  { value: 'inmobiliario', label: 'Inmobiliario' },
  { value: 'otro', label: 'Otro' }
];

const StepIndicator = ({ currentStep, totalSteps }) => {
  return (
    <div className="flex items-center justify-center mb-8">
      {[...Array(totalSteps)].map((_, index) => (
        <React.Fragment key={index}>
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center font-medium transition-all ${index + 1 < currentStep
              ? 'bg-green-500 text-white'
              : index + 1 === currentStep
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-500'
              }`}
          >
            {index + 1 < currentStep ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              index + 1
            )}
          </div>
          {index < totalSteps - 1 && (
            <div className={`w-16 h-1 mx-2 ${index + 1 < currentStep ? 'bg-green-500' : 'bg-gray-200'}`} />
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

const StepInfoBasica = ({ data, onChange }) => {
  const [autofillLoading, setAutofillLoading] = useState(false);
  const [autofillMessage, setAutofillMessage] = useState(null);

  const handleAutofill = async () => {
    if (!data.sitio_web) return;

    try {
      setAutofillLoading(true);
      setAutofillMessage(null);

      const result = await empresaService.autofill({
        nombre_comercial: data.nombre_comercial || 'Empresa',
        sitio_web: data.sitio_web
      });

      if (result.success && result.data) {
        onChange({
          ...data,
          ...result.data, // Merge all found fields (vision, mision, rfc, etc)
          nombre_comercial: result.data.nombre_comercial || data.nombre_comercial
        });
        setAutofillMessage({ type: 'success', text: '¡Datos completados con IA!' });
      }
    } catch (err) {
      console.error(err);
      setAutofillMessage({
        type: 'error',
        text: 'No se pudo completar automáticamente. Intente llenar los campos manualmente.'
      });
    } finally {
      setAutofillLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="border-b border-gray-200 dark:border-gray-700 pb-4 mb-4">
        <h2 className="text-xl font-bold text-slate-800 dark:text-white">Información Básica</h2>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Complete la información básica de su empresa para comenzar.</p>
      </div>

      {autofillMessage && (
        <div className={`p-4 rounded-xl text-sm flex items-center gap-2 ${autofillMessage.type === 'success'
            ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
            : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
          }`}>
          <span>{autofillMessage.type === 'success' ? '✨' : '⚠️'}</span>
          {autofillMessage.text}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Nombre Comercial *</label>
          <input
            type="text"
            value={data.nombre_comercial || ''}
            onChange={(e) => onChange({ ...data, nombre_comercial: e.target.value })}
            placeholder="Ej: Mi Empresa"
            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-2">
            Sitio Web (Opcional)
            <span className="text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-300 px-2 py-0.5 rounded-full font-medium">Recomendado</span>
          </label>
          <div className="flex gap-2">
            <input
              type="url"
              value={data.sitio_web || ''}
              onChange={(e) => onChange({ ...data, sitio_web: e.target.value })}
              placeholder="https://su-empresa.com"
              className="flex-1 px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all outline-none"
            />
            <button
              type="button"
              onClick={handleAutofill}
              disabled={!data.sitio_web || autofillLoading}
              className="px-5 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl shadow-lg shadow-purple-500/20 disabled:opacity-50 transition-all flex items-center gap-2 whitespace-nowrap font-medium hover:scale-105"
            >
              {autofillLoading ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Investigando...
                </>
              ) : (
                <>
                  <span className="text-lg">✨</span> Auto-completar
                </>
              )}
            </button>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 flex items-center gap-1.5 ml-1">
            <svg className="w-3.5 h-3.5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Nuestra IA analizará su sitio para completar su perfil empresarial automáticamente.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Razón Social *</label>
          <input
            type="text"
            value={data.razon_social || ''}
            onChange={(e) => onChange({ ...data, razon_social: e.target.value })}
            placeholder="Ej: Mi Empresa S.A. de C.V."
            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">RFC *</label>
          <input
            type="text"
            value={data.rfc || ''}
            onChange={(e) => onChange({ ...data, rfc: e.target.value.toUpperCase() })}
            placeholder="Ej: GFO850101XXX"
            maxLength={13}
            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none uppercase font-mono"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Industria *</label>
          <div className="relative">
            <select
              value={data.industria || ''}
              onChange={(e) => onChange({ ...data, industria: e.target.value })}
              className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none appearance-none"
            >
              <option value="">Seleccione una industria</option>
              {INDUSTRIAS.map((industria) => (
                <option key={industria.value} value={industria.value}>{industria.label}</option>
              ))}
            </select>
            <div className="absolute inset-y-0 right-0 flex items-center px-4 pointer-events-none text-slate-500">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Email de Contacto</label>
          <input
            type="email"
            value={data.email || ''}
            onChange={(e) => onChange({ ...data, email: e.target.value })}
            placeholder="contacto@empresa.com"
            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
          />
        </div>
      </div>
    </div>
  );
};

const StepEstrategia = ({ data, onChange }) => {
  const [nuevoPilar, setNuevoPilar] = useState('');

  const handleAddPilar = () => {
    if (nuevoPilar.trim()) {
      const pilares = data.pilares_estrategicos || [];
      onChange({ ...data, pilares_estrategicos: [...pilares, nuevoPilar.trim()] });
      setNuevoPilar('');
    }
  };

  const handleRemovePilar = (index) => {
    const pilares = data.pilares_estrategicos || [];
    onChange({ ...data, pilares_estrategicos: pilares.filter((_, i) => i !== index) });
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Estrategia Empresarial</h2>
      <p className="text-gray-600 text-sm mb-6">Define la visión, misión y pilares estratégicos de tu empresa.</p>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Visión</label>
        <textarea
          value={data.vision || ''}
          onChange={(e) => onChange({ ...data, vision: e.target.value })}
          placeholder="¿Hacia dónde quiere llegar su empresa en el futuro?"
          rows={4}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Misión</label>
        <textarea
          value={data.mision || ''}
          onChange={(e) => onChange({ ...data, mision: e.target.value })}
          placeholder="¿Cuál es el propósito fundamental de su empresa?"
          rows={4}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Pilares Estratégicos</label>
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={nuevoPilar}
            onChange={(e) => setNuevoPilar(e.target.value)}
            placeholder="Agregar pilar estratégico..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddPilar())}
          />
          <button
            type="button"
            onClick={handleAddPilar}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            Agregar
          </button>
        </div>
        <div className="space-y-2">
          {(data.pilares_estrategicos || []).map((pilar, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
              <span className="text-gray-700">{pilar}</span>
              <button
                type="button"
                onClick={() => handleRemovePilar(index)}
                className="text-red-500 hover:text-red-700"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const StepTipologias = ({ data, onChange }) => {
  const tipologiasActivas = data.tipologias_activas || [];

  const handleToggle = (tipologiaId) => {
    if (tipologiasActivas.includes(tipologiaId)) {
      onChange({ ...data, tipologias_activas: tipologiasActivas.filter(id => id !== tipologiaId) });
    } else {
      onChange({ ...data, tipologias_activas: [...tipologiasActivas, tipologiaId] });
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Tipologías de Servicio</h2>
      <p className="text-gray-600 text-sm mb-6">Seleccione los tipos de servicio que maneja su empresa. Esto habilitará los checklists de cumplimiento correspondientes.</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {TIPOLOGIAS_DISPONIBLES.map((tipologia) => (
          <div
            key={tipologia.id}
            onClick={() => handleToggle(tipologia.id)}
            className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${tipologiasActivas.includes(tipologia.id)
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-blue-300'
              }`}
          >
            <div className="flex items-start gap-3">
              <div className={`w-5 h-5 rounded flex-shrink-0 border-2 flex items-center justify-center mt-0.5 ${tipologiasActivas.includes(tipologia.id)
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
    </div>
  );
};

const StepConfirmacion = ({ data }) => (
  <div className="space-y-6">
    <h2 className="text-xl font-semibold text-gray-800 mb-4">Confirmación</h2>
    <p className="text-gray-600 text-sm mb-6">Revise la información antes de crear la empresa.</p>

    <div className="bg-gray-50 rounded-lg p-6 space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-500">Nombre Comercial</p>
          <p className="font-medium text-gray-800">{data.nombre_comercial || '-'}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Razón Social</p>
          <p className="font-medium text-gray-800">{data.razon_social || '-'}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">RFC</p>
          <p className="font-medium text-gray-800">{data.rfc || '-'}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Industria</p>
          <p className="font-medium text-gray-800">{INDUSTRIAS.find(i => i.value === data.industria)?.label || data.industria || '-'}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Email</p>
          <p className="font-medium text-gray-800">{data.email || '-'}</p>
        </div>
      </div>

      {data.vision && (
        <div className="pt-4 border-t">
          <p className="text-sm text-gray-500">Visión</p>
          <p className="text-gray-700">{data.vision}</p>
        </div>
      )}

      {data.mision && (
        <div className="pt-4 border-t">
          <p className="text-sm text-gray-500">Misión</p>
          <p className="text-gray-700">{data.mision}</p>
        </div>
      )}

      {data.pilares_estrategicos?.length > 0 && (
        <div className="pt-4 border-t">
          <p className="text-sm text-gray-500 mb-2">Pilares Estratégicos</p>
          <div className="flex flex-wrap gap-2">
            {data.pilares_estrategicos.map((pilar, index) => (
              <span key={index} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                {pilar}
              </span>
            ))}
          </div>
        </div>
      )}

      {data.tipologias_activas?.length > 0 && (
        <div className="pt-4 border-t">
          <p className="text-sm text-gray-500 mb-2">Tipologías Activas</p>
          <div className="flex flex-wrap gap-2">
            {data.tipologias_activas.map((tipId) => {
              const tip = TIPOLOGIAS_DISPONIBLES.find(t => t.id === tipId);
              return tip ? (
                <span key={tipId} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                  {tip.nombre}
                </span>
              ) : null;
            })}
          </div>
        </div>
      )}
    </div>
  </div>
);

export default function OnboardingEmpresa() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState({
    nombre_comercial: '',
    razon_social: '',
    rfc: '',
    industria: '',
    email: '',
    sitio_web: '',
    vision: '',
    mision: '',
    pilares_estrategicos: [],
    tipologias_activas: []
  });

  const totalSteps = 4;

  const validateStep = () => {
    switch (step) {
      case 1:
        if (!data.nombre_comercial?.trim()) {
          setError('El nombre comercial de la empresa es requerido');
          return false;
        }
        if (!data.razon_social?.trim()) {
          setError('La razón social es requerida');
          return false;
        }
        if (!data.rfc?.trim()) {
          setError('El RFC es requerido');
          return false;
        }
        if (!data.industria) {
          setError('Seleccione una industria');
          return false;
        }
        break;
      default:
        break;
    }
    setError(null);
    return true;
  };

  const handleNext = () => {
    if (validateStep()) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    setError(null);
    setStep(step - 1);
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await empresaService.crear(data);
      if (result.empresa_id) {
        navigate(`/empresa/${result.empresa_id}/configuracion`);
      } else {
        navigate('/empresas');
      }
    } catch (err) {
      setError('Error al crear la empresa. Por favor intente nuevamente.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-50 to-blue-50 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800 transition-colors duration-300 py-12 relative overflow-hidden">
      {/* Background Mesh Effect */}
      <div className="absolute inset-0 opacity-30 pointer-events-none">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="mesh" width="40" height="40" patternUnits="userSpaceOnUse">
              <circle cx="20" cy="20" r="1" fill="currentColor" className="text-blue-200 dark:text-blue-900" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#mesh)" />
        </svg>
      </div>

      <div className="max-w-3xl mx-auto px-4 relative z-10">
        <div className="text-center mb-8 animate-fade-in-up">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl mx-auto mb-4 flex items-center justify-center shadow-lg shadow-blue-500/30">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2 tracking-tight">Nueva Empresa</h1>
          <p className="text-slate-500 dark:text-slate-400">Configure su entorno empresarial en unos simples pasos</p>
        </div>

        <StepIndicator currentStep={step} totalSteps={totalSteps} />

        <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 dark:border-slate-700/50 p-8 animate-fade-in" style={{ animationDelay: '100ms' }}>
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-700 dark:text-red-300 text-sm flex items-center gap-3">
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {error}
            </div>
          )}

          {step === 1 && <StepInfoBasica data={data} onChange={setData} />}
          {step === 2 && <StepEstrategia data={data} onChange={setData} />}
          {step === 3 && <StepTipologias data={data} onChange={setData} />}
          {step === 4 && <StepConfirmacion data={data} />}

          <div className="flex justify-between mt-10 pt-6 border-t border-slate-200 dark:border-slate-700">
            <button
              onClick={step === 1 ? () => navigate('/empresas') : handleBack}
              className="px-6 py-2.5 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors font-medium"
            >
              {step === 1 ? 'Cancelar' : 'Anterior'}
            </button>

            {step < totalSteps ? (
              <button
                onClick={handleNext}
                className="px-8 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl shadow-lg shadow-blue-500/25 transition-all hover:scale-[1.02] font-medium"
              >
                Siguiente
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="px-8 py-2.5 bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white rounded-xl shadow-lg shadow-emerald-500/25 transition-all hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Creando...</span>
                  </>
                ) : (
                  'Crear Empresa'
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
