import { ReactNode, CSSProperties } from 'react';
import { Loader2 } from 'lucide-react';

interface CardProps {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  hover?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hierarchy?: 'primary' | 'secondary' | 'inline';
  onClick?: () => void;
  loading?: boolean;
  error?: string;
}

export default function Card({ 
  children, 
  className = '',
  style,
  hover = false, 
  padding = 'md',
  hierarchy = 'primary',
  onClick,
  loading = false,
  error,
}: CardProps) {
  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-6',
    lg: 'p-8',
  };

  const hierarchyClasses = {
    primary: 'bg-white shadow-lg border-2 border-transparent',
    secondary: 'bg-gray-50 shadow-sm border border-gray-200',
    inline: 'bg-transparent shadow-none border-b border-gray-200 rounded-none',
  };

  const hoverClasses = hover && !loading ? 'transition-all duration-200 hover:shadow-xl hover:-translate-y-1' : '';

  if (error) {
    return (
      <div
        className={`
          bg-red-50 border border-red-200 rounded-lg
          ${paddingClasses[padding]}
          ${className}
        `}
        style={style}
      >
        <div className="flex items-center gap-2 text-red-700">
          <span className="font-semibold">Error:</span>
          <span>{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`
        rounded-lg relative
        ${hierarchyClasses[hierarchy]}
        ${paddingClasses[padding]}
        ${hoverClasses}
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
      style={style}
      onClick={onClick}
    >
      {loading && (
        <div className="absolute inset-0 bg-white/80 backdrop-blur-sm rounded-lg flex items-center justify-center z-10">
          <div className="flex flex-col items-center gap-2">
            <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
            <span className="text-sm text-gray-600 font-medium">Loading...</span>
          </div>
        </div>
      )}
      {children}
    </div>
  );
}

