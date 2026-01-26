import React from 'react';

const TemplateCard = ({ template, agentId, agentName, onCustomize, onDownload }) => {
  const placeholderCount = template.placeholders?.length || 0;
  
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 hover:shadow-md transition-all duration-200 hover:border-blue-300">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-slate-800 text-sm leading-tight">
            {template.title || template.template_id}
          </h3>
          <p className="text-xs text-slate-500 mt-1">{agentName}</p>
        </div>
        <span className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full font-medium">
          {template.file_size_kb} KB
        </span>
      </div>
      
      {placeholderCount > 0 && (
        <div className="mb-4">
          <p className="text-xs text-slate-600 mb-2">
            <span className="font-medium">{placeholderCount}</span> campos personalizables
          </p>
          <div className="flex flex-wrap gap-1">
            {template.placeholders?.slice(0, 4).map((placeholder, idx) => (
              <span 
                key={idx}
                className="bg-slate-100 text-slate-600 text-xs px-2 py-0.5 rounded"
              >
                {placeholder}
              </span>
            ))}
            {placeholderCount > 4 && (
              <span className="text-slate-400 text-xs">+{placeholderCount - 4} más</span>
            )}
          </div>
        </div>
      )}
      
      <div className="flex gap-2 mt-4">
        <button
          onClick={() => onDownload(agentId, template.template_id, template.filename)}
          className="flex-1 px-3 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors flex items-center justify-center gap-1"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Original
        </button>
        {placeholderCount > 0 && (
          <button
            onClick={() => onCustomize(template, agentId, agentName)}
            className="flex-1 px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors flex items-center justify-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Personalizar
          </button>
        )}
      </div>
    </div>
  );
};

export default TemplateCard;
