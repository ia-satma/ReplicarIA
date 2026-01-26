import React, { useState, useRef, useEffect, useCallback } from 'react';
import AgentFlowVisualization from './AgentFlowVisualization';

/**
 * AGENT_INFO - Maps agent IDs to their icons and names
 */
const AGENT_INFO = {
  A1: { icon: '📥', name: 'Recepción' },
  A2: { icon: '🔍', name: 'Análisis' },
  A3: { icon: '📜', name: 'Normativo' },
  A4: { icon: '📊', name: 'Contable' },
  A5: { icon: '⚙️', name: 'Operativo' },
  A6: { icon: '💰', name: 'Financiero' },
  A7: { icon: '⚖️', name: 'Legal' },
  A8: { icon: '🛡️', name: 'Red Team' },
  A9: { icon: '📝', name: 'Síntesis' },
  A10: { icon: '📁', name: 'Archivo' },
};

/**
 * TypingIndicator Component
 * Shows three bouncing dots with agent name
 */
const TypingIndicator = ({ agentId, agentName }) => {
  const agent = AGENT_INFO[agentId] || AGENT_INFO.A1;
  const displayName = agentName || agent.name;

  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center text-lg">
        {agent.icon}
      </div>

      <div className="flex flex-col">
        <span className="text-sm font-medium text-gray-700 mb-2">{displayName}</span>

        <div className="flex items-center gap-1 px-4 py-3 bg-gray-100 rounded-lg">
          <span
            className="w-2 h-2 bg-gray-600 rounded-full animate-bounce"
            style={{ animationDelay: '0ms' }}
          />
          <span
            className="w-2 h-2 bg-gray-600 rounded-full animate-bounce"
            style={{ animationDelay: '150ms' }}
          />
          <span
            className="w-2 h-2 bg-gray-600 rounded-full animate-bounce"
            style={{ animationDelay: '300ms' }}
          />
        </div>
      </div>
    </div>
  );
};

/**
 * MessageBubble Component
 * Displays user and agent messages with optional confidence progress bar
 */
