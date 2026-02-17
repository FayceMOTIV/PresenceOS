"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Calendar,
  Send,
  BarChart3,
  Brain,
  Settings,
  Sparkles,
  LogOut,
  ChevronDown,
  PlusCircle,
  Building2,
  ChevronsUpDown,
  User as UserIcon,
  Loader2,
  Lightbulb,
  Bot,
  FileText,
  HelpCircle,
} from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { workspacesApi } from "@/lib/api";

const navigation = [
  { name: "🏠 Accueil", href: "/dashboard", icon: LayoutDashboard },
  { name: "✨ Créer un post", href: "/studio", icon: Sparkles },
  { name: "💡 Idées de posts", href: "/ideas", icon: Lightbulb },
  { name: "📊 Analyser Instagram", href: "/brain", icon: Brain },
  { name: "🤖 Mes Assistants", href: "/agents", icon: Bot },
  { name: "📅 Calendrier", href: "/planner", icon: Calendar },
  { name: "📝 Mes posts", href: "/posts", icon: FileText },
  { name: "🔗 Mes comptes", href: "/accounts", icon: UserIcon },
  { name: "❓ Aide", href: "/help", icon: HelpCircle },
  { name: "⚙️ Réglages", href: "/settings", icon: Settings },
];

const createAction = { name: "Créer", href: "/create", icon: PlusCircle };

interface SidebarProps {
  brands: Array<{ id: string; name: string; logo_url?: string }>;
  activeBrandId?: string;
  onBrandChange: (brandId: string) => void;
  workspaces?: Array<{ id: string; name: string; slug: string; logo_url?: string }>;
  activeWorkspaceId?: string;
  onWorkspaceChange?: (workspaceId: string) => void;
  currentUser?: { id: string; full_name: string; email: string; avatar_url?: string } | null;
}

