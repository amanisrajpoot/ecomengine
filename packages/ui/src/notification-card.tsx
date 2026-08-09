"use client";

import type { Notification } from "@commerce/types";
import { StatusBadge } from "./status-badge";

type NotificationCardProps = {
  notification: Notification;
  className?: string;
  orderHref?: string;
};

export function NotificationCard({
  notification,
  className = "",
  orderHref,
}: NotificationCardProps) {
  const orderLabel = notification.order_id ? (
    orderHref ? (
      <a href={orderHref} className="text-emerald-300/80 hover:text-emerald-200">
        order {notification.order_id.slice(0, 8)}…
      </a>
    ) : (
      `order ${notification.order_id.slice(0, 8)}…`
    )
  ) : null;

  return (
    <article
      className={`rounded-2xl border border-white/10 bg-black/20 px-4 py-4 ${className}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={notification.status} className="!text-[10px]" />
          <span className="text-xs uppercase tracking-wide text-white/45">
            {notification.event_name}
          </span>
        </div>
        <time className="text-xs text-white/40">
          {new Date(notification.created_at).toLocaleString("en-IN")}
        </time>
      </div>
      <p className="mt-3 text-sm text-white/80">{notification.body}</p>
      <p className="mt-2 text-xs text-white/40">
        {notification.channel} → {notification.recipient}
        {orderLabel ? <> · {orderLabel}</> : null}
      </p>
    </article>
  );
}
