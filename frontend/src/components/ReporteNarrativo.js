import React, { useState } from 'react';

const ReporteNarrativo = ({ reporte, tipo = 'markdown' }) => {
  const [vistaActiva, setVistaActiva] = useState(tipo);
  
  if (!reporte) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg text-gray-500">
        No hay reporte disponible
      </div>
    );
  }
  
  const { reporte_markdown, reporte_html, metadata } = reporte;
  const persona = metadata || {};
  
  const renderMarkdown = (text) => {
    if (!text) return null;
    
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      if (line.startsWith('# ')) {
        return <h1 key={idx} className="text-2xl font-bold text-gray-900 mb-4">{line.slice(2)}</h1>;
      }
      if (line.startsWith('## ')) {
        return <h2 key={idx} className="text-xl font-semibold text-gray-800 mt-6 mb-3">{line.slice(3)}</h2>;
      }
      if (line.startsWith('### ')) {
        return <h3 key={idx} className="text-lg font-medium text-gray-700 mt-4 mb-2">{line.slice(4)}</h3>;
      }
      if (line.startsWith('- ')) {
        return <li key={idx} className="ml-4 text-gray-700">{line.slice(2)}</li>;
      }
      if (line.startsWith('**') && line.endsWith('**')) {
        return <p key={idx} className="font-bold text-gray-800">{line.slice(2, -2)}</p>;
      }
      if (line.includes('**')) {
        const parts = line.split(/\*\*(.*?)\*\*/g);
        return (
          <p key={idx} className="text-gray-700">
            {parts.map((part, i) => 
              i % 2 === 1 ? <strong key={i}>{part}</strong> : part
            )}
          </p>
        );
      }
      if (line === '---') {
        return <hr key={idx} className="my-4 border-gray-300" />;
      }
      if (line.trim() === '') {
        return <div key={idx} className="h-2" />;
      }
      return <p key={idx} className="text-gray-700 leading-relaxed">{line}</p>;
    });
  };
  
  return (
    <div className="reporte-narrativo bg-white rounded-lg shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-blue-800 to-blue-600 text-white p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">{persona?.persona || 'Analista'}</h3>
            <p className="text-blue-200 text-sm">{persona?.titulo || 'Especialista'}</p>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={() => setVistaActiva('markdown')}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                vistaActiva === 'markdown' 
                  ? 'bg-white text-blue-800' 
                  : 'bg-blue-700 text-white hover:bg-blue-600'
              }`}
            >
              📄 Texto
            </button>
            <button
              onClick={() => setVistaActiva('html')}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                vistaActiva === 'html' 
                  ? 'bg-white text-blue-800' 
                  : 'bg-blue-700 text-white hover:bg-blue-600'
              }`}
            >
              🎨 Formateado
            </button>
          </div>
        </div>
      </div>
      
      <div className="p-6 max-h-[600px] overflow-y-auto">
        {vistaActiva === 'markdown' ? (
          <div className="prose prose-blue max-w-none">
            {renderMarkdown(reporte_markdown)}
          </div>
        ) : (
          <div 
            className="reporte-html prose max-w-none"
            dangerouslySetInnerHTML={{ __html: reporte_html }}
          />
        )}
      </div>
      
      <div className="border-t bg-gray-50 p-4 flex justify-between items-center">
        <span className="text-sm text-gray-500">
          {persona?.generado ? `Generado: ${new Date(persona.generado).toLocaleString('es-MX')}` : 'Generado por Revisar.IA'}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => {
              navigator.clipboard.writeText(reporte_markdown || '');
              alert('Reporte copiado al portapapeles');
            }}
            className="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded transition-colors"
          >
            📋 Copiar
          </button>
          <button
            onClick={() => {
              const blob = new Blob([reporte_markdown || ''], { type: 'text/markdown' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `reporte_${persona?.agente || 'sistema'}.md`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            className="px-3 py-1 text-sm bg-blue-600 text-white hover:bg-blue-700 rounded transition-colors"
          >
            ⬇️ Descargar
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReporteNarrativo;
