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
  'Tecnología',
  'Finanzas',
  'Manufactura',
  'Retail',
  'Servicios Profesionales',
  'Construcción',
  'Salud',
  'Educación',
  'Transporte y Logística',
  'Energía',
  'Agroindustria',
  'Otro'
];

const StepIndicator = ({ currentStep, totalSteps }) => {
  return (
    <div className="flex items-center justify-center mb-8">
      {[...Array(totalSteps)].map((_, index) => (
        <React.Fragment key={index}>
          <div 
            className={`w-10 h-10 rounded-full flex items-center justify-center font-medium transition-all ${
              index + 1 < currentStep 
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

const StepInfoBasica = ({ data, onChange }) => (
  <div className="space-y-6">
    <h2 className="text-xl font-semibold text-gray-800 mb-4">Información Básica</h2>
    <p className="text-gray-600 text-sm mb-6">Complete la información básica de su empresa para comenzar.</p>
    
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">Nombre de la Empresa *</label>
      <input
        type="text"
        value={data.nombre || ''}
        onChange={(e) => onChange({ ...data, nombre: e.target.value })}
        placeholder="Ej: Grupo Fortezza S.A. de C.V."
        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      />
    </div>

    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">RFC *</label>
      <input
        type="text"
        value={data.rfc || ''}
        onChange={(e) => onChange({ ...data, rfc: e.target.value.toUpperCase() })}
        placeholder="Ej: GFO850101XXX"
        maxLength={13}
        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 uppercase"
      />
    </div>

    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">Industria *</label>
      <select
        value={data.industria || ''}
        onChange={(e) => onChange({ ...data, industria: e.target.value })}
        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        <option value="">Seleccione una industria</option>
        {INDUSTRIAS.map((industria) => (
          <option key={industria} value={industria}>{industria}</option>
        ))}
      </select>
    </div>

    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">Email de Contacto</label>
      <input
        type="email"
        value={data.email || ''}
        onChange={(e) => onChange({ ...data, email: e.target.value })}
        placeholder="contacto@empresa.com"
        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      />
    </div>
  </div>
);

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
            className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
              tipologiasActivas.includes(tipologia.id)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-blue-300'
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
          <p className="text-sm text-gray-500">Nombre</p>
          <p className="font-medium text-gray-800">{data.nombre || '-'}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">RFC</p>
          <p className="font-medium text-gray-800">{data.rfc || '-'}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Industria</p>
          <p className="font-medium text-gray-800">{data.industria || '-'}</p>
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
    nombre: '',
    rfc: '',
    industria: '',
    email: '',
    vision: '',
    mision: '',
    pilares_estrategicos: [],
    tipologias_activas: []
  });

  const totalSteps = 4;

  const validateStep = () => {
    switch (step) {
      case 1:
        if (!data.nombre?.trim()) {
          setError('El nombre de la empresa es requerido');
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-12">
      <div className="max-w-2xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Nueva Empresa</h1>
          <p className="text-gray-600">Configure su empresa en unos simples pasos</p>
        </div>

        <StepIndicator currentStep={step} totalSteps={totalSteps} />

        <div className="bg-white rounded-xl shadow-lg p-8">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {step === 1 && <StepInfoBasica data={data} onChange={setData} />}
          {step === 2 && <StepEstrategia data={data} onChange={setData} />}
          {step === 3 && <StepTipologias data={data} onChange={setData} />}
          {step === 4 && <StepConfirmacion data={data} />}

          <div className="flex justify-between mt-8 pt-6 border-t">
            <button
              onClick={step === 1 ? () => navigate('/empresas') : handleBack}
              className="px-6 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              {step === 1 ? 'Cancelar' : 'Anterior'}
            </button>

            {step < totalSteps ? (
              <button
                onClick={handleNext}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Siguiente
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {loading ? 'Creando...' : 'Crear Empresa'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
