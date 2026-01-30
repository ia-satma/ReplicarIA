import { useState, useEffect } from 'react';

// Critical fields that are required for client creation
const CRITICAL_FIELDS = ['rfc', 'razon_social', 'nombre'];

export function ConfirmationCard({
  title = 'Confirmar datos',
  data,
  onConfirm,
  onEdit,
  onCancel,
  isLoading = false,
  fieldLabels = {},
  missingFields = [],
  onDataChange,
}) {
  const [isEditMode, setIsEditMode] = useState(false);
  const [editedData, setEditedData] = useState({});

  // Initialize editedData when data changes
  useEffect(() => {
    setEditedData(data || {});
  }, [data]);

  // Check if we have minimum required data
  const hasRFC = editedData.rfc && editedData.rfc.trim();
  const hasName = (editedData.razon_social && editedData.razon_social.trim()) ||
                  (editedData.nombre && editedData.nombre.trim());
  const canConfirm = hasRFC || hasName;

  const displayFields = Object.entries(editedData || {}).filter(
    ([key]) => !key.startsWith('_') && !['dataConfirmed', 'entityType', 'fuentes'].includes(key)
  );

  const getFieldLabel = (key) => {
    return fieldLabels[key] || key.replace(/([A-Z])/g, ' $1').replace(/_/g, ' ').replace(/^./, (s) => s.toUpperCase());
  };

  const formatValue = (value) => {
    if (value === null || value === undefined) return '—';
    if (typeof value === 'boolean') return value ? 'Sí' : 'No';
    if (Array.isArray(value)) return value.join(', ');
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  const handleFieldChange = (key, value) => {
    const newData = { ...editedData, [key]: value };
    setEditedData(newData);
    if (onDataChange) {
      onDataChange(newData);
    }
  };

  const handleConfirm = () => {
    if (onConfirm) {
      onConfirm(editedData);
    }
  };

  const isCriticalField = (key) => CRITICAL_FIELDS.includes(key);
  const isMissingField = (key) => missingFields.includes(key);

  // Fields to show in edit mode (prioritize critical fields)
  const editableFields = [
    { key: 'rfc', label: 'RFC', placeholder: 'Ej: ABC123456XYZ', required: true },
    { key: 'razon_social', label: 'Razón Social', placeholder: 'Nombre legal de la empresa', required: true },
    { key: 'nombre', label: 'Nombre Comercial', placeholder: 'Nombre comercial (opcional)' },
    { key: 'regimen_fiscal', label: 'Régimen Fiscal', placeholder: 'Ej: 601 - General de Ley' },
    { key: 'direccion', label: 'Dirección', placeholder: 'Dirección fiscal' },
    { key: 'codigo_postal', label: 'Código Postal', placeholder: '00000' },
    { key: 'ciudad', label: 'Ciudad', placeholder: 'Ciudad' },
    { key: 'estado', label: 'Estado', placeholder: 'Estado' },
    { key: 'telefono', label: 'Teléfono', placeholder: '(00) 0000-0000' },
    { key: 'email', label: 'Email', placeholder: 'contacto@empresa.com' },
  ];

  return (
    <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/20 overflow-hidden">
      <div className="px-6 py-4 bg-white/5 border-b border-white/10">
        <h3 className="text-lg font-semibold text-gray-100">{title}</h3>
        <p className="text-sm text-gray-400 mt-1">
          {isEditMode
            ? 'Completa o corrige la información necesaria'
            : 'Revisa que la información sea correcta antes de continuar'}
        </p>
        {!canConfirm && !isEditMode && (
          <p className="text-sm text-yellow-400 mt-2 flex items-center gap-2">
            <span>⚠️</span>
            Se requiere al menos el RFC o el nombre de la empresa. Haz clic en "Editar datos" para completar.
          </p>
        )}
      </div>

      <div className="p-6">
        {isEditMode ? (
          // Edit mode - show form
          <div className="space-y-4">
            {editableFields.map(({ key, label, placeholder, required }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  {label}
                  {required && <span className="text-red-400 ml-1">*</span>}
                  {isMissingField(key) && (
                    <span className="text-yellow-400 text-xs ml-2">(faltante)</span>
                  )}
                </label>
                <input
                  type={key === 'email' ? 'email' : 'text'}
                  value={editedData[key] || ''}
                  onChange={(e) => handleFieldChange(key, e.target.value)}
                  placeholder={placeholder}
                  className={`w-full px-3 py-2 bg-white/10 border rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    isMissingField(key) ? 'border-yellow-500/50' : 'border-white/20'
                  }`}
                />
              </div>
            ))}
          </div>
        ) : (
          // View mode - show data
          <dl className="space-y-4">
            {displayFields.map(([key, value]) => (
              <div key={key} className="flex flex-col sm:flex-row sm:gap-4">
                <dt className={`text-sm font-medium sm:w-1/3 ${
                  isCriticalField(key) && !value ? 'text-yellow-400' : 'text-gray-400'
                }`}>
                  {getFieldLabel(key)}
                  {isCriticalField(key) && !value && <span className="text-yellow-400 ml-1">⚠️</span>}
                </dt>
                <dd className="text-sm text-gray-200 sm:w-2/3 mt-1 sm:mt-0">
                  {formatValue(value)}
                </dd>
              </div>
            ))}
          </dl>
        )}

        {displayFields.length === 0 && !isEditMode && (
          <p className="text-sm text-gray-500 text-center py-4">
            No hay datos para mostrar. Haz clic en "Editar datos" para agregar información.
          </p>
        )}
      </div>

      <div className="px-6 py-4 bg-white/5 border-t border-white/10 flex flex-col sm:flex-row gap-3 sm:justify-end">
        {onCancel && (
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 text-gray-300 bg-white/10 border border-white/20 rounded-lg hover:bg-white/20 transition-colors disabled:opacity-50"
          >
            Cancelar
          </button>
        )}

        {isEditMode ? (
          <button
            onClick={() => setIsEditMode(false)}
            disabled={isLoading}
            className="px-4 py-2 text-blue-300 bg-blue-500/20 border border-blue-500/30 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50"
          >
            Ver resumen
          </button>
        ) : (
          <button
            onClick={() => setIsEditMode(true)}
            disabled={isLoading}
            className="px-4 py-2 text-blue-300 bg-blue-500/20 border border-blue-500/30 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50"
          >
            Editar datos
          </button>
        )}

        {onConfirm && (
          <button
            onClick={handleConfirm}
            disabled={isLoading || !canConfirm}
            title={!canConfirm ? 'Se requiere RFC o nombre de empresa' : ''}
            className={`px-4 py-2 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2 ${
              canConfirm ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-600 cursor-not-allowed'
            }`}
          >
            {isLoading && (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            )}
            Confirmar y continuar
          </button>
        )}
      </div>
    </div>
  );
}

export default ConfirmationCard;
