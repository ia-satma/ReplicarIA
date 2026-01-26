export function LoadingSpinner({ size = 'md', className = '' }) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-2',
    lg: 'w-12 h-12 border-3',
    xl: 'w-16 h-16 border-4',
  };

  return (
    <div
      className={`${sizeClasses[size] || sizeClasses.md} border-blue-500 border-t-transparent rounded-full animate-spin ${className}`}
    />
  );
}

export default LoadingSpinner;
