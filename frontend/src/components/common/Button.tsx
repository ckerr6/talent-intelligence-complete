import { ReactNode, ButtonHTMLAttributes, forwardRef } from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children?: ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  className = '',
  disabled,
  ...props
}, ref) => {
  const variantClasses = {
    primary: 'bg-indigo-600 text-white hover:bg-indigo-700 active:bg-indigo-800 focus:ring-indigo-500',
    secondary: 'bg-cyan-600 text-white hover:bg-cyan-700 active:bg-cyan-800 focus:ring-cyan-500',
    outline: 'border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50 active:bg-indigo-100 focus:ring-indigo-500',
    ghost: 'text-indigo-600 hover:bg-indigo-50 active:bg-indigo-100 focus:ring-indigo-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 active:bg-red-800 focus:ring-red-500',
    success: 'bg-emerald-600 text-white hover:bg-emerald-700 active:bg-emerald-800 focus:ring-emerald-500',
  };

  const sizeClasses = {
    xs: 'px-2 py-1 text-xs h-7',
    sm: 'px-3 py-1.5 text-sm h-9',
    md: 'px-4 py-2 text-base h-10',
    lg: 'px-6 py-3 text-lg h-12',
    xl: 'px-8 py-4 text-xl h-14',
  };

  const iconSizeClasses = {
    xs: 'w-3 h-3',
    sm: 'w-4 h-4',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
    xl: 'w-6 h-6',
  };

  const iconGapClasses = {
    xs: iconPosition === 'left' ? 'mr-1' : 'ml-1',
    sm: iconPosition === 'left' ? 'mr-1.5' : 'ml-1.5',
    md: iconPosition === 'left' ? 'mr-2' : 'ml-2',
    lg: iconPosition === 'left' ? 'mr-2.5' : 'ml-2.5',
    xl: iconPosition === 'left' ? 'mr-3' : 'ml-3',
  };

  const renderIcon = () => {
    if (loading) {
      return <Loader2 className={`${iconSizeClasses[size]} animate-spin ${iconPosition === 'left' ? 'mr-2' : 'ml-2'}`} />;
    }
    if (icon) {
      return <span className={`${iconGapClasses[size]} inline-flex items-center`}>{icon}</span>;
    }
    return null;
  };

  return (
    <button
      ref={ref}
      className={`
        inline-flex items-center justify-center
        font-semibold rounded-lg
        transition-all duration-200
        focus:outline-none focus:ring-2 focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed
        active:scale-[0.98]
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${fullWidth ? 'w-full' : ''}
        ${className}
      `}
      disabled={disabled || loading}
      {...props}
    >
      {iconPosition === 'left' && renderIcon()}
      {children}
      {iconPosition === 'right' && !loading && renderIcon()}
    </button>
  );
});

Button.displayName = 'Button';

export default Button;

