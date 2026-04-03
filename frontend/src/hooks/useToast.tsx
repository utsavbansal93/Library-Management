import { createContext, useContext, useState, useCallback } from 'react';
import type { ReactNode } from 'react';

type ToastContextType = {
  showToast: (message: string) => void;
};

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<{ message: string; visible: boolean; id: number }>({
    message: '',
    visible: false,
    id: 0,
  });

  const showToast = useCallback((message: string) => {
    setToast((prev) => ({ message, visible: true, id: prev.id + 1 }));
    setTimeout(() => {
      setToast((prev) => ({ ...prev, visible: false }));
    }, 3000);
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Global Toast Render */}
      <div
        className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] transition-all duration-300 transform ${
          toast.visible ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0 pointer-events-none'
        }`}
      >
        <div className="bg-surface-container-highest text-on-surface shadow-lg rounded-xl px-4 py-3 font-body text-sm font-semibold flex items-center gap-3">
          <span className="material-symbols-outlined text-primary text-[20px]">check_circle</span>
          {toast.message}
        </div>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
