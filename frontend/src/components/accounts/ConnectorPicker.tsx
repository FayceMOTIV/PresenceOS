"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Instagram, Facebook, Linkedin, Music, AlertCircle } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// ── Types ─────────────────────────────────────────────────────────────────────

type Platform = "instagram" | "tiktok" | "linkedin" | "facebook";

interface Connector {
  id: string;
  platform: Platform;
  account_username?: string;
  account_avatar_url?: string;
  status: "connected" | "expired" | "revoked" | "error";
  is_active: boolean;
}

export interface ConnectorPickerProps {
  connectors: Connector[];
  value?: string; // connector_id
  onChange: (connectorId: string) => void;
  platform?: string; // optional filter by platform
}

// ── Platform config ────────────────────────────────────────────────────────────

const PLATFORM_CONFIG: Record<
  Platform,
  { icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>; color: string; label: string }
> = {
  instagram: { icon: Instagram, color: "#E4405F", label: "Instagram" },
  tiktok:    { icon: Music,     color: "#000000", label: "TikTok" },
  linkedin:  { icon: Linkedin,  color: "#0A66C2", label: "LinkedIn" },
  facebook:  { icon: Facebook,  color: "#1877F2", label: "Facebook" },
};

// ── Sub-components ─────────────────────────────────────────────────────────────

function PlatformIcon({ platform, size = 16 }: { platform: Platform; size?: number }) {
  const cfg = PLATFORM_CONFIG[platform];
  const Icon = cfg.icon;
  return (
    <Icon
      className="shrink-0"
      style={{ color: cfg.color, width: size, height: size }}
    />
  );
}

function ConnectorLabel({ connector }: { connector: Connector }) {
  const username = connector.account_username ?? "Compte inconnu";
  const platformLabel = PLATFORM_CONFIG[connector.platform]?.label ?? connector.platform;

  return (
    <span className="flex items-center gap-2 min-w-0">
      <PlatformIcon platform={connector.platform} />
      {connector.account_avatar_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={connector.account_avatar_url}
          alt={username}
          className="w-5 h-5 rounded-full object-cover border border-gray-200"
        />
      )}
      <span className="truncate text-sm font-medium text-foreground">{username}</span>
      <span className="text-xs text-muted-foreground shrink-0">· {platformLabel}</span>
    </span>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

export function ConnectorPicker({ connectors, value, onChange, platform }: ConnectorPickerProps) {
  // Filter: active + connected + optional platform filter
  const eligible = connectors.filter(
    (c) =>
      c.is_active &&
      c.status === "connected" &&
      (platform ? c.platform === platform : true)
  );

  // Auto-select when there is exactly one eligible connector
  useEffect(() => {
    if (eligible.length === 1 && !value) {
      onChange(eligible[0].id);
    }
    // Only run when the eligible list or value changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eligible.length, value]);

  // ── 0 connectors ──────────────────────────────────────────────────────────
  if (eligible.length === 0) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-dashed border-gray-200 bg-gray-50 px-3 py-2 text-sm text-muted-foreground">
        <AlertCircle className="h-4 w-4 shrink-0 text-amber-500" />
        <span>Aucun compte connecté.&nbsp;</span>
        <Link
          href="/accounts"
          className="font-medium text-violet-600 underline-offset-2 hover:underline"
        >
          Connecter un compte
        </Link>
      </div>
    );
  }

  // ── 1 connector — read-only display ───────────────────────────────────────
  if (eligible.length === 1) {
    const single = eligible[0];
    return (
      <div className="flex items-center gap-2 rounded-lg border border-gray-200/80 bg-white px-3 py-2 shadow-sm">
        <ConnectorLabel connector={single} />
      </div>
    );
  }

  // ── 2+ connectors — dropdown ───────────────────────────────────────────────
  return (
    <Select value={value ?? ""} onValueChange={onChange}>
      <SelectTrigger className="w-full bg-white border-gray-200/80 shadow-sm">
        <SelectValue placeholder="Choisir un compte…">
          {value && (() => {
            const selected = eligible.find((c) => c.id === value);
            return selected ? <ConnectorLabel connector={selected} /> : null;
          })()}
        </SelectValue>
      </SelectTrigger>
      <SelectContent className="bg-white border-gray-200 shadow-lg">
        {eligible.map((connector) => (
          <SelectItem key={connector.id} value={connector.id}>
            <ConnectorLabel connector={connector} />
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
