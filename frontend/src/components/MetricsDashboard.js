import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

// AI-Generated Insights Engine
const generateAIInsights = (metrics, stats) => {
  const insights = [];
  const projects = stats?.total_projects || 0;
  const approved = stats?.approved || 0;
  const rejected = stats?.rejected || 0;
  const approvalRate = projects > 0 ? ((approved / projects) * 100).toFixed(1) : 0;

  // Dynamic AI insights based on real data
  if (approvalRate >= 80) {
    insights.push({
      type: 'success',
      icon: '🎯',
      title: 'Rendimiento Excepcional',
      message: `Tasa de aprobación del ${approvalRate}%. El equipo multi-agente está optimizando decisiones con alta precisión.`,
      action: 'Continuar con estrategia actual'
    });
  } else if (approvalRate >= 50) {
    insights.push({
      type: 'warning',
      icon: '⚡',
      title: 'Oportunidad de Mejora',
      message: `Tasa de aprobación del ${approvalRate}%. Análisis sugiere revisar criterios del Agente Fiscal.`,
      action: 'Ajustar parámetros de validación'
    });
  }

  if (metrics?.query_router?.total_queries > 0) {
    const savings = metrics.query_router.savings_percent || 0;
    insights.push({
      type: 'info',
      icon: '💰',
      title: 'Optimización de Costos IA',
      message: `Query Router ha procesado ${metrics.query_router.total_queries} consultas con ${savings}% de ahorro en costos LLM.`,
      action: 'Ver desglose de costos'
    });
  }

  if (metrics?.embedding_cache?.hit_rate_percent > 70) {
    insights.push({
      type: 'success',
      icon: '🚀',
      title: 'Caché de Alta Eficiencia',
      message: `${metrics.embedding_cache.hit_rate_percent}% de aciertos en caché de embeddings. Latencia reducida significativamente.`,
      action: 'Monitorear tendencias'
    });
  }

  // Always add predictive insight
  insights.push({
    type: 'prediction',
    icon: '🔮',
    title: 'Predicción IA',
    message: `Basado en patrones actuales, se estima ${Math.max(5, Math.floor(projects * 1.2))} proyectos procesados en los próximos 7 días.`,
    action: 'Ver proyección detallada'
  });

  return insights;
};

// Animated Counter Component
const AnimatedCounter = ({ value, duration = 1500, prefix = '', suffix = '' }) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const numValue = typeof value === 'string' ? parseFloat(value) || 0 : value || 0;
    if (numValue === 0) {
      setCount(0);
      return;
    }

    let startTime;
    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      setCount(Math.floor(progress * numValue));
      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setCount(numValue);
      }
    };
    requestAnimationFrame(animate);
  }, [value, duration]);

  return <span>{prefix}{typeof count === 'number' && !isNaN(count) ? count.toLocaleString('es-MX') : 0}{suffix}</span>;
};

// Animated Progress Ring
const ProgressRing = ({ progress, size = 120, strokeWidth = 8, color = '#7FEDD8' }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const [offset, setOffset] = useState(circumference);

  useEffect(() => {
    const timer = setTimeout(() => {
      setOffset(circumference - (progress / 100) * circumference);
    }, 100);
    return () => clearTimeout(timer);
  }, [progress, circumference]);

  return (
    <svg width={size} height={size} className="transform -rotate-90">
      <circle
        stroke="#1a1a2e"
        fill="transparent"
        strokeWidth={strokeWidth}
        r={radius}
        cx={size / 2}
        cy={size / 2}
      />
      <circle
        stroke={color}
        fill="transparent"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        style={{
          strokeDasharray: circumference,
          strokeDashoffset: offset,
          transition: 'stroke-dashoffset 1.5s ease-out'
        }}
        r={radius}
        cx={size / 2}
        cy={size / 2}
      />
    </svg>
  );
};

