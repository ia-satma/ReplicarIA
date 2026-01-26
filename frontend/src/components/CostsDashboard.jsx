import React, { useState, useEffect } from 'react';

const BarChartIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="12" width="4" height="9" rx="1" />
    <rect x="10" y="8" width="4" height="13" rx="1" />
    <rect x="17" y="4" width="4" height="17" rx="1" />
  </svg>
);

const CostsDashboard = () => {
  const [activityFeed] = useState([
    { id: 1, type: 'simple', model: 'GPT-4o-mini', tokens: 847, cost: 0.0012, time: 'hace 2s' },
    { id: 2, type: 'medium', model: 'GPT-4o', tokens: 2341, cost: 0.0089, time: 'hace 5s' },
    { id: 3, type: 'complex', model: 'GPT-4-Turbo', tokens: 4521, cost: 0.0452, time: 'hace 12s' },
    { id: 4, type: 'simple', model: 'GPT-4o-mini', tokens: 612, cost: 0.0008, time: 'hace 18s' },
    { id: 5, type: 'medium', model: 'GPT-4o', tokens: 1893, cost: 0.0071, time: 'hace 25s' },
  ]);

  const stats = {
    totalQueries: 1523,
    savings: 27.42,
    totalCost: 7.58,
    efficiency: 98.2,
    savingsPercent: 78
  };

  const tiers = [
    { name: 'SIMPLE', displayName: 'Simple', count: 890, color: '#4ade80' },
    { name: 'MEDIUM', displayName: 'Medio', count: 520, color: '#60a5fa' },
    { name: 'COMPLEX', displayName: 'Complejo', count: 113, color: '#a78bfa' }
  ];

  const maxTier = Math.max(...tiers.map(t => t.count));

  const styles = {
    container: {
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 50%, #16213e 100%)',
      padding: '24px',
      fontFamily: "'Inter', 'Segoe UI', -apple-system, sans-serif",
      color: '#ffffff'
    },
    content: {
      maxWidth: '1400px',
      margin: '0 auto'
    },
    header: {
      textAlign: 'center',
      marginBottom: '32px',
      paddingBottom: '24px',
      borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
    },
    titleContainer: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '12px',
      marginBottom: '8px'
    },
    titleIcon: {
      color: '#60a5fa'
    },
    title: {
      fontSize: '32px',
      fontWeight: 700,
      color: '#ffffff',
      letterSpacing: '1px',
      margin: 0
    },
    subtitle: {
      color: 'rgba(255, 255, 255, 0.6)',
      fontSize: '14px',
      letterSpacing: '2px',
      textTransform: 'uppercase',
      margin: 0
    },
    statusIndicator: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: '8px',
      padding: '8px 16px',
      background: 'rgba(74, 222, 128, 0.1)',
      borderRadius: '20px',
      border: '1px solid rgba(74, 222, 128, 0.3)',
      marginTop: '16px'
    },
    statusDot: {
      width: '8px',
      height: '8px',
      borderRadius: '50%',
      background: '#4ade80'
    },
    statusText: {
      fontSize: '12px',
      color: '#4ade80',
      textTransform: 'uppercase',
      letterSpacing: '1px'
    },
    statsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(4, 1fr)',
      gap: '20px',
      marginBottom: '24px'
    },
    statCard: {
      background: 'rgba(22, 33, 62, 0.8)',
      borderRadius: '12px',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      padding: '24px',
      textAlign: 'center',
      transition: 'all 0.2s ease'
    },
    statValue: (color) => ({
      fontSize: '32px',
      fontWeight: 700,
      color: color,
      marginBottom: '4px'
    }),
    statLabel: {
      fontSize: '12px',
      color: 'rgba(255, 255, 255, 0.6)',
      textTransform: 'uppercase',
      letterSpacing: '1px'
    },
    mainGrid: {
      display: 'grid',
      gridTemplateColumns: '1fr 320px',
      gap: '24px'
    },
    card: {
      background: 'rgba(22, 33, 62, 0.8)',
      borderRadius: '12px',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      padding: '24px',
      marginBottom: '24px'
    },
    sectionTitle: {
      fontSize: '14px',
      color: '#60a5fa',
      textTransform: 'uppercase',
      letterSpacing: '2px',
      marginBottom: '20px',
      fontWeight: 600,
      display: 'flex',
      alignItems: 'center',
      gap: '8px'
    },
    titleDot: {
      width: '6px',
      height: '6px',
      background: '#60a5fa',
      borderRadius: '2px'
    },
    barChart: {
      display: 'flex',
      flexDirection: 'column',
      gap: '16px'
    },
    barRow: {
      display: 'flex',
      alignItems: 'center',
      gap: '16px'
    },
    barLabel: {
      width: '80px',
      fontSize: '14px',
      color: '#ffffff',
      fontWeight: 500
    },
    barContainer: {
      flex: 1,
      height: '36px',
      background: 'rgba(15, 15, 15, 0.6)',
      borderRadius: '6px',
      overflow: 'hidden',
      position: 'relative'
    },
    bar: (width, color) => ({
      height: '100%',
      width: `${width}%`,
      background: color,
      borderRadius: '6px',
      position: 'relative',
      transition: 'width 0.8s ease-out'
    }),
    barValue: {
      position: 'absolute',
      right: '12px',
      top: '50%',
      transform: 'translateY(-50%)',
      color: '#ffffff',
      fontWeight: 600,
      fontSize: '14px'
    },
    costGrid: {
      marginTop: '24px',
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: '16px'
    },
    costItem: {
      textAlign: 'center',
      padding: '16px',
      background: 'rgba(15, 15, 15, 0.4)',
      borderRadius: '8px'
    },
    costLabel: (color) => ({
      color: color,
      fontSize: '11px',
      textTransform: 'uppercase',
      letterSpacing: '1px',
      marginBottom: '8px'
    }),
    costValue: {
      color: '#ffffff',
      fontSize: '18px',
      fontWeight: 600
    },
    activityFeed: {
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      maxHeight: '280px',
      overflowY: 'auto'
    },
    activityItem: (type) => {
      const colors = { simple: '#4ade80', medium: '#60a5fa', complex: '#a78bfa' };
      return {
        background: 'rgba(15, 15, 15, 0.4)',
        borderRadius: '8px',
        padding: '12px',
        borderLeft: `3px solid ${colors[type]}`,
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      };
    },
    activityDot: (type) => {
      const colors = { simple: '#4ade80', medium: '#60a5fa', complex: '#a78bfa' };
      return {
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        background: colors[type],
        flexShrink: 0
      };
    },
    activityDetails: {
      flex: 1
    },
    activityModel: {
      fontSize: '13px',
      color: '#ffffff',
      fontWeight: 500
    },
    activityMeta: {
      fontSize: '11px',
      color: 'rgba(255, 255, 255, 0.5)',
      marginTop: '2px'
    },
    activityCost: {
      fontSize: '13px',
      color: '#4ade80',
      fontWeight: 600
    },
    circularProgress: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px'
    },
    svgContainer: {
      position: 'relative',
      width: '160px',
      height: '160px'
    },
    progressText: {
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      textAlign: 'center'
    },
    progressValue: {
      fontSize: '36px',
      fontWeight: 700,
      color: '#4ade80'
    },
    progressLabel: {
      fontSize: '12px',
      color: 'rgba(255, 255, 255, 0.6)',
      textTransform: 'uppercase',
      letterSpacing: '1px'
    },
    modelAllocation: {
      display: 'flex',
      flexDirection: 'column',
      gap: '14px'
    },
    modelRow: {
      display: 'flex',
      justifyContent: 'space-between',
      marginBottom: '6px'
    },
    modelName: {
      color: '#ffffff',
      fontSize: '13px'
    },
    modelPercent: (color) => ({
      color: color,
      fontSize: '13px',
      fontWeight: 600
    }),
    modelBar: {
      height: '6px',
      background: 'rgba(15, 15, 15, 0.6)',
      borderRadius: '3px',
      overflow: 'hidden'
    },
    modelBarFill: (width, color) => ({
      height: '100%',
      width: `${width}%`,
      background: color,
      borderRadius: '3px',
      transition: 'width 0.8s ease-out'
    }),
    projectedCard: {
      background: 'rgba(22, 33, 62, 0.8)',
      borderRadius: '12px',
      border: '1px solid rgba(74, 222, 128, 0.2)',
      padding: '24px',
      textAlign: 'center'
    },
    projectedLabel: {
      fontSize: '12px',
      color: 'rgba(255, 255, 255, 0.6)',
      textTransform: 'uppercase',
      letterSpacing: '1px',
      marginBottom: '8px'
    },
    projectedValue: {
      fontSize: '28px',
      fontWeight: 700,
      color: '#4ade80'
    },
    projectedSaving: {
      fontSize: '12px',
      color: '#4ade80',
      marginTop: '8px'
    },
    footer: {
      marginTop: '24px',
      textAlign: 'center',
      color: 'rgba(255, 255, 255, 0.3)',
      fontSize: '11px',
      letterSpacing: '1px'
    }
  };

  const CircularProgressSVG = ({ percentage }) => {
    const radius = 60;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;
    
    return (
      <svg width="160" height="160" style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx="80"
          cy="80"
          r={radius}
          fill="none"
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth="10"
        />
        <circle
          cx="80"
          cy="80"
          r={radius}
          fill="none"
          stroke="#4ade80"
          strokeWidth="10"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease-out' }}
        />
      </svg>
    );
  };

  return (
    <div style={styles.container}>
      <div style={styles.content}>
        <div style={styles.header}>
          <div style={styles.titleContainer}>
            <span style={styles.titleIcon}><BarChartIcon /></span>
            <h1 style={styles.title}>Panel de Costos LLM</h1>
          </div>
          <p style={styles.subtitle}>Análisis de Procesamiento y Optimización</p>
          <div style={styles.statusIndicator}>
            <div style={styles.statusDot} />
            <span style={styles.statusText}>Sistema Activo</span>
          </div>
        </div>

        <div style={styles.statsGrid}>
          {[
            { label: 'Total de Consultas', value: stats.totalQueries.toLocaleString(), color: '#60a5fa' },
            { label: 'Ahorro en Costos', value: `$${stats.savings.toFixed(2)}`, color: '#4ade80' },
            { label: 'Gasto Total', value: `$${stats.totalCost.toFixed(2)}`, color: '#a78bfa' },
            { label: 'Eficiencia', value: `${stats.efficiency}%`, color: '#fbbf24' }
          ].map((stat, i) => (
            <div key={i} style={styles.statCard}>
              <div style={styles.statValue(stat.color)}>{stat.value}</div>
              <div style={styles.statLabel}>{stat.label}</div>
            </div>
          ))}
        </div>

        <div style={styles.mainGrid}>
          <div>
            <div style={styles.card}>
              <div style={styles.sectionTitle}>
                <div style={styles.titleDot} />
                Distribución de Consultas por Complejidad
              </div>
              <div style={styles.barChart}>
                {tiers.map((tier, i) => (
                  <div key={i} style={styles.barRow}>
                    <div style={styles.barLabel}>{tier.displayName}</div>
                    <div style={styles.barContainer}>
                      <div style={styles.bar((tier.count / maxTier) * 100, tier.color)}>
                        <span style={styles.barValue}>{tier.count}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div style={styles.costGrid}>
                {tiers.map((tier, i) => (
                  <div key={i} style={styles.costItem}>
                    <div style={styles.costLabel(tier.color)}>Costo {tier.displayName}</div>
                    <div style={styles.costValue}>
                      ${(tier.count * (i === 0 ? 0.001 : i === 1 ? 0.008 : 0.045)).toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div style={styles.card}>
              <div style={styles.sectionTitle}>
                <div style={{...styles.titleDot, background: '#4ade80'}} />
                Actividad Reciente
              </div>
              <div style={styles.activityFeed}>
                {activityFeed.map((item) => (
                  <div key={item.id} style={styles.activityItem(item.type)}>
                    <div style={styles.activityDot(item.type)} />
                    <div style={styles.activityDetails}>
                      <div style={styles.activityModel}>{item.model}</div>
                      <div style={styles.activityMeta}>
                        {item.tokens.toLocaleString()} tokens • {item.time}
                      </div>
                    </div>
                    <div style={styles.activityCost}>${item.cost.toFixed(4)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={styles.card}>
              <div style={styles.sectionTitle}>
                <div style={{...styles.titleDot, background: '#4ade80'}} />
                Eficiencia de Costos
              </div>
              <div style={styles.circularProgress}>
                <div style={styles.svgContainer}>
                  <CircularProgressSVG percentage={stats.savingsPercent} />
                  <div style={styles.progressText}>
                    <div style={styles.progressValue}>{stats.savingsPercent}%</div>
                    <div style={styles.progressLabel}>Ahorro</div>
                  </div>
                </div>
              </div>
              <div style={{ textAlign: 'center', marginTop: '8px' }}>
                <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px' }}>
                  vs. usar siempre GPT-4
                </div>
              </div>
            </div>

            <div style={styles.card}>
              <div style={styles.sectionTitle}>
                <div style={{...styles.titleDot, background: '#a78bfa'}} />
                Distribución de Modelos
              </div>
              <div style={styles.modelAllocation}>
                {[
                  { name: 'GPT-4o-mini', pct: 58, color: '#4ade80' },
                  { name: 'GPT-4o', pct: 34, color: '#60a5fa' },
                  { name: 'GPT-4-Turbo', pct: 8, color: '#a78bfa' }
                ].map((model, i) => (
                  <div key={i}>
                    <div style={styles.modelRow}>
                      <span style={styles.modelName}>{model.name}</span>
                      <span style={styles.modelPercent(model.color)}>{model.pct}%</span>
                    </div>
                    <div style={styles.modelBar}>
                      <div style={styles.modelBarFill(model.pct, model.color)} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div style={styles.projectedCard}>
              <div style={styles.projectedLabel}>Proyección Mensual</div>
              <div style={styles.projectedValue}>$152.40</div>
              <div style={styles.projectedSaving}>▼ 78% vs línea base</div>
            </div>
          </div>
        </div>

        <div style={styles.footer}>
          REVISAR.IA — PANEL DE OPTIMIZACIÓN DE COSTOS v2.1.0
        </div>
      </div>
    </div>
  );
};

export default CostsDashboard;
