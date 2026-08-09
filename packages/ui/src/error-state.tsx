import type { ReactNode } from "react";

import { Button } from "./button";

type ErrorStateProps = {
  title?: string;
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
  action?: ReactNode;
  className?: string;
};

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
  retryLabel = "Try again",
  action,
  className = "",
}: ErrorStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-2xl border border-rose-400/20 bg-rose-950/20 px-6 py-10 text-center ${className}`}
    >
      <p className="text-base font-medium text-rose-100">{title}</p>
      <p className="mt-2 max-w-sm text-sm text-rose-200/70">{message}</p>
      {onRetry ? (
        <div className="mt-5">
          <Button variant="soft" onClick={onRetry}>
            {retryLabel}
          </Button>
        </div>
      ) : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}