export function Sidebar({ brands, activeBrandId, onBrandChange, workspaces, activeWorkspaceId, onWorkspaceChange, currentUser }: SidebarProps) {
  const pathname = usePathname();
  const activeBrand = brands.find((b) => b.id === activeBrandId) || brands[0];
  const activeWorkspace = workspaces?.find((ws) => ws.id === activeWorkspaceId) || workspaces?.[0];

  const [showCreateWs, setShowCreateWs] = useState(false);
  const [newWsName, setNewWsName] = useState("");
  const [isCreatingWs, setIsCreatingWs] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("workspace_id");
    localStorage.removeItem("brand_id");
    window.location.href = "/auth/login";
  };

  return (
    <div className="flex h-full flex-col bg-white/80 backdrop-blur-xl border-r border-gray-200/60">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 px-6 border-b border-gray-100/80">
        <div className="w-9 h-9 rounded-xl gradient-bg flex items-center justify-center shadow-glow-sm animate-float">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <span className="text-lg font-bold gradient-text">
          PresenceOS
        </span>
      </div>

      {/* Workspace Selector */}
      {workspaces && workspaces.length > 0 && (
        <div className="px-4 pb-2 pt-3 border-b border-gray-100/80">
          <p className="text-[10px] uppercase tracking-wider text-gray-400 font-medium px-1 mb-1">🍽️ MON RESTAURANT</p>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="w-full justify-between text-left font-normal h-10 hover:bg-gray-50/80 transition-all duration-200"
              >
                <div className="flex items-center gap-2.5 truncate">
                  <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center text-xs font-semibold text-gray-600">
                    <Building2 className="w-3.5 h-3.5" />
                  </div>
                  <span className="truncate text-sm font-medium">{activeWorkspace?.name}</span>
                </div>
                <ChevronsUpDown className="w-3.5 h-3.5 text-gray-400" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-56">
              {workspaces.map((ws) => (
                <DropdownMenuItem
                  key={ws.id}
                  onClick={() => onWorkspaceChange?.(ws.id)}
                  className={cn(ws.id === activeWorkspaceId && "bg-violet-50 text-violet-700")}
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center text-xs font-semibold text-gray-600">
                      {ws.name.charAt(0)}
                    </div>
                    <span>{ws.name}</span>
                  </div>
                </DropdownMenuItem>
              ))}
              <DropdownMenuItem asChild>
                <Link href="#" onClick={(e) => { e.preventDefault(); setShowCreateWs(true); }} className="text-violet-600 font-medium">
                  + Ajouter un espace
                </Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      )}

      {/* Brand Selector */}
      {brands.length > 0 && (
        <div className="p-4 border-b border-gray-100/80">
          <p className="text-[10px] uppercase tracking-wider text-gray-400 font-medium px-1 mb-1">✨ MA MARQUE</p>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-between text-left font-normal h-11 border-gray-200/80 hover:bg-violet-50/50 hover:border-violet-200/60 transition-all duration-200"
              >
                <div className="flex items-center gap-2.5 truncate">
                  {activeBrand?.logo_url ? (
                    <img
                      src={activeBrand.logo_url}
                      alt={activeBrand.name}
                      className="w-7 h-7 rounded-lg object-cover ring-2 ring-violet-100"
                    />
                  ) : (
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-100 to-purple-100 flex items-center justify-center text-xs font-semibold text-violet-700 ring-2 ring-violet-50">
                      {activeBrand?.name?.charAt(0)}
                    </div>
                  )}
                  <span className="truncate text-sm font-medium">{activeBrand?.name}</span>
                </div>
                <ChevronDown className="w-4 h-4 text-gray-400" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-56">
              {brands.map((brand) => (
                <DropdownMenuItem
                  key={brand.id}
                  onClick={() => onBrandChange(brand.id)}
                  className={cn(brand.id === activeBrandId && "bg-violet-50 text-violet-700")}
                >
                  <div className="flex items-center gap-2.5">
                    {brand.logo_url ? (
                      <img
                        src={brand.logo_url}
                        alt={brand.name}
                        className="w-6 h-6 rounded-lg object-cover"
                      />
                    ) : (
                      <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-violet-100 to-purple-100 flex items-center justify-center text-xs font-semibold text-violet-700">
                        {brand.name.charAt(0)}
                      </div>
                    )}
                    <span>{brand.name}</span>
                  </div>
                </DropdownMenuItem>
              ))}
              <DropdownMenuItem asChild>
                <Link href="/brands/new" className="text-violet-600 font-medium">
                  + Ajouter une marque
                </Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      )}

      {/* Create Button */}
      <div className="px-3 pt-4 pb-2">
        <Link
          href={createAction.href}
          className={cn(
            "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-all duration-300",
            pathname === createAction.href || pathname.startsWith(createAction.href + "/")
              ? "gradient-bg text-white shadow-lg shadow-purple-500/25"
              : "bg-gradient-to-r from-violet-50 to-purple-50 text-violet-700 border border-violet-200/60 hover:from-violet-100 hover:to-purple-100 hover:shadow-md hover:shadow-purple-500/10"
          )}
        >
          <createAction.icon className={cn(
            "w-5 h-5 transition-transform duration-300",
            pathname !== createAction.href && "group-hover:rotate-90"
          )} />
          {createAction.name}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-0.5 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-gradient-to-r from-violet-50 to-purple-50/80 text-violet-700 shadow-sm shadow-purple-500/[0.05]"
                  : "text-gray-500 hover:bg-gray-50/80 hover:text-gray-900"
              )}
            >
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-full gradient-bg" />
              )}
              <item.icon className={cn(
                "w-5 h-5 transition-colors duration-200",
                isActive ? "text-violet-600" : "text-gray-400 group-hover:text-gray-600"
              )} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="border-t border-gray-100/80">
        {/* User Section */}
        {currentUser && (
          <div className="px-3 pt-3 pb-2">
            <Link
              href="/settings"
              className="group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-gray-500 hover:bg-gray-50/80 hover:text-gray-900 transition-all duration-200"
            >
              {currentUser.avatar_url ? (
                <img src={currentUser.avatar_url} alt={currentUser.full_name} className="w-7 h-7 rounded-full object-cover" />
              ) : (
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-100 to-purple-100 flex items-center justify-center text-xs font-semibold text-violet-700">
                  {currentUser.full_name?.charAt(0) || "?"}
                </div>
              )}
              <div className="truncate">
                <p className="text-sm font-medium text-gray-700 group-hover:text-gray-900 truncate">{currentUser.full_name}</p>
                <p className="text-xs text-gray-400 truncate">{currentUser.email}</p>
              </div>
            </Link>
          </div>
        )}

        {/* Logout Button */}
        <div className="px-3 pb-4 pt-2">
          <button
            onClick={handleLogout}
            className="group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-gray-400 hover:bg-red-50/80 hover:text-red-500 transition-all duration-200"
          >
            <LogOut className="w-5 h-5 group-hover:text-red-400 transition-colors" />
            Déconnexion
          </button>
        </div>
      </div>

      {/* Create Workspace Dialog */}
      <Dialog open={showCreateWs} onOpenChange={setShowCreateWs}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Ajouter un nouvel espace</DialogTitle>
            <p className="text-sm text-muted-foreground">
              Créez un nouvel espace pour gérer une autre activité. Chaque espace a son propre calendrier et ses propres posts.
            </p>
          </DialogHeader>
          <form onSubmit={async (e) => {
            e.preventDefault();
            if (!newWsName.trim()) return;
            setIsCreatingWs(true);
            try {
              const slug = newWsName.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
              const res = await workspacesApi.create({ name: newWsName.trim(), slug });
              localStorage.setItem("workspace_id", res.data.id);
              localStorage.removeItem("brand_id");
              window.location.href = "/dashboard";
            } catch (err: any) {
              // handle error with toast if available
            } finally {
              setIsCreatingWs(false);
            }
          }} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="ws-name">Nom de votre activité</Label>
              <Input id="ws-name" placeholder="Ex: Mon Restaurant, Ma Boutique..." value={newWsName} onChange={(e) => setNewWsName(e.target.value)} required />
            </div>
            <Button type="submit" variant="gradient" className="w-full" disabled={isCreatingWs}>
              {isCreatingWs ? <Loader2 className="w-4 h-4 animate-spin" /> : "Créer"}
            </Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
