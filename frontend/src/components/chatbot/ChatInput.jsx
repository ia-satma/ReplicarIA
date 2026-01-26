import { useState, useRef, useCallback, useEffect } from 'react';

export function ChatInput({
  onSend,
  onAttach,
  disabled = false,
  placeholder = 'Escribe un mensaje...',
  showAttachButton = true,
  maxLength = 4000,
}) {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  }, [value]);

  useEffect(() => {
    if (!disabled) {
      textareaRef.current?.focus();
    }
  }, [disabled]);

  const handleSubmit = useCallback(
    (e) => {
      e?.preventDefault();
      
      const trimmedValue = value.trim();
      if (!trimmedValue || disabled) return;

      onSend(trimmedValue);
      setValue('');
      
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    },
    [value, disabled, onSend]
  );

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  const handleChange = useCallback(
    (e) => {
      const newValue = e.target.value;
      if (newValue.length <= maxLength) {
        setValue(newValue);
      }
    },
    [maxLength]
  );

  const charactersRemaining = maxLength - value.length;
  const showCharacterCount = value.length > maxLength * 0.8;

  return (
    <form onSubmit={handleSubmit} className="border-t border-white/10 bg-black/20 backdrop-blur-sm p-4">
      <div className="flex items-end gap-2">
        {showAttachButton && (
          <button
            type="button"
            onClick={onAttach}
            disabled={disabled}
            className="flex-shrink-0 p-2 text-gray-400 hover:text-gray-200 hover:bg-white/10 rounded-full transition-colors disabled:opacity-50"
            title="Adjuntar archivo"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
              />
            </svg>
          </button>
        )}

        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder={placeholder}
            rows={1}
            className="w-full px-4 py-3 pr-12 bg-white/10 border border-white/20 text-gray-100 placeholder-gray-500 rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-white/5 disabled:text-gray-500"
            style={{ maxHeight: '200px' }}
          />

          {showCharacterCount && (
            <span
              className={`absolute bottom-1 right-14 text-xs ${
                charactersRemaining < 100 ? 'text-red-400' : 'text-gray-500'
              }`}
            >
              {charactersRemaining}
            </span>
          )}
        </div>

        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="flex-shrink-0 p-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors disabled:bg-gray-600 disabled:cursor-not-allowed"
          title="Enviar mensaje"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
        </button>
      </div>

      <p className="text-xs text-gray-500 mt-2 text-center">
        Presiona Enter para enviar, Shift+Enter para nueva línea
      </p>
    </form>
  );
}

export default ChatInput;
