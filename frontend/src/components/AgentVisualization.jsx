import React, { useState, useEffect, useRef, useCallback } from 'react';

const AGENTS = [
  {
    id: 'A1',
    name: 'Recepción',
    shortName: 'A1',
    description: 'Gestiona la recepción y clasificación inicial de documentos. Coordina la entrada de información y prepara los datos para el análisis.'
  },
  {
    id: 'A2',
    name: 'Análisis',
    shortName: 'A2',
    description: 'Realiza el análisis preliminar de la información recibida. Identifica patrones y clasifica la documentación.'
  },
  {
    id: 'A3',
    name: 'Compliance',
    shortName: 'A3',
    description: 'Verifica el cumplimiento normativo y regulatorio. Asegura que todos los procesos adhieren a los estándares requeridos.'
  },
  {
    id: 'A4',
    name: 'Contable',
    shortName: 'A4',
    description: 'Gestiona los aspectos contables y financieros. Registra y valida transacciones contables.'
  },
  {
    id: 'A5',
    name: 'Operativo',
    shortName: 'A5',
    description: 'Supervisa las operaciones diarias. Coordina la ejecución de procesos y garantiza la continuidad operativa.'
  },
  {
    id: 'A6',
    name: 'Financiero',
    shortName: 'A6',
    description: 'Analiza aspectos financieros y presupuestarios. Genera reportes y proyecciones financieras.'
  },
  {
    id: 'A7',
    name: 'Legal',
    shortName: 'A7',
    description: 'Revisa aspectos legales y contractuales. Asegura que los acuerdos cumplen con la normativa legal.'
  },
  {
    id: 'A8',
    name: 'Red Team',
    shortName: 'A8',
    description: 'Realiza validación adversarial. Identifica vulnerabilidades y riesgos potenciales en los procesos.'
  },
  {
    id: 'A9',
    name: 'Síntesis',
    shortName: 'A9',
    description: 'Integra los análisis de todos los agentes. Genera reportes consolidados y conclusiones finales.'
  },
  {
    id: 'A10',
    name: 'Archivo',
    shortName: 'A10',
    description: 'Gestiona el almacenamiento y organización de documentos. Mantiene la trazabilidad e histórico de procesos.'
  }
];

