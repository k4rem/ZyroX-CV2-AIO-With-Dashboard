"use client";

import React, { useState, useEffect } from "react";
import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { AdminStats, AdminConfig } from "@/types/api";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { StatusLabel } from "@/components/ui/status";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const NODE_DISPLAY_NAMES: Record<string, string> = {
  "Primary API Cluster": "Host process",
  "Database Shards": "SQLite stores",
  "Bot Microservices": "Loaded cogs",
  "Auth Sockets": "Gateway connection",
};

function displayNodeName(apiName: string): string {
  return NODE_DISPLAY_NAMES[apiName] ?? apiName;
}

function nodeStatus(apiStatus: string): "online" | "degraded" | "offline" {
  const s = apiStatus.toLowerCase();
  if (s === "healthy") return "online";
  if (s === "booting" || s === "warning") return "degraded";
  return "offline";
}

export function AdminContent() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [config, setConfig] = useState<AdminConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notification, setNotification] = useState("");

  const fetchData = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    try {
      const [statsData, configData] = await Promise.all([
        api.getAdminStats(),
        api.getAdminConfig(),
      ]);
      setStats(statsData);
      setConfig(configData);
      setNotification(configData.global_notification || "");
    } catch (err) {
      console.error("Failed to fetch admin data:", err);
      toast.error("Failed to load platform data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    void fetchData();
    const interval = setInterval(() => void fetchData(true), 30_000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleMaintenance = async () => {
    if (!config) return;
    setSaving(true);
    try {
      const newStatus = !config.maintenance_mode;
      await api.updateAdminConfig({ maintenance_mode: newStatus });
      setConfig({ ...config, maintenance_mode: newStatus });
      toast.success(`Maintenance mode ${newStatus ? "enabled" : "disabled"}`);
    } catch {
      toast.error("Failed to update maintenance mode");
    } finally {
      setSaving(false);
    }
  };

  const handleBroadcast = async () => {
    setSaving(true);
    try {
      await api.updateAdminConfig({ global_notification: notification });
      if (config) setConfig({ ...config, global_notification: notification });
      toast.success("Broadcast message updated");
    } catch {
      toast.error("Failed to update broadcast message");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[240px] items-center justify-center text-body text-fg-2">
        Loading platform data…
      </div>
    );
  }

  const hostStrip = stats
    ? [
        { label: "Members (all guilds)", value: stats.total_users },
        { label: "Guilds", value: stats.active_servers },
        { label: "Gateway latency", value: stats.api_latency },
        { label: "Database size", value: stats.db_size },
      ]
    : [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Platform"
        description="Private host operations for the CLS OS root owner. Stats refresh every 30 seconds."
      >
        <Button variant="secondary" size="sm" onClick={() => void fetchData(true)} disabled={refreshing}>
          <RefreshCw className={cn("size-4", refreshing && "animate-spin")} aria-hidden="true" />
          Refresh
        </Button>
      </PageHeader>

      {hostStrip.length > 0 && (
        <dl className="grid grid-cols-2 gap-3 rounded-md border border-line bg-surface-1 p-4 lg:grid-cols-4">
          {hostStrip.map((item) => (
            <div key={item.label}>
              <dt className="text-caption text-fg-3">{item.label}</dt>
              <dd className="mt-0.5 tabular-nums text-body font-medium text-fg-1" dir="ltr">
                {item.value}
              </dd>
            </div>
          ))}
        </dl>
      )}

      <section className="rounded-md border border-line bg-surface-1 p-4">
        <h2 className="text-section-title text-fg-1">Required services</h2>
        <div className="mt-3 overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Component</TableHead>
                <TableHead>State</TableHead>
                <TableHead>Detail</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(stats?.nodes ?? []).map((node) => (
                <TableRow key={node.name}>
                  <TableCell className="text-fg-1">{displayNodeName(node.name)}</TableCell>
                  <TableCell>
                    <StatusLabel status={nodeStatus(node.status)}>{node.status}</StatusLabel>
                  </TableCell>
                  <TableCell className="font-mono text-caption text-fg-2" dir="ltr">
                    {node.load}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </section>

      <section className="space-y-4 rounded-md border border-line bg-surface-1 p-4">
        <h2 className="text-section-title text-fg-1">Global settings</h2>
        <div className="flex items-center justify-between gap-4 border-b border-line pb-4">
          <div>
            <p className="text-body text-fg-1">Maintenance mode</p>
            <p className="text-caption text-fg-2">Restrict dashboard access while maintenance is enabled.</p>
          </div>
          <Switch
            checked={Boolean(config?.maintenance_mode)}
            onCheckedChange={() => void handleToggleMaintenance()}
            disabled={saving}
            aria-label="Maintenance mode"
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="global-notification" className="text-body text-fg-1">
            Broadcast message
          </label>
          <p className="text-caption text-fg-2">
            Optional message shown on the platform page when set.
          </p>
          <Textarea
            id="global-notification"
            value={notification}
            onChange={(e) => setNotification(e.target.value)}
            rows={4}
            placeholder="No broadcast message"
          />
          <Button onClick={() => void handleBroadcast()} disabled={saving}>
            {saving ? "Saving…" : "Save broadcast"}
          </Button>
        </div>
      </section>
    </div>
  );
}
