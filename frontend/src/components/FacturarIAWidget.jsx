import React, { useEffect, useRef, useState } from 'react';

const FacturarIAWidget = () => {
  const widgetContainerRef = useRef(null);
  const [widgetLoaded, setWidgetLoaded] = useState(false);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    const checkElevenLabsAvailable = () => {
      return typeof window !== 'undefined' && 
             window.customElements && 
             window.customElements.get('elevenlabs-convai');
    };

    const initWidget = () => {
      if (widgetContainerRef.current && !widgetContainerRef.current.querySelector('elevenlabs-convai')) {
        try {
          const widget = document.createElement('elevenlabs-convai');
          widget.setAttribute('agent-id', 'agent_6801kfej2xfce94vtvbppj61ry61');
          widgetContainerRef.current.appendChild(widget);
          setWidgetLoaded(true);
        } catch (error) {
          console.error('Error initializing Facturar.IA widget:', error);
          setLoadError(true);
        }
      }
    };

    if (checkElevenLabsAvailable()) {
      initWidget();
    } else {
      const maxAttempts = 10;
      let attempts = 0;
      const interval = setInterval(() => {
        attempts++;
        if (checkElevenLabsAvailable()) {
          clearInterval(interval);
          initWidget();
        } else if (attempts >= maxAttempts) {
          clearInterval(interval);
          console.warn('Facturar.IA: ElevenLabs widget could not be loaded');
          setLoadError(true);
        }
      }, 500);

      return () => clearInterval(interval);
    }
  }, []);

  if (loadError) {
    return null;
  }

  return (
    <div 
      ref={widgetContainerRef}
      className="fixed bottom-6 right-24 z-40"
      title="Facturar.IA - Asistente de Facturación SAT"
      aria-label="Facturar.IA - Asistente de voz para facturación SAT"
    />
  );
};

export default FacturarIAWidget;
