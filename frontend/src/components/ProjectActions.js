import React, { useState } from 'react';
import axios from 'axios';

const ProjectActions = ({ projectId, projectData, onResultsUpdate }) => {
  const [validating, setValidating] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleValidateAllDocs = async () => {
    setValidating(true);
    setError(null);
    try {
      // Add null checks for projectData
      const documents = (projectData?.documents) || (projectData?.documentos) || [];
      const docsToValidate = (documents || []).map((doc, idx) => ({
        id: (doc?.id) || (doc?._id) || `doc-${idx}`,
        name: (doc?.name) || (doc?.nombre) || (doc?.filename) || 'Sin nombre',
        path: (doc?.path) || (doc?.filePath) || (doc?.file_path) || '',
        type: (doc?.type) || (doc?.tipo) || 'evidencia',
        expected_data: {
          monto: (projectData?.monto_contrato) || (projectData?.montoContrato),
          rfc_proveedor: (projectData?.rfc_proveedor) || (projectData?.rfcProveedor),
          fecha: (projectData?.fecha_contrato) || (projectData?.fechaContrato)
        }
      }));

      if (!projectId) {
        throw new Error('Project ID is required');
      }

      const response = await axios.post(`/api/loops/projects/${projectId}/validate-all-documents`, {
        documents: docsToValidate
      });

      // Add null checks for response data
      const responseData = (response?.data) || {};
      setResults({
        type: 'ocr',
        data: responseData
      });

      if (onResultsUpdate && responseData) {
        onResultsUpdate('ocr', responseData);
      }
    } catch (err) {
      console.error('Error validating:', err);
      setError((err?.response?.data?.detail) || (err?.message) || 'Error al validar documentos');
    }
    setValidating(false);
  };

  const handleRedTeam = async () => {
    setSimulating(true);
    setError(null);
    try {
      // Add null checks for projectData properties
      const projectDataToSend = {
        tipologia: (projectData?.tipologia) || (projectData?.category),
        monto_contrato: (projectData?.monto_contrato) || (projectData?.montoContrato) || (projectData?.amount) || 0,
        descripcion_servicio: (projectData?.descripcion) || (projectData?.description) || '',
        justificacion_economica: (projectData?.justificacion_economica) || (projectData?.justificacionEconomica) || '',
        beneficio_esperado: (projectData?.beneficio_esperado) || (projectData?.beneficioEsperado) || '',
        risk_score: (projectData?.risk_score) || (projectData?.riskScore) || 0,
        documentos: ((projectData?.documents) || (projectData?.documentos) || []).map(d => ({
          tipo: (d?.type) || (d?.tipo) || 'documento',
          existe: !!((d?.path) || (d?.filePath)),
          validado: (d?.validated) || (d?.validado) || false
        })),
        resultados_agentes: (projectData?.deliberations) || (projectData?.resultadosAgentes) || []
      };

      if (!projectId) {
        throw new Error('Project ID is required');
      }

      const response = await axios.post(`/api/loops/projects/${projectId}/red-team-simulation`, {
        project_data: projectDataToSend
      });

      // Add null checks for response data
      const responseData = (response?.data) || {};
      setResults({
        type: 'redteam',
        data: responseData
      });

      if (onResultsUpdate && responseData) {
        onResultsUpdate('redteam', responseData);
      }
    } catch (err) {
      console.error('Error in simulation:', err);
      setError((err?.response?.data?.detail) || (err?.message) || 'Error en la simulación');
    }
    setSimulating(false);
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL': return 'text-red-600 bg-red-100';
      case 'HIGH': return 'text-orange-600 bg-orange-100';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-100';
      case 'LOW': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="mt-6 p-4 bg-gradient-to-r from-slate-800 to-slate-900 rounded-xl border border-slate-700">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <span className="text-2xl">🔄</span> Loops Iterativos
      </h3>
      
      <div className="flex flex-wrap gap-3 mb-4">
        <button
          onClick={handleValidateAllDocs}
          disabled={validating}
          className="px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2 font-medium"
        >
          {validating ? (
            <>
              <span className="animate-spin">⏳</span> Validando OCR...
            </>
          ) : (
            <>
              <span>🔍</span> Validar Documentos (Loop)
            </>
          )}
        </button>
        
        <button
          onClick={handleRedTeam}
          disabled={simulating}
          className="px-4 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2 font-medium"
        >
          {simulating ? (
            <>
              <span className="animate-pulse">⚔️</span> Simulando ataque...
            </>
          ) : (
            <>
              <span>🛡️</span> Simulación Red Team
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-900/50 border border-red-500 rounded-lg text-red-200 text-sm mb-4">
          <strong>Error:</strong> {error}
        </div>
      )}

      {results && (
        <div className="mt-4 p-4 bg-slate-700/50 rounded-lg">
          {(results?.type === 'ocr') && (results?.data?.success) && (
            <div>
              <h4 className="text-white font-medium mb-3 flex items-center gap-2">
                <span>📄</span> Resultados OCR Validation
              </h4>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="bg-green-900/30 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-green-400">{(results?.data?.validated) || 0}</div>
                  <div className="text-xs text-green-300">Validados</div>
                </div>
                <div className="bg-yellow-900/30 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-yellow-400">{(results?.data?.requires_review) || 0}</div>
                  <div className="text-xs text-yellow-300">Requieren Revisión</div>
                </div>
                <div className="bg-red-900/30 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-red-400">{(results?.data?.failed) || 0}</div>
                  <div className="text-xs text-red-300">Fallidos</div>
                </div>
              </div>
              <div className="text-sm text-slate-300">
                Tasa de éxito: <span className="text-white font-medium">{(((results?.data?.success_rate) || 0) * 100).toFixed(0)}%</span>
              </div>
            </div>
          )}

          {(results?.type === 'redteam') && (results?.data?.success) && (
            <div>
              <h4 className="text-white font-medium mb-3 flex items-center gap-2">
                <span>🛡️</span> Resultados Red Team Simulation
              </h4>

              <div className="flex items-center gap-4 mb-4">
                <div className={`px-4 py-2 rounded-lg font-bold ${
                  (results?.data?.data?.bulletproof)
                    ? 'bg-green-600 text-white'
                    : 'bg-red-600 text-white'
                }`}>
                  {(results?.data?.data?.bulletproof) ? '✅ BULLETPROOF' : '⚠️ VULNERABLE'}
                </div>
                <div className={`px-3 py-1 rounded ${getSeverityColor(results?.data?.data?.nivel_riesgo)}`}>
                  Riesgo: {(results?.data?.data?.nivel_riesgo) || 'N/A'}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                <div className="text-slate-300">
                  Vectores testeados: <span className="text-white font-medium">{(results?.data?.data?.vectores_testeados) || 0}</span>
                </div>
                <div className="text-slate-300">
                  Vulnerabilidades: <span className="text-white font-medium">{(results?.data?.data?.vulnerabilidades_encontradas) || 0}</span>
                </div>
              </div>

              {((results?.data?.data?.vulnerabilidades) || []).length > 0 && (
                <div className="mt-4">
                  <h5 className="text-white text-sm font-medium mb-2">Vulnerabilidades encontradas:</h5>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {(results?.data?.data?.vulnerabilidades || []).map((v, idx) => (
                      <div key={idx} className="p-3 bg-slate-800 rounded-lg text-sm">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getSeverityColor(v?.severity)}`}>
                            {(v?.severity) || 'UNKNOWN'}
                          </span>
                          <span className="text-slate-400">{(v?.vector_name) || 'Unknown vector'}</span>
                        </div>
                        <p className="text-slate-200">{(v?.description) || 'Sin descripción'}</p>
                        {(v?.recommendation) && (
                          <p className="text-green-400 text-xs mt-1">💡 {v.recommendation}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="mt-4 p-3 bg-slate-800 rounded-lg text-sm text-slate-300">
                <strong>Conclusión:</strong> {(results?.data?.data?.conclusion) || 'No hay conclusión disponible'}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ProjectActions;
