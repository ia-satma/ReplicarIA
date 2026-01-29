import { useState, useEffect } from "react";
import AgentWorkflowVisualization from "./components/AgentWorkflowVisualization";
import api from "./services/api";

const ProjectForm = () => {
  const [loading, setLoading] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState(false);
  const [success, setSuccess] = useState(false);
  const [projectId, setProjectId] = useState(null);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [error, setError] = useState("");
  
  const [companies, setCompanies] = useState([]);
  const [loadingCompanies, setLoadingCompanies] = useState(true);
  const [folios, setFolios] = useState([]);
  const [loadingFolios, setLoadingFolios] = useState(false);
  const [selectedParentProject, setSelectedParentProject] = useState(null);
  
  const [formData, setFormData] = useState({
    project_name: "",
    sponsor_name: "",
    sponsor_email: "",
    company_name: "",
    selected_company: "",
    budget_estimate: "",
    description: "",
    urgency_level: "Normal",
    departments: [],
    requires_human: "No",
    fiscal_document: null,
    constitutiva: null,
    project_documents: [],
    is_modification: false,
    parent_folio: "",
    modification_notes: ""
  });

  const [fileUrls, setFileUrls] = useState({
    fiscal_document: "",
    constitutiva: "",
    project_documents: []
  });

  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        setLoadingCompanies(true);
        const response = await api.get('/api/auth/companies');
        if (response.data.success && response.data.companies) {
          const companiesWithNew = [...response.data.companies, { id: "nueva", name: "Otra empresa (nueva)" }];
          setCompanies(companiesWithNew);
        } else {
          setCompanies([{ id: "nueva", name: "Otra empresa (nueva)" }]);
        }
      } catch (err) {
        console.error("Error fetching companies:", err);
        setCompanies([{ id: "nueva", name: "Otra empresa (nueva)" }]);
      } finally {
        setLoadingCompanies(false);
      }
    };

    fetchCompanies();
  }, []);

  useEffect(() => {
    if (formData.is_modification) {
      const fetchFolios = async () => {
        try {
          setLoadingFolios(true);
          const response = await api.get('/api/projects/folios');
          if (response.data.success && response.data.folios) {
            setFolios(response.data.folios);
          }
        } catch (err) {
          console.error("Error fetching folios:", err);
        } finally {
          setLoadingFolios(false);
        }
      };
      fetchFolios();
    }
  }, [formData.is_modification]);

  const selectedCompanyObj = companies.find(c => c.id === formData.selected_company);
  const showNewCompanyFields = formData.selected_company === "nueva";

  const departments = [
    "Operaciones",
    "Legal", 
    "Recursos Humanos",
    "Marketing",
    "Finanzas",
    "Compras",
    "Calidad",
    "Proyectos y Arquitectura"
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    if (name === 'selected_company' && value && value !== 'nueva') {
      localStorage.setItem('selected_empresa_id', value);
    }
  };

  const handleFileChange = async (e, fieldName) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploadingFiles(true);
    setError("");

    try {
      const formDataFile = new FormData();
      formDataFile.append('file', file);
      
      const response = await api.post('/api/projects/upload-file', formDataFile, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });

      if (response.data.success) {
        setFileUrls(prev => ({
          ...prev,
          [fieldName]: response.data.file_url
        }));
        setFormData(prev => ({
          ...prev,
          [fieldName]: file
        }));
      }
    } catch (err) {
      setError(`No pudimos guardar tu archivo: ${err.response?.data?.detail || err.message}`);
    } finally {
      setUploadingFiles(false);
    }
  };

  const handleAdditionalFiles = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setUploadingFiles(true);
    setError("");

    try {
      const uploadPromises = files.map(async (file) => {
        const formDataFile = new FormData();
        formDataFile.append('file', file);
        
        const response = await api.post('/api/projects/upload-file', formDataFile, {
          headers: {
            'Content-Type': 'multipart/form-data',
          }
        });

        return response.data.file_url;
      });

      const urls = await Promise.all(uploadPromises);
      
      setFileUrls(prev => ({
        ...prev,
        project_documents: [...prev.project_documents, ...urls]
      }));
      
      setFormData(prev => ({
        ...prev,
        project_documents: [...prev.project_documents, ...files]
      }));
    } catch (err) {
      setError(`No pudimos guardar algunos archivos: ${err.response?.data?.detail || err.message}`);
    } finally {
      setUploadingFiles(false);
    }
  };

  const handleDepartmentToggle = (dept) => {
    setFormData(prev => ({
      ...prev,
      departments: prev.departments.includes(dept)
        ? prev.departments.filter(d => d !== dept)
        : [...prev.departments, dept]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess(false);

    const urlParams = new URLSearchParams(window.location.search);
    const isDemoMode = urlParams.get('demo') === 'true';

    if (isDemoMode) {
      setTimeout(() => {
        setSuccess(true);
        setProjectId('DEMO-' + Date.now());
        setLoading(false);
      }, 1500);
      return;
    }

    try {
      const companyName = showNewCompanyFields ? formData.company_name : (selectedCompanyObj?.name || '');
      const projectData = {
        project_name: formData.project_name,
        sponsor_name: formData.sponsor_name,
        sponsor_email: formData.sponsor_email,
        company_name: companyName,
        department: formData.departments.join(", "),
        description: formData.description,
        strategic_alignment: formData.project_name,
        expected_economic_benefit: parseFloat(formData.budget_estimate) * 2.5,
        budget_estimate: parseFloat(formData.budget_estimate),
        duration_months: 12,
        urgency_level: formData.urgency_level,
        requires_human: formData.requires_human,
        attachments: [
          ...(showNewCompanyFields ? [fileUrls.fiscal_document, fileUrls.constitutiva] : []),
          ...fileUrls.project_documents
        ].filter(url => url),
        is_modification: formData.is_modification,
        parent_folio: formData.parent_folio,
        modification_notes: formData.modification_notes
      };

      const response = await api.post('/api/projects/submit', projectData);
      
      if (response.data.success) {
        setProjectId(response.data.project_id);
        setSuccess(true);
        setFormData({
          project_name: "",
          sponsor_name: "",
          sponsor_email: "",
          company_name: "",
          selected_company: "",
          budget_estimate: "",
          description: "",
          urgency_level: "Normal",
          departments: [],
          requires_human: "No",
          fiscal_document: null,
          constitutiva: null,
          project_documents: [],
          is_modification: false,
          parent_folio: "",
          modification_notes: ""
        });
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Oops, algo no salió bien. Por favor intenta nuevamente.");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalysisComplete = (result) => {
    setAnalysisComplete(true);
    setTimeout(() => {
      window.location.href = "/";
    }, 3000);
  };

  const handleAnalysisError = (err) => {
    console.error("Error en análisis:", err);
  };

  if (success) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
        padding: '32px 16px'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ 
            textAlign: 'center', 
            marginBottom: '32px',
            padding: '24px',
            background: 'rgba(30, 41, 59, 0.8)',
            borderRadius: '16px',
            border: '1px solid #334155'
          }}>
            <div style={{
              width: '64px',
              height: '64px',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, #22c55e, #10b981)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px'
            }}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <h1 style={{ 
              fontSize: '28px', 
              fontWeight: '700', 
              color: '#f1f5f9',
              marginBottom: '8px'
            }}>
              Proyecto Recibido Exitosamente
            </h1>
            <p style={{ 
              color: '#94a3b8', 
              fontSize: '15px',
              maxWidth: '500px',
              margin: '0 auto'
            }}>
              Nuestros agentes de inteligencia artificial están analizando tu proyecto en tiempo real
            </p>
          </div>
          
          <AgentWorkflowVisualization
            projectId={projectId}
            onComplete={handleAnalysisComplete}
            onError={handleAnalysisError}
          />
          
          <div style={{ 
            marginTop: '24px', 
            textAlign: 'center',
            padding: '20px',
            background: 'rgba(30, 41, 59, 0.6)',
            borderRadius: '12px',
            border: '1px solid #334155'
          }}>
            <p style={{ 
              color: '#94a3b8', 
              fontSize: '13px',
              marginBottom: '16px'
            }}>
              Tu expediente de defensa fiscal se generará automáticamente al completar el análisis.
            </p>
            {analysisComplete && (
              <p style={{ 
                color: '#86efac', 
                fontSize: '14px',
                fontWeight: '500',
                marginBottom: '16px'
              }}>
                ✓ Análisis completado. Redirigiendo a tu panel...
              </p>
            )}
            <button
              onClick={() => window.location.href = "/"}
              style={{
                padding: '12px 24px',
                borderRadius: '8px',
                background: 'transparent',
                border: '1px solid #475569',
                color: '#e2e8f0',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#334155';
                e.target.style.borderColor = '#64748b';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'transparent';
                e.target.style.borderColor = '#475569';
              }}
            >
              Ir a tu Panel
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-emerald-50 to-teal-50 py-8 sm:py-12 px-4 sm:px-6">
      <div className="max-w-4xl mx-auto">
        <div className="glass-card overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-[#54ddaf] to-[#3bb896] p-4 sm:p-6 lg:p-8">
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-[#021423] mb-2">
              🚀 Cuéntanos sobre tu Proyecto
            </h1>
            <p className="text-[#021423]/80 text-sm sm:text-base">
              Nuestros agentes IA analizarán tu iniciativa y te darán retroalimentación en tiempo real
            </p>
          </div>

          <form onSubmit={handleSubmit} className="p-4 sm:p-6 lg:p-8 space-y-4 sm:space-y-6">
            {/* Error Message */}
            {error && (
              <div className="bg-red-50/80 backdrop-blur-sm border border-red-200 rounded-xl p-3 sm:p-4 animate-scale-in">
                <p className="text-red-700 text-sm sm:text-base flex items-center gap-2">
                  <span className="text-lg flex-shrink-0">⚠️</span>
                  <span>{error}</span>
                </p>
              </div>
            )}

            {/* Modification Toggle */}
            <div className="bg-gradient-to-r from-amber-50/80 to-orange-50/80 backdrop-blur-sm border border-amber-200 rounded-xl p-3 sm:p-4">
              <label className="flex items-center cursor-pointer gap-3">
                <input
                  type="checkbox"
                  checked={formData.is_modification}
                  onChange={(e) => {
                    setFormData(prev => ({ 
                      ...prev, 
                      is_modification: e.target.checked,
                      parent_folio: e.target.checked ? prev.parent_folio : "",
                      modification_notes: e.target.checked ? prev.modification_notes : ""
                    }));
                    if (!e.target.checked) {
                      setSelectedParentProject(null);
                    }
                  }}
                  className="w-5 h-5 min-w-[20px] text-amber-600 rounded focus:ring-amber-500 cursor-pointer"
                />
                <span className="text-sm sm:text-base font-semibold text-amber-800">
                  ¿Este proyecto es una actualización de uno anterior?
                </span>
              </label>
              
              {formData.is_modification && (
                <div className="mt-4 space-y-4 border-t border-amber-200 pt-4">
                  <div>
                    <label className="label-premium">
                      ¿Cuál es el proyecto anterior que actualizas? *
                    </label>
                    {loadingFolios ? (
                      <div className="input-premium bg-gray-100 text-gray-500 cursor-not-allowed">
                        Traemos tus proyectos...
                      </div>
                    ) : folios.length === 0 ? (
                      <div className="input-premium bg-yellow-50 text-amber-700 border-amber-300">
                        No hay proyectos disponibles para actualizar. Los proyectos aparecerán aquí cuando hayan pasado por revisión.
                      </div>
                    ) : (
                      <select
                        name="parent_folio"
                        required={formData.is_modification}
                        value={formData.parent_folio}
                        onChange={(e) => {
                          const folio = e.target.value;
                          handleChange(e);
                          const project = folios.find(f => f.folio === folio);
                          setSelectedParentProject(project || null);
                        }}
                        className="input-premium"
                      >
                        <option value="">Elige el proyecto a actualizar...</option>
                        {folios.map(item => (
                          <option key={item.folio} value={item.folio}>
                            {item.folio} - {item.project_name} ({item.company_name})
                          </option>
                        ))}
                      </select>
                    )}
                    
                    {selectedParentProject && (
                      <div className="mt-3 p-4 bg-blue-50/80 border border-blue-200 rounded-xl animate-scale-in">
                        <h4 className="text-sm font-semibold text-blue-800 mb-2 flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Información del Proyecto Seleccionado
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
                          <div>
                            <span className="text-gray-500">Empresa/Proveedor:</span>
                            <p className="font-medium text-gray-800">{selectedParentProject.company_name || "N/A"}</p>
                          </div>
                          <div>
                            <span className="text-gray-500">Estado:</span>
                            <p className="font-medium text-gray-800">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                                selectedParentProject.status === 'approved' 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {selectedParentProject.status === 'approved' ? 'Aprobado' : 'En Revisión'}
                              </span>
                            </p>
                          </div>
                          {selectedParentProject.amount > 0 && (
                            <div>
                              <span className="text-gray-500">Monto:</span>
                              <p className="font-medium text-gray-800">
                                ${Number(selectedParentProject.amount).toLocaleString('es-MX')}
                              </p>
                            </div>
                          )}
                          {selectedParentProject.deliberation_count > 0 && (
                            <div>
                              <span className="text-gray-500">Deliberaciones:</span>
                              <p className="font-medium text-gray-800">{selectedParentProject.deliberation_count}</p>
                            </div>
                          )}
                          {selectedParentProject.description && (
                            <div className="sm:col-span-2">
                              <span className="text-gray-500">Descripción:</span>
                              <p className="font-medium text-gray-800 line-clamp-2">{selectedParentProject.description}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div>
                    <label className="label-premium">
                      ¿Qué cambios o mejoras solicitas en esta actualización? *
                    </label>
                    <textarea
                      name="modification_notes"
                      required={formData.is_modification}
                      rows="3"
                      value={formData.modification_notes}
                      onChange={handleChange}
                      className="input-premium"
                      placeholder="Cuéntanos qué cambios, mejoras o ajustes necesitas en relación al proyecto anterior..."
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Sé específico con los cambios que deseas realizar.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Información del Proyecto */}
            <div>
              <label className="label-premium">
                ¿Cómo se llama tu proyecto? *
              </label>
              <input
                type="text"
                name="project_name"
                required
                value={formData.project_name}
                onChange={handleChange}
                className="input-premium"
                placeholder="Ej: Sistema IA Predictivo 2026"
              />
              <p className="text-xs text-gray-500 mt-1">
                Elige un nombre descriptivo y único para tu iniciativa.
              </p>
            </div>

            {/* Datos del Solicitante */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
              <div>
                <label className="label-premium">
                  Tu nombre completo *
                </label>
                <input
                  type="text"
                  name="sponsor_name"
                  required
                  value={formData.sponsor_name}
                  onChange={handleChange}
                  className="input-premium"
                  placeholder="Nombre completo"
                />
              </div>

              <div>
                <label className="label-premium">
                  Tu correo electrónico *
                </label>
                <input
                  type="email"
                  name="sponsor_email"
                  required
                  value={formData.sponsor_email}
                  onChange={handleChange}
                  className="input-premium"
                  placeholder="email@empresa.com"
                />
              </div>
            </div>

            {/* Razón Social - Selector */}
            <div>
              <label className="label-premium">
                ¿En cuál empresa es este proyecto? *
              </label>
              {loadingCompanies ? (
                <div className="input-premium bg-gray-100 text-gray-500 cursor-not-allowed">
                  Traemos tus empresas...
                </div>
              ) : (
                <select
                  name="selected_company"
                  required
                  value={formData.selected_company}
                  onChange={handleChange}
                  className="input-premium"
                >
                  <option value="">Elige tu empresa...</option>
                  {companies.map(company => (
                    <option key={company.id} value={company.id}>{company.name}</option>
                  ))}
                </select>
              )}
            </div>

            {/* Campos para Nueva Empresa - Solo si selecciona "Otra empresa" */}
            {showNewCompanyFields && (
              <>
                <div className="bg-yellow-50/80 backdrop-blur-sm border border-yellow-200 rounded-xl p-4 sm:p-6">
                  <p className="text-sm sm:text-base font-semibold text-yellow-800 mb-4">
                    📝 Documentos Legales de tu Nueva Empresa
                  </p>
                  
                  {/* Nombre de la nueva empresa */}
                  <div className="mb-4">
                    <label className="label-premium">
                      Nombre legal de la empresa *
                    </label>
                    <input
                      type="text"
                      name="company_name"
                      required={showNewCompanyFields}
                      value={formData.company_name}
                      onChange={handleChange}
                      className="input-premium"
                      placeholder="Nombre legal completo de la empresa"
                    />
                  </div>

                  {/* Constancia Fiscal */}
                  <div className="mb-4">
                    <label className="label-premium">
                      Constancia de Situación Fiscal del SAT *
                    </label>
                    <div className="relative">
                      <input
                        type="file"
                        required={showNewCompanyFields}
                        accept=".pdf,.jpg,.png,.jpeg"
                        onChange={(e) => handleFileChange(e, 'fiscal_document')}
                        className="w-full px-4 py-3 rounded-xl bg-gray-50/80 border-2 border-dashed border-yellow-300 text-transparent cursor-pointer hover:bg-gray-100/80 transition-colors file:hidden"
                      />
                      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <span className="text-yellow-600 text-sm font-medium">📄 Selecciona documento...</span>
                      </div>
                    </div>
                    {formData.fiscal_document && (
                      <p className="text-xs text-green-600 mt-2 flex items-center gap-1">
                        <span>✓</span>
                        <span>{formData.fiscal_document.name} ({(formData.fiscal_document.size / 1024).toFixed(1)} KB)</span>
                      </p>
                    )}
                  </div>

                  {/* Constitutiva */}
                  <div>
                    <label className="label-premium">
                      Acta Constitutiva de la Empresa *
                    </label>
                    <div className="relative">
                      <input
                        type="file"
                        required={showNewCompanyFields}
                        accept=".pdf,.jpg,.png,.jpeg"
                        onChange={(e) => handleFileChange(e, 'constitutiva')}
                        className="w-full px-4 py-3 rounded-xl bg-gray-50/80 border-2 border-dashed border-yellow-300 text-transparent cursor-pointer hover:bg-gray-100/80 transition-colors file:hidden"
                      />
                      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <span className="text-yellow-600 text-sm font-medium">📄 Selecciona documento...</span>
                      </div>
                    </div>
                    {formData.constitutiva && (
                      <p className="text-xs text-green-600 mt-2 flex items-center gap-1">
                        <span>✓</span>
                        <span>{formData.constitutiva.name} ({(formData.constitutiva.size / 1024).toFixed(1)} KB)</span>
                      </p>
                    )}
                  </div>
                </div>
              </>
            )}

            {/* Presupuesto */}
            <div>
              <label className="label-premium">
                ¿Cuál es el presupuesto estimado? (MXN) *
              </label>
              <input
                type="number"
                name="budget_estimate"
                required
                min="0"
                step="0.01"
                value={formData.budget_estimate}
                onChange={handleChange}
                className="input-premium"
                placeholder="1000000"
              />
              <p className="text-xs text-gray-500 mt-1">
                💡 El valor esperado se proyecta automáticamente multiplicando tu presupuesto por 2.5
              </p>
            </div>

            {/* Descripción */}
            <div>
              <label className="label-premium">
                ¿Qué esperas lograr con este proyecto? *
              </label>
              <textarea
                name="description"
                required
                rows="4"
                value={formData.description}
                onChange={handleChange}
                className="input-premium"
                placeholder="Cuéntanos los objetivos principales, alcance, resultados esperados y cualquier detalle importante..."
              />
              <p className="text-xs text-gray-500 mt-1">
                Sé específico y detallado para que nuestros agentes IA puedan analizar mejor tu proyecto.
              </p>
            </div>

            {/* Departamentos */}
            <div>
              <label className="label-premium">
                ¿Qué departamentos participarán en este proyecto? *
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {departments.map(dept => (
                  <label
                    key={dept}
                    className={`flex items-center p-3 rounded-xl border-2 cursor-pointer transition-all min-h-[44px] ${
                      formData.departments.includes(dept)
                        ? 'border-[#54ddaf] bg-[#54ddaf]/10'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={formData.departments.includes(dept)}
                      onChange={() => handleDepartmentToggle(dept)}
                      className="w-5 h-5 min-w-[20px] text-[#54ddaf] rounded cursor-pointer focus:ring-[#54ddaf]"
                    />
                    <span className="ml-2 text-sm text-gray-700">{dept}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Nivel de Urgencia */}
            <div>
              <label className="label-premium">
                ¿Cuál es la urgencia de este proyecto?
              </label>
              <select
                name="urgency_level"
                value={formData.urgency_level}
                onChange={handleChange}
                className="input-premium"
              >
                <option value="Baja">Baja</option>
                <option value="Normal">Normal</option>
                <option value="Alta">Alta</option>
                <option value="Urgente">Urgente</option>
              </select>
            </div>

            {/* Requiere Humano */}
            <div>
              <label className="label-premium">
                ¿Necesitas que un humano revise este proyecto también?
              </label>
              <select
                name="requires_human"
                value={formData.requires_human}
                onChange={handleChange}
                className="input-premium"
              >
                <option value="No">No</option>
                <option value="Sí">Sí</option>
              </select>
            </div>

            {/* Separador */}
            <div className="border-t-2 border-[#54ddaf]/30 pt-6 mt-8">
              <h3 className="text-xl sm:text-2xl font-bold text-gray-800 mb-2 flex items-center gap-2">
                <span>📄</span> Documentos de tu Proyecto
              </h3>
              <p className="text-xs sm:text-sm text-gray-600">
                <strong className="text-red-600">* Obligatorio</strong> - Sube los documentos, propuestas y detalles de tu proyecto. Nuestros agentes IA los analizarán y te enviarán sus recomendaciones por correo.
              </p>
            </div>

            {/* Documentos del Proyecto - CAMPO PRINCIPAL */}
            <div className="bg-gradient-to-br from-[#54ddaf]/10 to-[#3bb896]/10 border-2 border-dashed border-[#54ddaf] rounded-xl p-4 sm:p-6">
              <label className="block text-sm sm:text-base font-bold text-gray-800 mb-2">
                📎 Sube los Documentos de tu Proyecto *
              </label>
              <p className="text-xs sm:text-sm text-gray-600 mb-4">
                Incluye tu solicitud, propuestas, análisis técnicos, y toda la información que nuestros agentes IA necesitan analizar.
              </p>
              <div className="relative">
                <input
                  type="file"
                  multiple
                  required
                  accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.png,.jpeg"
                  onChange={handleAdditionalFiles}
                  className="w-full px-4 py-3 rounded-xl bg-white/50 border-2 border-dashed border-[#54ddaf] text-transparent cursor-pointer hover:bg-white transition-colors file:hidden"
                />
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                  <div className="w-8 h-8 flex items-center justify-center text-2xl mb-2 flex-shrink-0">📁</div>
                  <span className="text-sm sm:text-base font-medium text-gray-700 text-center px-4">
                    Arrastra archivos o haz clic para seleccionar
                  </span>
                </div>
              </div>
              
              {formData.project_documents.length > 0 && (
                <div className="mt-4 space-y-2 bg-white/80 rounded-lg p-3 sm:p-4">
                  <p className="text-xs sm:text-sm font-semibold text-green-700 mb-2 flex items-center gap-2">
                    <span>✅</span> Archivos listos para análisis ({formData.project_documents.length}):
                  </p>
                  {formData.project_documents.map((file, idx) => (
                    <p key={idx} className="text-xs text-green-600 flex items-center gap-2">
                      <span className="w-4 h-4 flex-shrink-0">📄</span>
                      <span className="break-words">{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
                    </p>
                  ))}
                </div>
              )}
            </div>

            {/* Indicador de carga de archivos */}
            {uploadingFiles && (
              <div className="bg-emerald-50/80 backdrop-blur-sm border border-emerald-200 rounded-xl p-3 sm:p-4 animate-scale-in">
                <p className="text-emerald-700 text-sm flex items-center gap-2">
                  <span className="animate-spin text-lg">⏳</span>
                  Estamos guardando tus archivos...
                </p>
              </div>
            )}

            {/* Botones */}
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 pt-4 mt-8">
              <button
                type="button"
                onClick={() => window.location.href = "/"}
                className="btn-ghost-premium w-full sm:w-auto"
              >
                Volver
              </button>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary-premium w-full sm:flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Estamos guardando..." : "Enviar Proyecto 🚀"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ProjectForm;