const AgentVisualization = () => {
  const canvasRef = useRef(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [animatingAgents, setAnimatingAgents] = useState(new Set());
  const [hoveredAgent, setHoveredAgent] = useState(null);
  const animationFrameRef = useRef(null);
  const [agentPositions, setAgentPositions] = useState({});

  // Calculate agent positions in circle
  const calculatePositions = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const radius = Math.min(rect.width, rect.height) * 0.35;

    const positions = {};
    AGENTS.forEach((agent, index) => {
      const angle = (index / AGENTS.length) * 2 * Math.PI - Math.PI / 2;
      positions[agent.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
        angle
      };
    });

    positions.orquestador = {
      x: centerX,
      y: centerY
    };

    setAgentPositions(positions);
  }, []);

  useEffect(() => {
    calculatePositions();
    window.addEventListener('resize', calculatePositions);
    return () => window.removeEventListener('resize', calculatePositions);
  }, [calculatePositions]);

  // Draw canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    // Clear canvas
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (Object.keys(agentPositions).length === 0) return;

    // Draw connection lines
    const drawLine = (from, to, color = '#e5e7eb', width = 1, isAnimated = false) => {
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      if (isAnimated) {
        ctx.setLineDash([5, 5]);
      }
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);
      ctx.stroke();
      ctx.setLineDash([]);
    };

    // Draw lines from each agent to orquestador
    const orqPos = agentPositions.orquestador;
    AGENTS.forEach((agent) => {
      const agentPos = agentPositions[agent.id];
      if (agentPos && orqPos) {
        const isAnimating = animatingAgents.has(agent.id);
        drawLine(
          agentPos,
          orqPos,
          isAnimating ? '#4f46e5' : '#e5e7eb',
          isAnimating ? 2 : 1,
          isAnimating
        );
      }
    });

    // Draw orquestador node (central)
    if (orqPos) {
      ctx.fillStyle = '#ffffff';
      ctx.strokeStyle = '#4f46e5';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(orqPos.x, orqPos.y, 25, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = '#4f46e5';
      ctx.font = 'bold 12px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('Orquestador', orqPos.x, orqPos.y);
    }

    // Draw agent nodes
    AGENTS.forEach((agent) => {
      const pos = agentPositions[agent.id];
      if (!pos) return;

      const isActive = selectedAgent?.id === agent.id;
      const isAnimating = animatingAgents.has(agent.id);
      const isHovered = hoveredAgent?.id === agent.id;

      // Draw outer ring for active/animated agents
      if (isActive || isAnimating) {
        ctx.strokeStyle = isAnimating ? '#4f46e5' : '#4f46e5';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, 28, 0, 2 * Math.PI);
        ctx.stroke();
      }

      // Draw main circle
      const radius = isActive || isAnimating ? 18 : 16;
      ctx.fillStyle = isActive || isAnimating ? '#4f46e5' : '#d1d5db';
      ctx.strokeStyle = isHovered ? '#4f46e5' : (isActive || isAnimating ? '#4f46e5' : '#9ca3af');
      ctx.lineWidth = isHovered ? 2 : 1.5;

      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();

      // Draw text
      ctx.fillStyle = isActive || isAnimating ? '#ffffff' : '#374151';
      ctx.font = 'bold 11px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(agent.shortName, pos.x, pos.y);
    });
  }, [agentPositions, selectedAgent, animatingAgents, hoveredAgent]);

  const handleCanvasClick = (e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Check if clicked on any agent
    for (const agent of AGENTS) {
      const pos = agentPositions[agent.id];
      if (!pos) continue;

      const distance = Math.sqrt((clickX - pos.x) ** 2 + (clickY - pos.y) ** 2);
      if (distance <= 25) {
        setSelectedAgent(agent);
        return;
      }
    }

    setSelectedAgent(null);
  };

  const handleCanvasMouseMove = (e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const moveX = e.clientX - rect.left;
    const moveY = e.clientY - rect.top;

    let hovered = null;
    for (const agent of AGENTS) {
      const pos = agentPositions[agent.id];
      if (!pos) continue;

      const distance = Math.sqrt((moveX - pos.x) ** 2 + (moveY - pos.y) ** 2);
      if (distance <= 25) {
        hovered = agent;
        break;
      }
    }

    setHoveredAgent(hovered);
    canvas.style.cursor = hovered ? 'pointer' : 'default';
  };

  const simulateAnalysis = () => {
    const agentIds = AGENTS.map((a) => a.id);
    let currentIndex = 0;
    const newAnimatingAgents = new Set();

    const animateNext = () => {
      if (currentIndex < agentIds.length) {
        newAnimatingAgents.add(agentIds[currentIndex]);
        setAnimatingAgents(new Set(newAnimatingAgents));

        setTimeout(() => {
          newAnimatingAgents.delete(agentIds[currentIndex]);
          setAnimatingAgents(new Set(newAnimatingAgents));
          currentIndex++;
          animateNext();
        }, 400);
      } else {
        setAnimatingAgents(new Set());
      }
    };

    animateNext();
  };

  return (
    <div className="w-full h-full bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl shadow-sm p-6 flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Visualización de Agentes</h2>
          <p className="text-sm text-gray-500 mt-1">Red de comunicación entre agentes IA</p>
        </div>
        <button
          onClick={simulateAnalysis}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors shadow-sm"
        >
          Simular Análisis
        </button>
      </div>

      {/* Main content */}
      <div className="flex-1 flex gap-6 min-h-0">
        {/* Canvas area */}
        <div className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden flex items-center justify-center">
          <canvas
            ref={canvasRef}
            onClick={handleCanvasClick}
            onMouseMove={handleCanvasMouseMove}
            onMouseLeave={() => setHoveredAgent(null)}
            className="w-full h-full cursor-pointer"
          />
        </div>

        {/* Details panel */}
        <div className="w-80 bg-white rounded-lg shadow-sm border border-gray-200 p-4 flex flex-col overflow-hidden">
          {selectedAgent ? (
            <>
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{selectedAgent.shortName}</h3>
                  <p className="text-sm font-medium text-indigo-600 mt-1">{selectedAgent.name}</p>
                </div>
                <button
                  onClick={() => setSelectedAgent(null)}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  ✕
                </button>
              </div>

              <div className="flex-1 overflow-y-auto">
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-semibold text-gray-500 uppercase">Descripción</label>
                    <p className="text-sm text-gray-700 mt-2 leading-relaxed">
                      {selectedAgent.description}
                    </p>
                  </div>

                  <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3">
                    <p className="text-xs font-medium text-indigo-900">
                      Estado: <span className="text-indigo-600 font-bold">Activo</span>
                    </p>
                  </div>

                  <div className="pt-4 border-t border-gray-200">
                    <label className="text-xs font-semibold text-gray-500 uppercase block mb-3">
                      Conexiones
                    </label>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      <div className="flex items-center gap-2 text-sm text-gray-700">
                        <div className="w-2 h-2 rounded-full bg-indigo-600"></div>
                        <span>Conectado con Orquestador</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <div className="w-2 h-2 rounded-full bg-gray-300"></div>
                        <span>Comunicación con otros agentes</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-3">
                <span className="text-xl">👆</span>
              </div>
              <p className="text-gray-600 font-medium">Selecciona un agente</p>
              <p className="text-xs text-gray-500 mt-1">Haz clic en cualquier nodo para ver detalles</p>
            </div>
          )}
        </div>
      </div>

      {/* Agent list legend */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p className="text-xs font-semibold text-gray-500 uppercase mb-3">Agentes en el sistema</p>
        <div className="grid grid-cols-5 gap-2">
          {AGENTS.map((agent) => (
            <button
              key={agent.id}
              onClick={() => setSelectedAgent(agent)}
              className={`p-2 rounded-lg text-xs font-medium transition-all ${
                selectedAgent?.id === agent.id
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {agent.shortName}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AgentVisualization;
