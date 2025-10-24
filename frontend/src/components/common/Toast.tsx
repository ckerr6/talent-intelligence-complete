import { useEffect, useState } from 'react';
import { X, CheckCircle2, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { createPortal } from 'react-dom';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastProps {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
  onClose: (id: string) => void;
}

function Toast({ id, type, message, duration = 5000, action, onClose }: ToastProps) {
  const [progress, setProgress] = useState(100);
  const [isLeaving, setIsLeaving] = useState(false);

  useEffect(() => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setProgress(remaining);

      if (remaining === 0) {
        clearInterval(interval);
        handleClose();
      }
    }, 16);

    return () => clearInterval(interval);
  }, [duration]);

  const handleClose = () => {
    setIsLeaving(true);
    setTimeout(() => onClose(id), 200);
  };

  const config = {
    success: {
      icon: CheckCircle2,
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-200',
      textColor: 'text-emerald-800',
      iconColor: 'text-emerald-600',
      progressColor: 'bg-emerald-600',
    },
    error: {
      icon: AlertCircle,
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      textColor: 'text-red-800',
      iconColor: 'text-red-600',
      progressColor: 'bg-red-600',
    },
    warning: {
      icon: AlertTriangle,
      bgColor: 'bg-amber-50',
      borderColor: 'border-amber-200',
      textColor: 'text-amber-800',
      iconColor: 'text-amber-600',
      progressColor: 'bg-amber-600',
    },
    info: {
      icon: Info,
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-800',
      iconColor: 'text-blue-600',
      progressColor: 'bg-blue-600',
    },
  };

  const { icon: Icon, bgColor, borderColor, textColor, iconColor, progressColor } = config[type];

  return (
    <div
      className={`
        ${bgColor} ${borderColor} ${textColor}
        border rounded-lg shadow-lg
        p-4 mb-3 min-w-[320px] max-w-md
        transition-all duration-200
        ${isLeaving ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0'}
      `}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 ${iconColor} flex-shrink-0 mt-0.5`} />
        
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium">{message}</p>
          
          {action && (
            <button
              onClick={() => {
                action.onClick();
                handleClose();
              }}
              className={`mt-2 text-sm font-semibold ${iconColor} hover:underline focus:outline-none focus:underline`}
            >
              {action.label}
            </button>
          )}
        </div>

        <button
          onClick={handleClose}
          className={`${iconColor} hover:opacity-70 transition-opacity focus:outline-none focus:ring-2 focus:ring-offset-1 rounded`}
          aria-label="Close notification"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Progress bar */}
      <div className="mt-3 h-1 bg-black/10 rounded-full overflow-hidden">
        <div
          className={`h-full ${progressColor} transition-all duration-75 ease-linear`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}

// Toast Container
export interface ToastContainerProps {
  toasts: ToastProps[];
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center';
}

export function ToastContainer({ toasts, position = 'top-right' }: ToastContainerProps) {
  const positionClasses = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-center': 'top-4 left-1/2 -translate-x-1/2',
  };

  if (toasts.length === 0) return null;

  return createPortal(
    <div
      className={`fixed ${positionClasses[position]} z-[1600] pointer-events-none`}
      aria-live="polite"
      aria-atomic="true"
    >
      <div className="pointer-events-auto">
        {toasts.map((toast) => (
          <Toast key={toast.id} {...toast} />
        ))}
      </div>
    </div>,
    document.body
  );
}

// Hook for managing toasts
export function useToast() {
  const [toasts, setToasts] = useState<ToastProps[]>([]);

  const addToast = (
    type: ToastType,
    message: string,
    options?: {
      duration?: number;
      action?: { label: string; onClick: () => void };
    }
  ) => {
    const id = Math.random().toString(36).substring(7);
    const newToast: ToastProps = {
      id,
      type,
      message,
      duration: options?.duration,
      action: options?.action,
      onClose: removeToast,
    };

    setToasts((prev) => [...prev, newToast]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  return {
    toasts,
    success: (message: string, options?: Parameters<typeof addToast>[2]) =>
      addToast('success', message, options),
    error: (message: string, options?: Parameters<typeof addToast>[2]) =>
      addToast('error', message, options),
    warning: (message: string, options?: Parameters<typeof addToast>[2]) =>
      addToast('warning', message, options),
    info: (message: string, options?: Parameters<typeof addToast>[2]) =>
      addToast('info', message, options),
  };
}

export default Toast;

