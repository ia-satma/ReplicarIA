import React from 'react';

function RiskScoreBadge({ score, showLabel = true, size = 'md' }) {
  const getNivel = (score) => {
    if (score < 40) return { nivel: 'BAJO', color: 'bg-green-100 text-green-800 border-green-200' };
    if (score < 60) return { nivel: 'MEDIO', color: 'bg-yellow-100 text-yellow-800 border-yellow-200' };
    if (score < 80) return { nivel: 'ALTO', color: 'bg-orange-100 text-orange-800 border-orange-200' };
    return { nivel: 'CRÍTICO', color: 'bg-red-100 text-red-800 border-red-200' };
  };
  
  const { nivel, color } = getNivel(score || 0);
  
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-2'
  };
  
  return (
    <span className={`
      inline-flex items-center gap-1 rounded-full border font-medium
      ${color} ${sizeClasses[size]}
    `}>
      <span className="font-bold">{score || 0}</span>
      {showLabel && <span className="opacity-75">/ {nivel}</span>}
    </span>
  );
}

export default RiskScoreBadge;
