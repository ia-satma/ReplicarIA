import { useState, useCallback, useRef, useEffect } from 'react';

export function useChatMessages() {
  const [messages, setMessages] = useState([]);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const streamingMessageRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addUserMessage = useCallback((content, attachments = []) => {
    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      type: 'user',
      content,
      text: content,
      attachments,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    
    setConversationHistory((prev) => [
      ...prev,
      { role: 'user', content }
    ]);

    return userMessage;
  }, []);

  const addBotMessage = useCallback((content, metadata = {}) => {
    const botMessage = {
      id: `bot-${Date.now()}`,
      role: 'assistant',
      type: 'bot',
      content,
      text: content,
      timestamp: new Date().toISOString(),
      ...metadata,
    };

    setMessages((prev) => [...prev, botMessage]);
    
    setConversationHistory((prev) => [
      ...prev,
      { role: 'assistant', content }
    ]);

    return botMessage;
  }, []);

  const addSystemMessage = useCallback((content, type = 'info') => {
    const systemMessage = {
      id: `system-${Date.now()}`,
      role: 'system',
      type,
      content,
      text: content,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, systemMessage]);
    return systemMessage;
  }, []);

  const startStreaming = useCallback((metadata = {}) => {
    setIsStreaming(true);
    
    const streamingMessage = {
      id: `streaming-${Date.now()}`,
      role: 'assistant',
      type: 'bot',
      content: '',
      text: '',
      isStreaming: true,
      timestamp: new Date().toISOString(),
      ...metadata,
    };

    streamingMessageRef.current = streamingMessage.id;
    setMessages((prev) => [...prev, streamingMessage]);
    
    return streamingMessage.id;
  }, []);

  const updateStreamingMessage = useCallback((chunk) => {
    if (!streamingMessageRef.current) return;

    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === streamingMessageRef.current
          ? { ...msg, content: msg.content + chunk, text: msg.text + chunk }
          : msg
      )
    );
  }, []);

  const finalizeStreamingMessage = useCallback((finalContent = null, metadata = {}) => {
    if (!streamingMessageRef.current) return;

    setMessages((prev) => {
      const updated = prev.map((msg) =>
        msg.id === streamingMessageRef.current
          ? {
              ...msg,
              content: finalContent || msg.content,
              text: finalContent || msg.text,
              isStreaming: false,
              ...metadata,
            }
          : msg
      );
      
      const finalMessage = updated.find(m => m.id === streamingMessageRef.current);
      if (finalMessage) {
        setConversationHistory((prevHistory) => [
          ...prevHistory,
          { role: 'assistant', content: finalMessage.content }
        ]);
      }
      
      return updated;
    });

    streamingMessageRef.current = null;
    setIsStreaming(false);
  }, []);

  const cancelStreaming = useCallback(() => {
    if (!streamingMessageRef.current) return;

    setMessages((prev) => prev.filter((msg) => msg.id !== streamingMessageRef.current));
    
    streamingMessageRef.current = null;
    setIsStreaming(false);
  }, []);

  const setTyping = useCallback((typing, delay = 0) => {
    if (delay > 0) {
      setTimeout(() => setIsTyping(typing), delay);
    } else {
      setIsTyping(typing);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationHistory([]);
  }, []);

  const removeMessage = useCallback((messageId) => {
    setMessages((prev) => prev.filter((msg) => msg.id !== messageId));
  }, []);

  const updateMessage = useCallback((messageId, updates) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId ? { ...msg, ...updates } : msg
      )
    );
  }, []);

  return {
    messages,
    conversationHistory,
    isTyping,
    isStreaming,
    messagesEndRef,

    addUserMessage,
    addBotMessage,
    addSystemMessage,
    startStreaming,
    updateStreamingMessage,
    finalizeStreamingMessage,
    cancelStreaming,
    setTyping,
    clearMessages,
    removeMessage,
    updateMessage,
    setMessages,
  };
}

export default useChatMessages;
