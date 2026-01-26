export function ProgressIndicator({
  steps,
  currentStep,
  onStepClick,
  className = '',
}) {
  const numericStep = typeof currentStep === 'number' ? currentStep : 0;

  return (
    <div className={`bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10 ${className}`}>
      <h3 className="text-sm font-semibold text-gray-300 mb-4">
        Progreso del Onboarding
      </h3>

      <div className="space-y-3">
        {steps.map((step, index) => {
          const isCompleted = index < numericStep;
          const isCurrent = index === numericStep;
          const isClickable = index <= numericStep && onStepClick;

          return (
            <div
              key={step.id || step.key || index}
              onClick={() => isClickable && onStepClick(index)}
              className={`flex items-center gap-3 p-2 rounded-lg transition-colors ${
                isClickable ? 'cursor-pointer hover:bg-white/10' : ''
              } ${isCurrent ? 'bg-blue-500/20' : ''}`}
            >
              <div
                className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  isCompleted
                    ? 'bg-green-500 text-white'
                    : isCurrent
                    ? 'bg-blue-600 text-white'
                    : 'bg-white/10 text-gray-500'
                }`}
              >
                {isCompleted ? (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  index + 1
                )}
              </div>

              <div className="flex-1 min-w-0">
                <p
                  className={`text-sm font-medium truncate ${
                    isCurrent ? 'text-blue-300' : isCompleted ? 'text-gray-300' : 'text-gray-500'
                  }`}
                >
                  {step.title}
                </p>
                {isCurrent && step.description && (
                  <p className="text-xs text-gray-500 truncate">{step.description}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 pt-4 border-t border-white/10">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Progreso total</span>
          <span>{Math.round((numericStep / Math.max(steps.length - 1, 1)) * 100)}%</span>
        </div>
        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600 transition-all duration-300"
            style={{ width: `${(numericStep / Math.max(steps.length - 1, 1)) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export default ProgressIndicator;
