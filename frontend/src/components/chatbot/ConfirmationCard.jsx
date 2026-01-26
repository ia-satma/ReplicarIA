export function ConfirmationCard({
  title = 'Confirmar datos',
  data,
  onConfirm,
  onEdit,
  onCancel,
  isLoading = false,
  fieldLabels = {},
}) {
  const displayFields = Object.entries(data || {}).filter(
    ([key]) => !key.startsWith('_') && !['dataConfirmed', 'entityType'].includes(key)
  );

  const getFieldLabel = (key) => {
    return fieldLabels[key] || key.replace(/([A-Z])/g, ' $1').replace(/^./, (s) => s.toUpperCase());
  };

  const formatValue = (value) => {
    if (value === null || value === undefined) return '—';
    if (typeof value === 'boolean') return value ? 'Sí' : 'No';
    if (Array.isArray(value)) return value.join(', ');
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  return (
    <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/20 overflow-hidden">
      <div className="px-6 py-4 bg-white/5 border-b border-white/10">
        <h3 className="text-lg font-semibold text-gray-100">{title}</h3>
        <p className="text-sm text-gray-400 mt-1">
          Revisa que la información sea correcta antes de continuar
        </p>
      </div>

      <div className="p-6">
        <dl className="space-y-4">
          {displayFields.map(([key, value]) => (
            <div key={key} className="flex flex-col sm:flex-row sm:gap-4">
              <dt className="text-sm font-medium text-gray-400 sm:w-1/3">
                {getFieldLabel(key)}
              </dt>
              <dd className="text-sm text-gray-200 sm:w-2/3 mt-1 sm:mt-0">
                {formatValue(value)}
              </dd>
            </div>
          ))}
        </dl>

        {displayFields.length === 0 && (
          <p className="text-sm text-gray-500 text-center py-4">
            No hay datos para mostrar
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
        
        {onEdit && (
          <button
            onClick={onEdit}
            disabled={isLoading}
            className="px-4 py-2 text-blue-300 bg-blue-500/20 border border-blue-500/30 rounded-lg hover:bg-blue-500/30 transition-colors disabled:opacity-50"
          >
            Editar datos
          </button>
        )}
        
        {onConfirm && (
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
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
