/**
 * useTimeout - Hook para timeouts con limpieza automática
 *
 * USO:
 *   useTimeout(() => {
 *     showNotification();
 *   }, 3000); // Después de 3 segundos
 *
 *   // Para cancelar, pasar null como delay
 *   useTimeout(callback, shouldRun ? 3000 : null);
 */

import { useEffect, useRef } from 'react';

export function useTimeout(callback, delay) {
  const savedCallback = useRef(callback);

  // Guardar la última callback
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  // Configurar el timeout
  useEffect(() => {
    if (delay === null) {
      return;
    }

    const id = setTimeout(() => {
      savedCallback.current();
    }, delay);

    return () => clearTimeout(id);
  }, [delay]);
}

export default useTimeout;
