import { useState, useCallback, useRef } from 'react';

export function useChatAPI() {
  const [isSearchingWeb, setIsSearchingWeb] = useState(false);
  const [useRealAI, setUseRealAI] = useState(true);
  const [lastError, setLastError] = useState(null);
  const abortControllerRef = useRef(null);

  const sendToClaudeAPI = useCallback(async ({
    message,
    conversationHistory = [],
    companyId = null,
    companyContext = {},
    stream = true,
    onStreamChunk = null,
  }) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setLastError(null);

    try {
      const response = await fetch('/api/chat/archivo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          history: conversationHistory,
          company_id: companyId,
          company_context: companyContext
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (stream && onStreamChunk) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          fullContent += chunk;
          onStreamChunk(chunk);
        }

        return {
          message: fullContent,
          streamed: true,
        };
      } else {
        const data = await response.json();
        return {
          message: data.message || data.response,
          suggestions: data.suggestions || [],
          extractedData: data.extracted_data,
        };
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        return null;
      }

      const errorMessage = err.message || 'Error de conexión';
      setLastError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  const searchWeb = useCallback(async (query, rfc = null) => {
    setIsSearchingWeb(true);
    setLastError(null);

    try {
      const response = await fetch('/api/chat/archivo/web-search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, rfc })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      const errorMessage = err.message;
      setLastError(errorMessage);
      throw err;
    } finally {
      setIsSearchingWeb(false);
    }
  }, []);

  const analyzeDocumentWithAI = useCallback(async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/chat/archivo/analyze-document', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Error analyzing document');
      }

      return await response.json();
    } catch (err) {
      const errorMessage = err.message;
      setLastError(errorMessage);
      throw err;
    }
  }, []);

  const cancelRequest = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  const toggleRealAI = useCallback((enabled) => {
    setUseRealAI(enabled);
  }, []);

  return {
    isSearchingWeb,
    useRealAI,
    lastError,

    sendToClaudeAPI,
    searchWeb,
    analyzeDocumentWithAI,
    cancelRequest,
    toggleRealAI,
    clearError: () => setLastError(null),
    abortControllerRef,
  };
}

export default useChatAPI;
