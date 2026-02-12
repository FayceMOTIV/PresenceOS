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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "AI Studio", href: "/studio", icon: Sparkles },
  { name: "Planner", href: "/planner", icon: Calendar },
  { name: "Posts", href: "/posts", icon: Send },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Brain", href: "/brain", icon: Brain },
  { name: "Settings", href: "/settings", icon: Settings },
];

const createAction = { name: "Creer", href: "/create", icon: PlusCircle };

interface SidebarProps {
  brands: Array<{ id: string; name: string; logo_url?: string }>;
  activeBrandId?: string;
  onBrandChange: (brandId: string) => void;
}

export function Sidebar({ brands, activeBrandId, onBrandChange }: SidebarProps) {
  const pathname = usePathname();
  const activeBrand = brands.find((b) => b.id === activeBrandId) || brands[0];

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("workspace_id");
    localStorage.removeItem("brand_id");
    window.location.href = "/auth/login";
  };

  return (
    <div className="flex h-full flex-col glass border-r">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 px-6 border-b">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <span className="text-lg font-bold">PresenceOS</span>
      </div>

      {/* Brand Selector */}
      {brands.length > 0 && (
        <div className="p-4 border-b">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-between text-left font-normal"
              >
                <div className="flex items-center gap-2 truncate">
                  {activeBrand?.logo_url ? (
                    <img
                      src={activeBrand.logo_url}
                      alt={activeBrand.name}
                      className="w-6 h-6 rounded"
                    />
                  ) : (
                    <div className="w-6 h-6 rounded bg-muted flex items-center justify-center text-xs font-medium">
                      {activeBrand?.name?.charAt(0)}
                    </div>
                  )}
                  <span className="truncate">{activeBrand?.name}</span>
                </div>
                <ChevronDown className="w-4 h-4 opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-56">
              {brands.map((brand) => (
                <DropdownMenuItem
                  key={brand.id}
                  onClick={() => onBrandChange(brand.id)}
                  className={cn(brand.id === activeBrandId && "bg-accent")}
                >
                  <div className="flex items-center gap-2">
                    {brand.logo_url ? (
                      <img
                        src={brand.logo_url}
                        alt={brand.name}
                        className="w-6 h-6 rounded"
                      />
                    ) : (
                      <div className="w-6 h-6 rounded bg-muted flex items-center justify-center text-xs font-medium">
                        {brand.name.charAt(0)}
                      </div>
                    )}
                    <span>{brand.name}</span>
                  </div>
                </DropdownMenuItem>
              ))}
              <DropdownMenuItem asChild>
                <Link href="/brands/new" className="text-primary">
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
            "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-all",
            pathname === createAction.href || pathname.startsWith(createAction.href + "/")
              ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
              : "bg-gradient-to-r from-amber-500/10 to-orange-500/10 text-primary border border-primary/20 hover:from-amber-500/20 hover:to-orange-500/20"
          )}
        >
          <createAction.icon className="w-5 h-5" />
          {createAction.name}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <item.icon className="w-5 h-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="border-t px-3 py-4">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <LogOut className="w-5 h-5" />
          Deconnexion
        </button>
      </div>
    </div>
  );
}
