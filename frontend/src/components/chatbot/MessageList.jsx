import { useRef, useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';

export function MessageList({
  messages,
  isTyping,
  currentAgent,
  onSuggestionClick,
  className = '',
}) {
  const bottomRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isTyping]);

  return (
    <div
      ref={containerRef}
      className={`flex-1 overflow-y-auto p-4 space-y-1 ${className}`}
    >
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-gray-400">
          <div className="text-6xl mb-4">💬</div>
          <p className="text-lg">Inicia la conversación</p>
          <p className="text-sm">Escribe un mensaje para comenzar</p>
        </div>
      ) : (
        <>
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onSuggestionClick={onSuggestionClick}
            />
          ))}

          {isTyping && <TypingIndicator agent={currentAgent} />}

          <div ref={bottomRef} />
        </>
      )}
    </div>
  );
}

export default MessageList;
