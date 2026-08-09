"use client";

import { useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";


type ModalProps = {
  open: boolean;
  title: string;
  children: ReactNode;
  onClose: () => void;
  footer?: ReactNode;
  className?: string;
};

export function Modal({ open, title, children, onClose, footer, className = "" }: ModalProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose, open]);

  if (!open || typeof document === "undefined") return null;

  return createPortal(
    <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        aria-label="Close dialog"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className={`relative z-10 w-full max-w-md rounded-2xl border border-white/10 bg-[#121816] p-5 shadow-xl ${className}`}
      >
        <div className="flex items-start justify-between gap-3">
          <h2 id="modal-title" className="text-base font-medium text-white/90">
            {title}
          </h2>
          <button
            type="button"
            className="text-sm text-white/50 hover:text-white/80"
            onClick={onClose}
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <div className="mt-4 text-sm text-white/75">{children}</div>
        {footer ? <div className="mt-5 flex justify-end gap-2">{footer}</div> : null}
      </div>
    </div>,
    document.body,
  );
}

type ConfirmModalProps = {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "primary" | "danger";
  onConfirm: () => void;
  onClose: () => void;
};

export function ConfirmModal({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "primary",
  onConfirm,
  onClose,
}: ConfirmModalProps) {
  return (
    <Modal
      open={open}
      title={title}
      onClose={onClose}
      footer={
        <>
          <button
            type="button"
            className="rounded-xl px-4 py-2.5 text-sm text-white/70 hover:bg-white/5"
            onClick={onClose}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className={`rounded-xl px-4 py-2.5 text-sm font-medium ${
              variant === "danger"
                ? "bg-rose-500 text-rose-950 hover:bg-rose-400"
                : "bg-emerald-500 text-emerald-950 hover:bg-emerald-400"
            }`}
            onClick={() => {
              onConfirm();
              onClose();
            }}
          >
            {confirmLabel}
          </button>
        </>
      }
    >
      {message}
    </Modal>
  );
}