const MessageBubble = ({ message }) => {
  const isUser = message.role === 'user';
  const agent = AGENT_INFO[message.agentId] || AGENT_INFO.A1;

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`flex ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start gap-3 max-w-[75%]`}>
        {/* Agent Avatar */}
        {!isUser && (
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center text-lg">
            {agent.icon}
          </div>
        )}

        {/* Message Content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          {/* Agent Name Label */}
          {!isUser && (
            <span className="text-xs font-medium text-gray-600 mb-1">{agent.name}</span>
          )}

          {/* Message Bubble */}
          <div
            className={`px-4 py-3 rounded-lg ${
              isUser
                ? 'bg-blue-600 text-white rounded-br-none'
                : 'bg-gray-100 text-gray-900 rounded-bl-none'
            }`}
          >
            <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
          </div>

          {/* Confidence Progress Bar */}
          {!isUser && message.confidence && (
            <div className="w-full mt-2">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-gray-500">Confianza:</span>
                <span className="text-xs font-medium text-gray-600">{Math.round(message.confidence * 100)}%</span>
              </div>
              <div className="w-full bg-gray-300 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${message.confidence * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* Timestamp */}
          <span className="text-xs text-gray-500 mt-1">
            {new Date(message.timestamp).toLocaleTimeString('es-MX', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>

        {/* User Avatar */}
        {isUser && (
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium">
            Tú
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Main AgentChat Component
 * Complete chat interface with agent flow visualization and message handling
 */
const AgentChat = ({ projectId }) => {
  // State Management
  const [messages, setMessages] = useState([
    {
      id: '1',
      role: 'agent',
      agentId: 'A1',
      content: '¡Hola! Soy el asistente de agentes. Aquí puedes interactuar con nuestro sistema de inteligencia artificial.',
      timestamp: new Date(),
      confidence: 0.95,
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeAgents, setActiveAgents] = useState([]);
  const [completedAgents, setCompletedAgents] = useState([]);
  const [currentAgent, setCurrentAgent] = useState(null);

  // Refs
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /**
   * Send message to backend API
   * Simulates agent progress and adds response to messages
   */
  const sendMessage = useCallback(async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || isLoading) return;

    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: trimmedInput,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Determine next agent to activate
      const allAgentIds = Object.keys(AGENT_INFO);
      const nextAgentId = allAgentIds.find((id) => !completedAgents.includes(id));

      if (nextAgentId && !activeAgents.includes(nextAgentId)) {
        setActiveAgents((prev) => [...prev, nextAgentId]);
        setCurrentAgent(nextAgentId);
      }

      // Simulate agent processing
      const processingDelay = setTimeout(() => {
        if (activeAgents.length > 0) {
          const agentToComplete = activeAgents[0];
          setCompletedAgents((prev) => [...prev, agentToComplete]);
          setActiveAgents((prev) => prev.filter((id) => id !== agentToComplete));
        }
      }, 2000);

      // POST to backend
      const response = await fetch('/api/agents/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: trimmedInput,
          project_id: projectId,
        }),
      });

      clearTimeout(processingDelay);

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();

      // Add agent response
      const agentMessage = {
        id: Date.now().toString(),
        role: 'agent',
        agentId: nextAgentId || 'A1',
        content: data.response || data.message || 'Respuesta procesada',
        timestamp: new Date(),
        confidence: data.confidence || 0.85,
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      console.error('Error sending message:', error);

      // Add error message
      const errorMessage = {
        id: Date.now().toString(),
        role: 'agent',
        agentId: 'A1',
        content: `Error al procesar la solicitud: ${error.message}`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);

      // Reset agent states on error
      if (activeAgents.length > 0) {
        setActiveAgents((prev) => prev.slice(1));
      }
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }, [input, isLoading, projectId, activeAgents, completedAgents]);

  /**
   * Handle key press in input field
   */
  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    },
    [sendMessage]
  );

  return (
    <div className="h-screen flex flex-col bg-white">
      {/* Top: Agent Flow Visualization */}
      <div className="flex-shrink-0 border-b border-gray-200 p-4 max-h-[35%] overflow-auto">
        <AgentFlowVisualization
          activeAgents={activeAgents}
          completedAgents={completedAgents}
          showDetails={false}
        />
      </div>

      {/* Middle: Messages Area */}
      <div className="flex-1 flex flex-col overflow-hidden bg-white">
        <div className="flex-1 overflow-y-auto p-6">
          {messages.length === 1 && messages[0].role === 'agent' && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="text-4xl mb-4">💬</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Bienvenido a AgentChat</h3>
                <p className="text-gray-600 max-w-md">
                  Inicia una conversación escribiendo tu mensaje en el campo inferior. Nuestros agentes inteligentes procesarán tu solicitud.
                </p>
              </div>
            </div>
          )}

          {messages.length > 1 && (
            <div>
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}

              {isLoading && (
                <TypingIndicator agentId={currentAgent || 'A1'} />
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Bottom: Input Field */}
        <div className="flex-shrink-0 border-t border-gray-200 bg-white p-4">
          <div className="flex items-end gap-3">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Escribe tu mensaje aquí... (Presiona Enter para enviar, Shift+Enter para nueva línea)"
              rows={1}
              disabled={isLoading}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none disabled:bg-gray-100"
              style={{ maxHeight: '120px' }}
            />

            <button
              onClick={sendMessage}
              disabled={isLoading || !input.trim()}
              className="flex-shrink-0 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
              title="Enviar mensaje"
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Enviando...
                </span>
              ) : (
                'Enviar'
              )}
            </button>
          </div>

          <p className="text-xs text-gray-500 mt-2">
            Presiona Enter para enviar, Shift+Enter para nueva línea
          </p>
        </div>
      </div>
    </div>
  );
};

export default AgentChat;
