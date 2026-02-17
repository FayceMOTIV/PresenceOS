"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Instagram,
  Facebook,
  Linkedin,
  Music,
  Plus,
  Link2,
  Users,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { HelpTooltip } from "@/components/ui/help-tooltip";
import { connectorsApi } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { AccountCard } from "@/components/accounts/AccountCard";
import { AddAccountDialog } from "@/components/accounts/AddAccountDialog";

// ── Types ─────────────────────────────────────────────────────────────────────

type PlatformId = "instagram" | "facebook" | "tiktok" | "linkedin";

interface Connector {
  id: string;
  brand_id: string;
  platform: PlatformId;
  account_username?: string;
  account_avatar_url?: string;
  status: "connected" | "expired" | "revoked" | "error";
  is_active: boolean;
  daily_posts_count: number;
  last_sync_at?: string;
  created_at: string;
  updated_at?: string;
}

// ── Platform definitions ───────────────────────────────────────────────────────

const PLATFORMS: {
  id: PlatformId;
  name: string;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  color: string;
  maxAccounts: number;
}[] = [
  { id: "instagram", name: "Instagram", icon: Instagram, color: "#E4405F", maxAccounts: 3 },
  { id: "facebook",  name: "Facebook",  icon: Facebook,  color: "#1877F2", maxAccounts: 2 },
  { id: "tiktok",    name: "TikTok",    icon: Music,     color: "#000000", maxAccounts: 2 },
  { id: "linkedin",  name: "LinkedIn",  icon: Linkedin,  color: "#0A66C2", maxAccounts: 1 },
];

// ── Component ──────────────────────────────────────────────────────────────────

export default function AccountsPage() {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const loadConnectors = useCallback(async () => {
    const brandId = typeof window !== "undefined" ? localStorage.getItem("brand_id") : null;
    if (!brandId) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    try {
      const res = await connectorsApi.list(brandId);
      setConnectors(res.data ?? []);
    } catch {
      toast({
        title: "Erreur",
        description: "Impossible de charger les comptes connectés.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConnectors();
  }, [loadConnectors]);

  const handleRefresh = useCallback((_id: string) => {
    loadConnectors();
  }, [loadConnectors]);

  const handleDisconnect = useCallback((_id: string) => {
    loadConnectors();
  }, [loadConnectors]);

  // Group connectors by platform
  const connectorsByPlatform: Record<PlatformId, Connector[]> = {
    instagram: [],
    facebook: [],
    tiktok: [],
    linkedin: [],
  };
  for (const c of connectors) {
    if (connectorsByPlatform[c.platform]) {
      connectorsByPlatform[c.platform].push(c);
    }
  }

  return (
    <div className="space-y-8">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground tracking-tight">
            Mes comptes
          </h1>
          <p className="mt-1 text-muted-foreground">
            Gérez vos comptes de réseaux sociaux connectés
          </p>
        </div>

        <Button
          variant="gradient"
          onClick={() => setIsDialogOpen(true)}
          className="gap-2 shrink-0"
        >
          <Plus className="h-4 w-4" />
          Ajouter un compte
        </Button>
      </motion.div>

      {/* ── Platform sections ───────────────────────────────────────────────── */}
      {PLATFORMS.map((platform, index) => {
        const platformConnectors = connectorsByPlatform[platform.id];
        const count = platformConnectors.length;
        const Icon = platform.icon;

        return (
          <motion.div
            key={platform.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1, duration: 0.4 }}
          >
            <Card className="bg-white border border-gray-200/60 shadow-sm">
              {/* Section header */}
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className="flex h-9 w-9 items-center justify-center rounded-lg"
                      style={{ backgroundColor: `${platform.color}15` }}
                    >
                      <Icon
                        className="h-5 w-5"
                        style={{ color: platform.color }}
                      />
                    </div>
                    <CardTitle className="text-base font-semibold text-foreground">
                      {platform.name}
                    </CardTitle>
                  </div>

                  {/* Count badge: connected / max */}
                  {isLoading ? (
                    <Skeleton className="h-5 w-12 rounded-full" />
                  ) : (
                    <Badge
                      variant={count === 0 ? "secondary" : "outline"}
                      className="text-xs font-medium"
                    >
                      {count}/{platform.maxAccounts}
                    </Badge>
                  )}
                </div>
              </CardHeader>

              {/* Section body */}
              <CardContent>
                {isLoading ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    <Skeleton className="h-24 w-full rounded-xl" />
                    <Skeleton className="h-24 w-full rounded-xl" />
                  </div>
                ) : platformConnectors.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {platformConnectors.map((connector) => (
                      <AccountCard
                        key={connector.id}
                        connector={connector}
                        onDisconnect={handleDisconnect}
                        onRefresh={handleRefresh}
                      />
                    ))}
                  </div>
                ) : (
                  /* Empty state */
                  <div className="flex items-center gap-3 rounded-lg border border-dashed border-gray-200 bg-gray-50/60 px-4 py-5 text-sm text-muted-foreground">
                    <Link2 className="h-4 w-4 shrink-0 text-gray-400" />
                    <span>Aucun compte connecté pour cette plateforme.</span>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        );
      })}

      {/* ── Footer tooltip ──────────────────────────────────────────────────── */}
      <div className="flex items-center gap-1 text-xs text-muted-foreground">
        <Users className="h-3.5 w-3.5" />
        <span>Comptes connectés</span>
        <HelpTooltip content="Les comptes connectés sont utilisés pour publier du contenu sur vos réseaux sociaux." />
      </div>

      {/* ── Dialogs ─────────────────────────────────────────────────────────── */}
      <AddAccountDialog
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        brandId={typeof window !== "undefined" ? (localStorage.getItem("brand_id") ?? "") : ""}
        existingCounts={Object.fromEntries(
          Object.entries(connectorsByPlatform).map(([k, v]) => [k, v.length])
        )}
        onAccountAdded={loadConnectors}
      />
    </div>
  );
}
