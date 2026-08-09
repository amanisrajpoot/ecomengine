"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

export type ToastVariant = "default" | "success" | "error" | "warning";

export type ToastInput = {
  title: string;
  description?: string;
  variant?: ToastVariant;
  durationMs?: number;
};

type ToastRecord = ToastInput & {
  id: string;
};

type ToastContextValue = {
  toast: (input: ToastInput) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const variantStyles: Record<ToastVariant, string> = {
  default: "border-white/15 bg-[#0f1412]/95 text-white/90",
  success: "border-emerald-400/30 bg-emerald-950/95 text-emerald-50",
  error: "border-rose-400/30 bg-rose-950/95 text-rose-50",
  warning: "border-amber-400/30 bg-amber-950/95 text-amber-50",
};

function ToastItem({ toast, onDismiss }: { toast: ToastRecord; onDismiss: (id: string) => void }) {
  useEffect(() => {
    const duration = toast.durationMs ?? 5000;
    const timer = window.setTimeout(() => onDismiss(toast.id), duration);
    return () => window.clearTimeout(timer);
  }, [onDismiss, toast.durationMs, toast.id]);

  return (
    <div
      role="status"
      className={`pointer-events-auto w-full max-w-sm rounded-xl border px-4 py-3 shadow-lg backdrop-blur-md ${variantStyles[toast.variant ?? "default"]}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium">{toast.title}</p>
          {toast.description ? (
            <p className="mt-1 text-xs opacity-80">{toast.description}</p>
          ) : null}
        </div>
        <button
          type="button"
          className="shrink-0 text-xs opacity-60 hover:opacity-100"
          onClick={() => onDismiss(toast.id)}
          aria-label="Dismiss"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastRecord[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const dismiss = useCallback((id: string) => {
    setToasts((rows) => rows.filter((row) => row.id !== id));
  }, []);

  const toast = useCallback((input: ToastInput) => {
    const id =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setToasts((rows) => [...rows, { ...input, id }].slice(-5));
  }, []);

  const value = useMemo(() => ({ toast }), [toast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      {mounted
        ? createPortal(
            <div className="pointer-events-none fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
              {toasts.map((row) => (
                <ToastItem key={row.id} toast={row} onDismiss={dismiss} />
              ))}
            </div>,
            document.body,
          )
        : null}
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return ctx;
}
