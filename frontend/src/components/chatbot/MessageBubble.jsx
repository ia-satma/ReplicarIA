import { memo } from 'react';
import { AGENTS } from '../../constants/onboarding';

function MessageBubbleComponent({ message, onSuggestionClick }) {
  const isUser = message.role === 'user' || message.type === 'user';
  const isSystem = message.role === 'system';
  const isStreaming = message.isStreaming;

  const agent = message.agent ? AGENTS[message.agent] || AGENTS.ARCHIVO : AGENTS.ARCHIVO;

  if (isSystem) {
    return (
      <div className="flex justify-center my-2">
        <div
          className={`px-4 py-2 rounded-lg text-sm ${
            message.type === 'error'
              ? 'bg-red-500/20 text-red-300 border border-red-500/30'
              : message.type === 'success'
              ? 'bg-green-500/20 text-green-300 border border-green-500/30'
              : message.type === 'warning'
              ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
              : 'bg-white/10 text-gray-300 border border-white/20'
          }`}
        >
          {message.content || message.text}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`flex ${isUser ? 'flex-row-reverse' : 'flex-row'} items-end gap-2 max-w-[80%]`}
      >
        {!isUser && agent && (
          <div
            className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-lg"
            style={{ backgroundColor: agent.color + '30' }}
            title={agent.displayName}
          >
            {agent.avatar}
          </div>
        )}

        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          {!isUser && agent && (
            <span className="text-xs text-gray-400 mb-1 ml-1">
              {agent.displayName}
              {agent.role && <span className="text-gray-500"> · {agent.role}</span>}
            </span>
          )}

          <div
            className={`px-4 py-3 rounded-2xl ${
              isUser
                ? 'bg-blue-600 text-white rounded-br-md'
                : 'bg-white/10 backdrop-blur-sm text-gray-100 rounded-bl-md border border-white/20'
            } ${isStreaming ? 'animate-pulse' : ''}`}
          >
            <div className="whitespace-pre-wrap break-words">
              {message.content || message.text}
              {isStreaming && (
                <span className="inline-block w-2 h-4 ml-1 bg-gray-400 animate-pulse rounded" />
              )}
            </div>

            {message.attachments && message.attachments.length > 0 && (
              <div className="mt-2 pt-2 border-t border-white/20">
                {message.attachments.map((file, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm opacity-80">
                    <span>📎</span>
                    <span>{file.name}</span>
                    {file.size && (
                      <span className="text-xs">
                        ({(file.size / 1024).toFixed(1)} KB)
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {!isUser && message.suggestions && message.suggestions.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {message.suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => onSuggestionClick?.(suggestion)}
                  className="px-3 py-1.5 text-sm bg-white/10 border border-white/30 text-gray-200 rounded-full hover:bg-white/20 hover:border-white/40 transition-colors"
                >
                  {typeof suggestion === 'string' ? suggestion : suggestion.text}
                </button>
              ))}
            </div>
          )}

          <span className="text-xs text-gray-500 mt-1 mx-1">
            {new Date(message.timestamp).toLocaleTimeString('es-MX', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>

        {isUser && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium">
            Tú
          </div>
        )}
      </div>
    </div>
  );
}

export const MessageBubble = memo(MessageBubbleComponent);
export default MessageBubble;
