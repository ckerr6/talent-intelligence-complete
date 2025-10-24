import { ReactNode, MouseEvent } from 'react';
import { X } from 'lucide-react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  rounded?: boolean;
  icon?: ReactNode;
  onRemove?: () => void;
  onClick?: () => void;
  className?: string;
  pulse?: boolean;
}

export default function Badge({ 
  children, 
  variant = 'default', 
  size = 'md',
  rounded = false,
  icon,
  onRemove,
  onClick,
  className = '',
  pulse = false,
}: BadgeProps) {
  const variantClasses = {
    default: 'bg-gray-100 text-gray-700 border-gray-200',
    primary: 'bg-indigo-100 text-indigo-700 border-indigo-200',
    secondary: 'bg-cyan-100 text-cyan-700 border-cyan-200',
    success: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    warning: 'bg-amber-100 text-amber-700 border-amber-200',
    danger: 'bg-red-100 text-red-700 border-red-200',
    info: 'bg-blue-100 text-blue-700 border-blue-200',
  };

  const sizeClasses = {
    xs: 'px-1.5 py-0.5 text-xs gap-1',
    sm: 'px-2 py-0.5 text-xs gap-1',
    md: 'px-2.5 py-1 text-sm gap-1.5',
    lg: 'px-3 py-1.5 text-base gap-2',
  };

  const iconSizeClasses = {
    xs: 'w-2.5 h-2.5',
    sm: 'w-3 h-3',
    md: 'w-3.5 h-3.5',
    lg: 'w-4 h-4',
  };

  const isInteractive = onClick || onRemove;

  const handleClick = (e: MouseEvent<HTMLSpanElement>) => {
    if (onClick) {
      e.stopPropagation();
      onClick();
    }
  };

  const handleRemove = (e: MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (onRemove) {
      onRemove();
    }
  };

  return (
    <span
      className={`
        inline-flex items-center font-semibold border
        transition-all duration-200
        ${rounded ? 'rounded-full' : 'rounded-md'}
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${isInteractive ? 'cursor-pointer hover:opacity-80' : ''}
        ${pulse ? 'animate-pulse' : ''}
        ${className}
      `}
      onClick={handleClick}
    >
      {icon && (
        <span className={`${iconSizeClasses[size]} inline-flex items-center justify-center`}>
          {icon}
        </span>
      )}
      {children}
      {onRemove && (
        <button
          type="button"
          onClick={handleRemove}
          className={`
            ${iconSizeClasses[size]}
            inline-flex items-center justify-center
            hover:opacity-70 transition-opacity
            focus:outline-none focus:ring-1 focus:ring-offset-1 rounded-full
          `}
          aria-label="Remove"
        >
          <X className={iconSizeClasses[size]} />
        </button>
      )}
    </span>
  );
}

