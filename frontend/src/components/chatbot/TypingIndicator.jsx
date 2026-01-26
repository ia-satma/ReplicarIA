import { AGENTS } from '../../constants/onboarding';

export function TypingIndicator({ agent }) {
  const agentData = agent ? AGENTS[agent] || AGENTS.ARCHIVO : AGENTS.ARCHIVO;

  return (
    <div className="flex items-end gap-2 mb-4">
      <div
        className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-lg"
        style={{ backgroundColor: agentData.color + '30' }}
      >
        {agentData.avatar}
      </div>

      <div className="flex flex-col items-start">
        <span className="text-xs text-gray-400 mb-1 ml-1">
          {agentData.displayName}
        </span>
        
        <div className="px-4 py-3 rounded-2xl rounded-bl-md bg-white/10 backdrop-blur-sm border border-white/20">
          <div className="flex gap-1">
            <span
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '0ms' }}
            />
            <span
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '150ms' }}
            />
            <span
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '300ms' }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default TypingIndicator;
