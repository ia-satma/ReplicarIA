import React, { useState, useEffect, useRef } from 'react';

export default function DisenarIA() {
  const [auditoria, setAuditoria] = useState(null);
  const [sugerencias, setSugerencias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const chatEndRef = useRef(null);

  useEffect(() => {
    cargarDatos();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const cargarDatos = async () => {
    setLoading(true);
    try {
      const [audRes, sugRes] = await Promise.all([
        fetch('/api/disenar/auditoria'),
        fetch('/api/disenar/sugerencias')
      ]);

      const audData = await audRes.json();
      if (audData.success) setAuditoria(audData);

      const sugData = await sugRes.json();
      if (sugData.success) setSugerencias(sugData.sugerencias);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const enviarMensaje = async () => {
    if (!chatMessage.trim() || chatLoading) return;

    const userMsg = chatMessage;
    setChatMessage('');
    setChatHistory(prev => [...prev, { role: 'user', content: userMsg }]);
    setChatLoading(true);

    try {
      const res = await fetch('/api/disenar/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg, history: chatHistory })
      });
      const data = await res.json();

      if (data.success) {
        setChatHistory(prev => [...prev, { role: 'assistant', content: data.response }]);
      } else {
        setChatHistory(prev => [...prev, { role: 'assistant', content: `Error: ${data.detail || 'No se pudo obtener respuesta'}` }]);
      }
    } catch (error) {
      console.error('Error:', error);
      setChatHistory(prev => [...prev, { role: 'assistant', content: 'Error de conexión con el servidor' }]);
    } finally {
      setChatLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-emerald-400';
    if (score >= 70) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getScoreBg = (score) => {
    if (score >= 90) return 'bg-emerald-500';
    if (score >= 70) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-slate-400 text-lg">Diseñar.IA está analizando el diseño...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-gradient-to-r from-purple-900/50 to-pink-900/50 rounded-2xl p-6 mb-6 border border-purple-500/30 backdrop-blur-sm">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center text-3xl shadow-lg shadow-purple-500/20">
                🎨
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Diseñar.IA</h1>
                <p className="text-purple-200/80">Guardián del Diseño y la Experiencia de Usuario</p>
              </div>
            </div>
            <button
              onClick={cargarDatos}
              className="px-5 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl flex items-center gap-2 transition-all shadow-lg shadow-purple-600/20"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Auditar Ahora
            </button>
          </div>

          {auditoria && (
            <div className="mt-6 flex items-center gap-6">
              <div className={`text-5xl font-bold ${getScoreColor(auditoria.score_general)}`}>
                {auditoria.score_general}%
              </div>
              <div>
                <div className="text-lg text-white font-semibold">{auditoria.mensaje}</div>
                <div className="text-sm text-slate-400">
                  Última auditoría: {new Date(auditoria.timestamp).toLocaleString('es-MX')}
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  Tiempo: {auditoria.tiempo_auditoria_ms?.toFixed(0)}ms
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {[
            { id: 'dashboard', icon: '📊', label: 'Dashboard' },
            { id: 'chat', icon: '💬', label: 'Chat' },
            { id: 'sugerencias', icon: '💡', label: 'Nuevas Tecnologías' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 rounded-xl font-medium transition-all whitespace-nowrap flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/20'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === 'dashboard' && auditoria && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <AuditoriaCard
              titulo="🎨 Colorimetría"
              score={auditoria.colorimetria?.score || 0}
              detalles={[
                `${auditoria.colorimetria?.total_colores || 0} colores detectados`,
                `${auditoria.colorimetria?.colores_prohibidos?.length || 0} fuera de paleta`
              ]}
              problemas={auditoria.colorimetria?.colores_prohibidos?.slice(0, 3)}
            />

            <AuditoriaCard
              titulo="🔤 Tipografías"
              score={auditoria.tipografia?.score || 0}
              detalles={[
                `Fuentes oficiales: ${auditoria.tipografia?.fuentes_oficiales?.join(', ')}`,
                `${auditoria.tipografia?.fuentes_no_oficiales?.length || 0} fuentes no oficiales`
              ]}
            />

            <AuditoriaCard
              titulo="📱 Responsive / Móvil"
              score={auditoria.responsive?.score || 0}
              detalles={[
                `${auditoria.responsive?.componentes_analizados || 0} componentes`,
                `${auditoria.responsive?.total_problemas || 0} problemas detectados`
              ]}
              problemas={auditoria.responsive?.problemas?.slice(0, 3)}
            />

            <AuditoriaCard
              titulo="🧩 Componentes UI"
              score={auditoria.componentes?.score || 0}
              detalles={[
                `${auditoria.componentes?.total_componentes || 0} componentes analizados`
              ]}
            />

            <AuditoriaCard
              titulo="♿ Accesibilidad"
              score={auditoria.accesibilidad?.score || 0}
              detalles={[
                `${auditoria.accesibilidad?.total_problemas || 0} problemas a11y`
              ]}
              problemas={auditoria.accesibilidad?.problemas?.slice(0, 3)}
            />

            <AuditoriaCard
              titulo="⚡ Rendimiento CSS"
              score={auditoria.rendimiento?.score || 0}
              detalles={[
                `${auditoria.rendimiento?.total_problemas || 0} optimizaciones sugeridas`
              ]}
              problemas={auditoria.rendimiento?.problemas?.slice(0, 3)}
            />
          </div>
        )}

        {activeTab === 'chat' && (
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl overflow-hidden border border-slate-700">
            <div className="h-[28rem] overflow-y-auto p-4 space-y-4">
              {chatHistory.length === 0 && (
                <div className="text-center text-slate-500 py-12">
                  <div className="text-5xl mb-4">🎨</div>
                  <p className="text-lg mb-4">Hola, soy Diseñar.IA</p>
                  <p className="text-sm mb-4">Pregúntame sobre diseño, colores, responsive o UX</p>
                  <div className="flex flex-wrap justify-center gap-2">
                    {[
                      '¿Cómo puedo mejorar el responsive?',
                      '¿Qué colores debo usar?',
                      '¿Cómo implemento animaciones?'
                    ].map((sugerencia, idx) => (
                      <button
                        key={idx}
                        onClick={() => setChatMessage(sugerencia)}
                        className="text-purple-400 hover:text-purple-300 text-sm px-3 py-1.5 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition-all"
                      >
                        {sugerencia}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {chatHistory.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] p-4 rounded-2xl ${
                      msg.role === 'user'
                        ? 'bg-purple-600 text-white'
                        : 'bg-slate-700/70 text-slate-100'
                    }`}
                  >
                    {msg.role === 'assistant' && (
                      <div className="text-xs text-purple-400 mb-2 flex items-center gap-1">
                        <span>🎨</span> Diseñar.IA
                      </div>
                    )}
                    <div className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</div>
                  </div>
                </div>
              ))}

              {chatLoading && (
                <div className="flex justify-start">
                  <div className="bg-slate-700/70 p-4 rounded-2xl">
                    <div className="flex items-center gap-3">
                      <div className="animate-spin w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full" />
                      <span className="text-slate-400">Diseñar.IA está pensando...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <div className="p-4 border-t border-slate-700 bg-slate-800/80">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && enviarMensaje()}
                  placeholder="Pregunta sobre diseño, colores, responsive..."
                  className="flex-1 px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition-all"
                />
                <button
                  onClick={enviarMensaje}
                  disabled={chatLoading || !chatMessage.trim()}
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-600/20 flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                  Enviar
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'sugerencias' && (
          <div className="space-y-4">
            {sugerencias.map((sug, idx) => (
              <div key={idx} className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700 hover:border-purple-500/30 transition-all">
                <div className="flex flex-col md:flex-row items-start justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-white flex items-center gap-3 flex-wrap">
                      <span className="text-2xl">💡</span>
                      {sug.tecnologia}
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                        sug.dificultad === 'baja' ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30' :
                        sug.dificultad === 'media' ? 'bg-yellow-600/20 text-yellow-400 border border-yellow-500/30' : 
                        'bg-red-600/20 text-red-400 border border-red-500/30'
                      }`}>
                        {sug.dificultad}
                      </span>
                    </h3>
                    <p className="text-slate-400 mt-2">{sug.descripcion}</p>
                    <p className="text-purple-400 mt-2 flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                      Impacto: {sug.impacto}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-all text-sm">
                      Ver Demo
                    </button>
                    <button className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-all text-sm shadow-lg shadow-purple-600/20">
                      Implementar
                    </button>
                  </div>
                </div>

                {sug.ejemplo && (
                  <div className="mt-4">
                    <div className="text-xs text-slate-500 mb-2">Ejemplo de código:</div>
                    <pre className="bg-slate-900/80 p-4 rounded-xl text-sm text-slate-300 overflow-x-auto border border-slate-700">
                      <code>{sug.ejemplo}</code>
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AuditoriaCard({ titulo, score, detalles, problemas }) {
  const getScoreColor = (s) => s >= 90 ? 'text-emerald-400' : s >= 70 ? 'text-yellow-400' : 'text-red-400';
  const getScoreBg = (s) => s >= 90 ? 'bg-emerald-500' : s >= 70 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-5 border border-slate-700 hover:border-purple-500/30 transition-all">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">{titulo}</h3>
        <span className={`text-2xl font-bold ${getScoreColor(score)}`}>{score}%</span>
      </div>

      <div className="h-2 bg-slate-700 rounded-full overflow-hidden mb-4">
        <div 
          className={`h-full ${getScoreBg(score)} transition-all duration-500`} 
          style={{ width: `${score}%` }} 
        />
      </div>

      <div className="space-y-1.5 text-sm text-slate-400">
        {detalles.map((d, i) => (
          <div key={i} className="flex items-start gap-2">
            <span className="text-slate-500">•</span>
            <span>{d}</span>
          </div>
        ))}
      </div>

      {problemas && problemas.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <div className="text-xs text-red-400 mb-2 font-medium">Problemas detectados:</div>
          {problemas.map((p, i) => (
            <div key={i} className="text-xs text-slate-500 mb-1 flex items-start gap-1">
              <span className="text-red-400">•</span>
              <span>
                {p.color || p.archivo || p.problema}
                {p.sugerencia && <span className="text-cyan-400 ml-1">→ {p.sugerencia}</span>}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