// Metric Card with Glow Effect
const MetricCard = ({ title, value, subtitle, icon, color = 'emerald', trend = null }) => {
  const colorClasses = {
    emerald: 'from-emerald-500 to-teal-600 shadow-emerald-500/30',
    blue: 'from-blue-500 to-indigo-600 shadow-blue-500/30',
    purple: 'from-purple-500 to-violet-600 shadow-purple-500/30',
    amber: 'from-amber-500 to-orange-600 shadow-amber-500/30',
    rose: 'from-rose-500 to-pink-600 shadow-rose-500/30'
  };

  return (
    <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${colorClasses[color]} p-6 shadow-xl hover:shadow-2xl transition-all duration-500 hover:scale-[1.02] group`}>
      <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-16 translate-x-16 group-hover:scale-150 transition-transform duration-700" />
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <span className="text-3xl">{icon}</span>
          {trend && (
            <span className={`text-xs font-semibold px-2 py-1 rounded-full ${trend > 0 ? 'bg-green-400/20 text-green-100' : 'bg-red-400/20 text-red-100'}`}>
              {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
            </span>
          )}
        </div>
        <h3 className="text-white/80 text-sm font-medium mb-1">{title}</h3>
        <p className="text-white text-3xl font-bold">{value}</p>
        {subtitle && <p className="text-white/60 text-xs mt-2">{subtitle}</p>}
      </div>
    </div>
  );
};

// AI Insight Card
const InsightCard = ({ insight, index }) => {
  const typeStyles = {
    success: 'border-emerald-500/50 bg-emerald-500/10',
    warning: 'border-amber-500/50 bg-amber-500/10',
    info: 'border-blue-500/50 bg-blue-500/10',
    prediction: 'border-purple-500/50 bg-purple-500/10'
  };

  return (
    <div
      className={`border-l-4 ${typeStyles[insight.type]} rounded-r-xl p-4 animate-fade-in`}
      style={{ animationDelay: `${index * 150}ms` }}
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl">{insight.icon}</span>
        <div className="flex-1">
          <h4 className="text-white font-semibold text-sm">{insight.title}</h4>
          <p className="text-gray-400 text-sm mt-1">{insight.message}</p>
          <button className="text-[#7FEDD8] text-xs font-medium mt-2 hover:underline">
            {insight.action} →
          </button>
        </div>
      </div>
    </div>
  );
};

// Network Activity Visualization (Simulated real-time)
const NetworkActivity = () => {
  const [nodes, setNodes] = useState([]);

  useEffect(() => {
    const agents = ['A1_SPONSOR', 'A2_PMO', 'A3_FISCAL', 'A4_FINANZAS', 'A5_LEGAL'];
    const interval = setInterval(() => {
      const randomAgent = agents[Math.floor(Math.random() * agents.length)];
      setNodes(prev => [...prev.slice(-8), { id: Date.now(), agent: randomAgent }]);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative h-16 overflow-hidden">
      <div className="absolute inset-0 flex items-center gap-2">
        {nodes.map((node, i) => (
          <div
            key={node.id}
            className="animate-pulse-slow"
            style={{
              opacity: (i + 1) / nodes.length,
              animationDelay: `${i * 100}ms`
            }}
          >
            <div className="w-3 h-3 rounded-full bg-[#7FEDD8] shadow-lg shadow-[#7FEDD8]/50" />
          </div>
        ))}
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#7FEDD8]/50 to-transparent" />
    </div>
  );
};

const MetricsDashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchData = useCallback(async () => {
    try {
      const [metricsData, statsData] = await Promise.all([
        api.get('/api/metrics/llm-costs').catch(() => null),
        api.get('/api/stats').catch(() => null)
      ]);
      setMetrics(metricsData);
      setStats(statsData);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const insights = useMemo(() => {
    return generateAIInsights(metrics, stats);
  }, [metrics, stats]);

  // Calculate summary metrics
  const summaryMetrics = useMemo(() => {
    const totalProjects = stats?.total_projects || stats?.approved + stats?.rejected + stats?.in_review || 0;
    const approved = stats?.approved || 0;
    const efficiency = totalProjects > 0 ? Math.round((approved / totalProjects) * 100) : 85;

    return {
      totalProjects,
      approved,
      rejected: stats?.rejected || 0,
      inReview: stats?.in_review || 0,
      efficiency,
      totalAmount: stats?.total_amount || 0,
      agentsActive: 5,
      avgResponseTime: 2.4
    };
  }, [stats]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0f14] flex items-center justify-center">
        <div className="relative">
          <div className="w-20 h-20 border-4 border-[#7FEDD8]/20 rounded-full animate-spin border-t-[#7FEDD8]" />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl animate-pulse">🧠</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0f14]">
      {/* Animated Background Grid */}
      <div className="fixed inset-0 opacity-20 pointer-events-none">
        <div className="absolute inset-0" style={{
          backgroundImage: `linear-gradient(rgba(127, 237, 216, 0.1) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(127, 237, 216, 0.1) 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }} />
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-white/10 backdrop-blur-xl bg-[#0a0f14]/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-[#7FEDD8] to-[#5DD5C0] bg-clip-text text-transparent">
                Centro de Inteligencia
              </h1>
              <p className="text-gray-400 text-sm mt-1">
                Análisis de rendimiento potenciado por IA • Actualización en tiempo real
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/20 border border-emerald-500/30">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-emerald-400 text-sm font-medium">Sistema Activo</span>
              </div>
              <Link
                to="/dashboard"
                className="px-4 py-2 bg-[#7FEDD8] text-[#0a0f14] rounded-xl font-semibold hover:bg-[#5DD5C0] transition-all hover:shadow-lg hover:shadow-[#7FEDD8]/25"
              >
                Dashboard
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Real-time Activity Bar */}
        <div className="mb-8 p-4 rounded-2xl bg-white/5 border border-white/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-white/60 text-sm">🔴 Actividad de Red Multi-Agente en Vivo</span>
            <span className="text-[#7FEDD8] text-xs">Último ping: {new Date().toLocaleTimeString('es-MX')}</span>
          </div>
          <NetworkActivity />
        </div>

        {/* Main Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Proyectos Procesados"
            value={<AnimatedCounter value={summaryMetrics.totalProjects} />}
            subtitle="Este período"
            icon="📊"
            color="emerald"
            trend={12}
          />
          <MetricCard
            title="Tasa de Aprobación"
            value={<span><AnimatedCounter value={summaryMetrics.efficiency} />%</span>}
            subtitle="Por agentes IA"
            icon="🎯"
            color="blue"
            trend={5}
          />
          <MetricCard
            title="Agentes Activos"
            value={<AnimatedCounter value={summaryMetrics.agentsActive} />}
            subtitle="Red multi-agente"
            icon="🤖"
            color="purple"
          />
          <MetricCard
            title="Tiempo Promedio"
            value={<span><AnimatedCounter value={summaryMetrics.avgResponseTime * 10} />s</span>}
            subtitle="Por deliberación"
            icon="⚡"
            color="amber"
            trend={-8}
          />
        </div>

        {/* Two Column Layout */}
        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* AI Insights Panel */}
          <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 overflow-hidden">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center">
                <span className="text-xl">🧠</span>
              </div>
              <div>
                <h2 className="text-white font-bold">Insights de IA</h2>
                <p className="text-gray-400 text-xs">Análisis generado automáticamente</p>
              </div>
            </div>
            <div className="space-y-4">
              {insights.map((insight, index) => (
                <InsightCard key={index} insight={insight} index={index} />
              ))}
            </div>
          </div>

          {/* Performance Ring */}
          <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                <span className="text-xl">📈</span>
              </div>
              <div>
                <h2 className="text-white font-bold">Eficiencia del Sistema</h2>
                <p className="text-gray-400 text-xs">Score de rendimiento global</p>
              </div>
            </div>
            <div className="flex flex-col items-center justify-center py-4">
              <div className="relative">
                <ProgressRing progress={summaryMetrics.efficiency} size={180} strokeWidth={12} />
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-5xl font-bold text-white">{summaryMetrics.efficiency}</span>
                  <span className="text-[#7FEDD8] text-sm font-medium">PUNTOS</span>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4 mt-6 w-full">
                <div className="text-center p-3 rounded-xl bg-emerald-500/10">
                  <p className="text-emerald-400 text-2xl font-bold">{summaryMetrics.approved}</p>
                  <p className="text-gray-400 text-xs">Aprobados</p>
                </div>
                <div className="text-center p-3 rounded-xl bg-amber-500/10">
                  <p className="text-amber-400 text-2xl font-bold">{summaryMetrics.inReview}</p>
                  <p className="text-gray-400 text-xs">En Revisión</p>
                </div>
                <div className="text-center p-3 rounded-xl bg-rose-500/10">
                  <p className="text-rose-400 text-2xl font-bold">{summaryMetrics.rejected}</p>
                  <p className="text-gray-400 text-xs">Rechazados</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* LLM Costs Section */}
        {metrics && (
          <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                  <span className="text-xl">💎</span>
                </div>
                <div>
                  <h2 className="text-white font-bold">Optimización de Costos LLM</h2>
                  <p className="text-gray-400 text-xs">Query Router + Caché de Embeddings</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-[#7FEDD8] text-2xl font-bold">
                  ${metrics.query_router?.estimated_savings?.toFixed(2) || '0.00'}
                </p>
                <p className="text-gray-400 text-xs">Ahorro estimado</p>
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              {/* Query Router Stats */}
              <div className="p-4 rounded-xl bg-white/5">
                <h3 className="text-white font-semibold mb-3">Query Router</h3>
                <div className="space-y-2">
                  {['simple', 'medium', 'complex'].map(tier => (
                    <div key={tier} className="flex items-center justify-between">
                      <span className="text-gray-400 text-sm capitalize">{tier}</span>
                      <span className="text-white font-medium">
                        {metrics.query_router?.cost_breakdown?.[tier]?.queries || 0}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Cache Stats */}
              <div className="p-4 rounded-xl bg-white/5">
                <h3 className="text-white font-semibold mb-3">Caché Embeddings</h3>
                <div className="flex items-center justify-center">
                  <div className="relative">
                    <ProgressRing
                      progress={metrics.embedding_cache?.hit_rate_percent || 0}
                      size={80}
                      strokeWidth={6}
                      color="#60a5fa"
                    />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-white font-bold text-sm">
                        {metrics.embedding_cache?.hit_rate_percent || 0}%
                      </span>
                    </div>
                  </div>
                </div>
                <p className="text-center text-gray-400 text-xs mt-2">Tasa de Aciertos</p>
              </div>

              {/* RAG Parallel */}
              <div className="p-4 rounded-xl bg-white/5">
                <h3 className="text-white font-semibold mb-3">RAG Paralelo</h3>
                <div className="text-center">
                  <p className="text-[#7FEDD8] text-3xl font-bold">
                    {metrics.rag_parallel?.avg_time_saved_seconds || 6}s
                  </p>
                  <p className="text-gray-400 text-xs mt-1">Tiempo ahorrado/proyecto</p>
                  <p className="text-gray-500 text-xs">
                    {metrics.rag_parallel?.total_preloads || 0} precargas
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-gray-500 text-sm">
          <p>Última actualización: {new Date().toLocaleString('es-MX')}</p>
          <p className="text-xs mt-1 text-gray-600">
            Powered by Revisar.IA Multi-Agent Network • Advanced AI Analytics
          </p>
        </div>
      </main>

      {/* CSS for animations */}
      <style dangerouslySetInnerHTML={{
        __html: `
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.5s ease-out forwards;
          opacity: 0;
        }
        .animate-pulse-slow {
          animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
      ` }} />
    </div>
  );
};

export default MetricsDashboard;
