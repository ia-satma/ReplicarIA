import { useState, useCallback } from 'react';

const ONBOARDING_STEPS = [
  {
    id: 0,
    key: 'welcome',
    title: 'Bienvenida',
    description: 'Identificar tipo de entidad',
    requiredFields: [],
    agent: 'ARCHIVO',
  },
  {
    id: 1,
    key: 'entity_type',
    title: 'Tipo de Entidad',
    description: 'Seleccionar cliente o proveedor',
    requiredFields: ['entityType'],
    agent: 'ARCHIVO',
  },
  {
    id: 2,
    key: 'basic_info',
    title: 'Información Básica',
    description: 'RFC, razón social, datos de contacto',
    requiredFields: ['rfc', 'razonSocial'],
    agent: 'ARCHIVO',
  },
  {
    id: 3,
    key: 'documents',
    title: 'Documentación',
    description: 'Subir constancia fiscal, identificación',
    requiredFields: ['constanciaFiscal'],
    agent: 'ARCHIVO',
  },
  {
    id: 4,
    key: 'ai_analysis',
    title: 'Análisis IA',
    description: 'Extracción automática de datos',
    requiredFields: [],
    agent: 'ARCHIVO',
  },
  {
    id: 5,
    key: 'confirmation',
    title: 'Confirmación',
    description: 'Validar datos extraídos',
    requiredFields: ['dataConfirmed'],
    agent: 'ARCHIVO',
  },
  {
    id: 6,
    key: 'efos_check',
    title: 'Verificación EFOS',
    description: 'Consulta Lista 69-B SAT',
    requiredFields: [],
    agent: 'A6_PROVEEDOR',
  },
  {
    id: 7,
    key: 'complete',
    title: 'Completado',
    description: 'Entidad registrada exitosamente',
    requiredFields: [],
    agent: 'ARCHIVO',
  },
];

export function useOnboardingSteps(initialStep = 0) {
  const [currentStep, setCurrentStep] = useState(initialStep);
  const [collectedData, setCollectedData] = useState({});
  const [entityType, setEntityType] = useState(null);
  const [extractedData, setExtractedData] = useState({});
  const [onboardingStatus, setOnboardingStatus] = useState('idle');
  const [onboardingError, setOnboardingError] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [intelligentMode, setIntelligentMode] = useState(false);
  const [createdEntity, setCreatedEntity] = useState(null);
  const [emailContacto, setEmailContacto] = useState('');
  const [createdClienteId, setCreatedClienteId] = useState(null);

  const currentStepData = typeof currentStep === 'number' ? ONBOARDING_STEPS[currentStep] : null;

  const validateStep = useCallback((stepIndex = currentStep) => {
    if (typeof stepIndex !== 'number') return { valid: true, missingFields: [] };
    
    const step = ONBOARDING_STEPS[stepIndex];
    if (!step) return { valid: false, missingFields: [] };

    const missingFields = step.requiredFields.filter((field) => {
      const value = collectedData[field] || extractedData[field];
      return !value || (typeof value === 'string' && value.trim() === '');
    });

    return {
      valid: missingFields.length === 0,
      missingFields,
    };
  }, [currentStep, collectedData, extractedData]);

  const nextStep = useCallback(() => {
    if (typeof currentStep !== 'number') return false;
    
    const validation = validateStep();
    
    if (!validation.valid) {
      setOnboardingError(`Campos requeridos faltantes: ${validation.missingFields.join(', ')}`);
      return false;
    }

    if (currentStep < ONBOARDING_STEPS.length - 1) {
      setCurrentStep((prev) => prev + 1);
      setOnboardingError(null);
      return true;
    }

    return false;
  }, [currentStep, validateStep]);

  const prevStep = useCallback(() => {
    if (typeof currentStep !== 'number') return false;
    
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
      setOnboardingError(null);
      return true;
    }
    return false;
  }, [currentStep]);

  const goToStep = useCallback((stepIndex) => {
    if (typeof stepIndex === 'number' && stepIndex >= 0 && stepIndex < ONBOARDING_STEPS.length) {
      setCurrentStep(stepIndex);
      setOnboardingError(null);
      return true;
    } else if (typeof stepIndex === 'string') {
      setCurrentStep(stepIndex);
      setOnboardingError(null);
      return true;
    }
    return false;
  }, []);

  const updateCollectedData = useCallback((key, value) => {
    setCollectedData((prev) => ({
      ...prev,
      [key]: value,
    }));
  }, []);

  const mergeCollectedData = useCallback((data) => {
    setCollectedData((prev) => ({
      ...prev,
      ...data,
    }));
  }, []);

  const mergeExtractedData = useCallback((data) => {
    setExtractedData((prev) => ({
      ...prev,
      ...data,
    }));
  }, []);

  const selectEntityType = useCallback((type) => {
    if (type === 'cliente' || type === 'proveedor') {
      setEntityType(type);
      updateCollectedData('entityType', type);
      return true;
    }
    return false;
  }, [updateCollectedData]);

  const confirmExtractedData = useCallback(() => {
    setCollectedData((prev) => ({
      ...prev,
      ...extractedData,
      dataConfirmed: true,
    }));
    setShowConfirmation(false);
  }, [extractedData]);

  const completeOnboarding = useCallback(async (entityData) => {
    setOnboardingStatus('completed');
    setCreatedEntity(entityData);
    goToStep(ONBOARDING_STEPS.length - 1);
  }, [goToStep]);

  const resetOnboarding = useCallback(() => {
    setCurrentStep(0);
    setCollectedData({});
    setEntityType(null);
    setExtractedData({});
    setOnboardingStatus('idle');
    setOnboardingError(null);
    setShowConfirmation(false);
    setCreatedEntity(null);
    setEmailContacto('');
    setCreatedClienteId(null);
  }, []);

  const getProgress = useCallback(() => {
    if (typeof currentStep !== 'number') return { current: 0, total: ONBOARDING_STEPS.length, percentage: 0 };
    
    return {
      current: currentStep,
      total: ONBOARDING_STEPS.length,
      percentage: Math.round((currentStep / (ONBOARDING_STEPS.length - 1)) * 100),
    };
  }, [currentStep]);

  const isStepCompleted = useCallback((stepIndex) => {
    if (typeof currentStep !== 'number') return false;
    return stepIndex < currentStep;
  }, [currentStep]);

  const isStepAccessible = useCallback((stepIndex) => {
    if (typeof currentStep !== 'number') return false;
    return stepIndex <= currentStep;
  }, [currentStep]);

  return {
    currentStep,
    currentStepData,
    steps: ONBOARDING_STEPS,
    collectedData,
    entityType,
    extractedData,
    onboardingStatus,
    onboardingError,
    showConfirmation,
    intelligentMode,
    createdEntity,
    emailContacto,
    createdClienteId,

    nextStep,
    prevStep,
    goToStep,
    setCurrentStep,

    updateCollectedData,
    mergeCollectedData,
    mergeExtractedData,
    selectEntityType,
    confirmExtractedData,
    setShowConfirmation,
    setIntelligentMode,
    setEmailContacto,
    setCreatedClienteId,
    setCollectedData,
    setExtractedData,
    setOnboardingStatus,
    setOnboardingError,

    completeOnboarding,
    resetOnboarding,

    validateStep,
    getProgress,
    isStepCompleted,
    isStepAccessible,

    clearError: () => setOnboardingError(null),
  };
}

export default useOnboardingSteps;
