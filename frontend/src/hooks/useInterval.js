/**
 * useInterval - Hook para intervalos con limpieza automática
 *
 * Evita memory leaks al limpiar el interval cuando el componente se desmonta.
 *
 * USO:
 *   useInterval(() => {
 *     fetchData();
 *   }, 5000); // Cada 5 segundos
 *
 *   // Para pausar, pasar null como delay
 *   useInterval(callback, isRunning ? 5000 : null);
 */

import { useEffect, useRef } from 'react';

export function useInterval(callback, delay) {
  const savedCallback = useRef(callback);

  // Guardar la última callback
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  // Configurar el interval
  useEffect(() => {
    // No hacer nada si delay es null (permite pausar)
    if (delay === null) {
      return;
    }

    const tick = () => {
      savedCallback.current();
    };

    const id = setInterval(tick, delay);

    // Limpieza al desmontar o cuando delay cambia
    return () => clearInterval(id);
  }, [delay]);
}

export default useInterval;
