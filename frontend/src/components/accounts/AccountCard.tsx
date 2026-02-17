"use client";

import { motion } from "framer-motion";
import {
  Instagram,
  Facebook,
  Linkedin,
  RefreshCw,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Clock,
} from "lucide-react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

// --- Types ---

interface Connector {
  id: string;
  brand_id: string;
  platform: "instagram" | "tiktok" | "linkedin" | "facebook";
  account_username?: string;
  account_avatar_url?: string;
  status: "connected" | "expired" | "revoked" | "error";
  is_active: boolean;
  daily_posts_count: number;
  last_sync_at?: string;
  created_at: string;
}

interface AccountCardProps {
  connector: Connector;
  onRefresh: (id: string) => void;
  onDisconnect: (id: string) => void;
}

// --- Platform config ---

const PLATFORM_CONFIG: Record<
  Connector["platform"],
  { label: string; color: string; bgColor: string; icon: React.ReactNode }
> = {
  instagram: {
    label: "Instagram",
    color: "#E4405F",
    bgColor: "rgba(228, 64, 95, 0.08)",
    icon: <Instagram size={22} />,
  },
  tiktok: {
    label: "TikTok",
    color: "#000000",
    bgColor: "rgba(0, 0, 0, 0.06)",
    icon: (
      <svg
        width="22"
        height="22"
        viewBox="0 0 24 24"
        fill="currentColor"
        aria-label="TikTok"
      >
        <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.32 6.32 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.18 8.18 0 0 0 4.78 1.52V6.77a4.85 4.85 0 0 1-1.01-.08z" />
      </svg>
    ),
  },
  linkedin: {
    label: "LinkedIn",
    color: "#0A66C2",
    bgColor: "rgba(10, 102, 194, 0.08)",
    icon: <Linkedin size={22} />,
  },
  facebook: {
    label: "Facebook",
    color: "#1877F2",
    bgColor: "rgba(24, 119, 242, 0.08)",
    icon: <Facebook size={22} />,
  },
};

// --- Status config ---

const STATUS_CONFIG: Record<
  Connector["status"],
  { label: string; className: string; icon: React.ReactNode }
> = {
  connected: {
    label: "Connecté",
    className:
      "border-transparent bg-emerald-100 text-emerald-700 hover:bg-emerald-100",
    icon: <CheckCircle2 size={11} />,
  },
  expired: {
    label: "Expiré",
    className:
      "border-transparent bg-amber-100 text-amber-700 hover:bg-amber-100",
    icon: <Clock size={11} />,
  },
  error: {
    label: "Erreur",
    className: "border-transparent bg-red-100 text-red-700 hover:bg-red-100",
    icon: <AlertCircle size={11} />,
  },
  revoked: {
    label: "Révoqué",
    className:
      "border-transparent bg-gray-100 text-gray-500 hover:bg-gray-100",
    icon: <AlertCircle size={11} />,
  },
};

// --- Helpers ---

function formatDate(dateStr: string): string {
  try {
    return format(new Date(dateStr), "d MMM yyyy", { locale: fr });
  } catch {
    return "—";
  }
}

// --- Component ---

export function AccountCard({ connector, onRefresh, onDisconnect }: AccountCardProps) {
  const platform = PLATFORM_CONFIG[connector.platform];
  const statusCfg = STATUS_CONFIG[connector.status];
  const showRefresh =
    connector.status === "expired" || connector.status === "error";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <Card className="rounded-2xl border border-gray-200/70 bg-white shadow-sm hover:shadow-md transition-shadow duration-300">
        <CardContent className="p-5">
          {/* Top row: icon + username + status badge */}
          <div className="flex items-start gap-3">
            {/* Platform icon */}
            <div
              className="flex items-center justify-center rounded-xl p-2.5 flex-shrink-0"
              style={{
                color: platform.color,
                backgroundColor: platform.bgColor,
              }}
            >
              {platform.icon}
            </div>

            {/* Username + platform label */}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-gray-900 truncate">
                {connector.account_username
                  ? `@${connector.account_username}`
                  : platform.label}
              </p>
              <p className="text-xs text-gray-400 mt-0.5">{platform.label}</p>
            </div>

            {/* Status badge */}
            <Badge
              className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full flex-shrink-0 ${statusCfg.className}`}
            >
              {statusCfg.icon}
              {statusCfg.label}
            </Badge>
          </div>

          {/* Separator */}
          <div className="my-4 h-px bg-gray-100" />

          {/* Stats row */}
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>
              <span className="font-medium text-gray-700">
                {connector.daily_posts_count}
              </span>{" "}
              post{connector.daily_posts_count !== 1 ? "s" : ""} aujourd&apos;hui
            </span>
            <span>
              Connecté depuis{" "}
              <span className="font-medium text-gray-700">
                {formatDate(connector.created_at)}
              </span>
            </span>
          </div>

          {/* Actions */}
          {(showRefresh || true) && (
            <div className="flex items-center gap-2 mt-4">
              {showRefresh && (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 gap-1.5 text-xs border-amber-300 text-amber-700 hover:bg-amber-50 hover:border-amber-400"
                  onClick={() => onRefresh(connector.id)}
                >
                  <RefreshCw size={12} />
                  Actualiser
                </Button>
              )}

              <div className="ml-auto">
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 gap-1.5 text-xs text-red-500 hover:text-red-600 hover:bg-red-50"
                    >
                      <Trash2 size={12} />
                      Déconnecter
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent className="rounded-2xl">
                    <AlertDialogHeader>
                      <AlertDialogTitle>
                        Déconnecter ce compte ?
                      </AlertDialogTitle>
                      <AlertDialogDescription>
                        Le compte{" "}
                        <span className="font-semibold text-gray-900">
                          {connector.account_username
                            ? `@${connector.account_username}`
                            : platform.label}
                        </span>{" "}
                        sera déconnecté de PresenceOS. Vous pourrez le
                        reconnecter à tout moment.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel className="rounded-xl">
                        Annuler
                      </AlertDialogCancel>
                      <AlertDialogAction
                        className="rounded-xl bg-red-600 hover:bg-red-700 text-white"
                        onClick={() => onDisconnect(connector.id)}
                      >
                        Déconnecter
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default AccountCard;
