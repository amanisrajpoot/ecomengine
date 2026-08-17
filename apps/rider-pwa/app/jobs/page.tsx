"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import type { Delivery, DeliveryPartnerProfile } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Button, EmptyState, Skeleton, StatTile } from "@commerce/ui";

import { JobCard } from "@/components/JobCard";
import { getApiClient } from "@/lib/api";
import { deliveryNeedsAction } from "@/lib/deliveryHelpers";
import { session } from "@/lib/session";

export default function JobsPage() {
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [profile, setProfile] = useState<DeliveryPartnerProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        if (!session.getAccessToken()) {
          setError("Sign in to view jobs.");
          return;
        }
        const api = getApiClient();
        try {
          const p = await api.getMyPartnerProfile();
          setProfile(p);
        } catch {
          setProfile(null);
        }
        const list = await api.listMyDeliveries(true);
        setDeliveries(list);
      } catch (err) {
        if (err instanceof ApiError && err.code === "PARTNER_NOT_FOUND") {
          setError("Create your partner profile first.");
        } else {
          setError(err instanceof ApiError ? err.message : "Failed to load jobs");
        }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const stats = useMemo(() => {
    const actionNeeded = deliveries.filter(deliveryNeedsAction).length;
    const inProgress = deliveries.filter((d) => d.status === "IN_PROGRESS").length;
    return { actionNeeded, inProgress, total: deliveries.length };
  }, [deliveries]);

  const urgentJobs = useMemo(
    () => deliveries.filter(deliveryNeedsAction),
    [deliveries],
  );

  const displayJobs = urgentJobs.length > 0 ? urgentJobs : deliveries;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Active jobs</h1>
        <p className="text-sm text-gray-500">
          {profile?.is_online ? "You are online and ready for assignments." : "Go online on your profile to receive jobs."}
        </p>
      </div>

      {!loading && profile ? (
        <div className="grid grid-cols-3 gap-3">
          <StatTile
            label="Action needed"
            value={stats.actionNeeded}
            accent={stats.actionNeeded > 0}
            className={stats.actionNeeded > 0 ? "border-blue-200 bg-blue-50" : ""}
          />
          <StatTile label="In progress" value={stats.inProgress} />
          <StatTile label="Active" value={stats.total} />
        </div>
      ) : null}

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
      ) : null}

      {error ? (
        <p className="text-sm text-red-600">
          {error}{" "}
          <Link href="/onboarding" className="font-medium underline">Partner profile</Link>
          {" · "}
          <Link href="/login" className="font-medium underline">Sign in</Link>
        </p>
      ) : null}

      <ul className="space-y-3">
        {displayJobs.map((delivery) => (
          <li key={delivery.id}>
            <JobCard delivery={delivery} />
          </li>
        ))}
      </ul>

      {!loading && !error && deliveries.length === 0 ? (
        <EmptyState
          title="No active jobs"
          description="Stay online on your profile page. Jobs appear here when dispatch assigns you."
          action={
            <Link href="/onboarding">
              <Button variant="brand" className="bg-[var(--brand)] hover:bg-[var(--brand-dark)]">
                Go to profile
              </Button>
            </Link>
          }
        />
      ) : null}
    </div>
  );
}
