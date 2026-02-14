"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { DegradedBanner } from "@/components/DegradedBanner";
import { workspacesApi, authApi, usersApi } from "@/lib/api";
import { Brand, Workspace, User } from "@/types";
import { Loader2 } from "lucide-react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { InteractiveTour } from "@/components/onboarding/interactive-tour";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [brands, setBrands] = useState<Brand[]>([]);
  const [activeBrandId, setActiveBrandId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDegraded, setIsDegraded] = useState(false);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/auth/login");
      return;
    }

    const workspaceId = localStorage.getItem("workspace_id");

    if (!workspaceId) {
      router.push("/onboarding");
      return;
    }

    // Set active workspace from localStorage
    setActiveWorkspaceId(workspaceId);

    // Fetch user + workspaces in parallel with brands
    Promise.all([
      authApi.me().catch(() => null),
      usersApi.getMyWorkspaces().catch(() => ({ data: [] })),
      workspacesApi.getBrands(workspaceId).catch(() => ({ data: [] })),
    ]).then(([userRes, wsRes, brandsRes]) => {
      if (userRes?.data) setCurrentUser(userRes.data);
      if (wsRes?.data) setWorkspaces(wsRes.data);

      const data = brandsRes.data;
      if (Array.isArray(data) && data.length > 0 && data[0]?.degraded) {
        setIsDegraded(true);
      }
      setBrands(data);
      const savedBrandId = localStorage.getItem("brand_id");
      if (savedBrandId && data.find((b: Brand) => b.id === savedBrandId)) {
        setActiveBrandId(savedBrandId);
      } else if (data.length > 0) {
        setActiveBrandId(data[0].id);
        localStorage.setItem("brand_id", data[0].id);
      }

      setIsLoading(false);
    }).catch(() => {
      setIsDegraded(true);
      setBrands([]);
      setIsLoading(false);
    });
  }, [router]);

  const handleBrandChange = (brandId: string) => {
    setActiveBrandId(brandId);
    localStorage.setItem("brand_id", brandId);
  };

  const handleWorkspaceChange = (workspaceId: string) => {
    setActiveWorkspaceId(workspaceId);
    localStorage.setItem("workspace_id", workspaceId);
    localStorage.removeItem("brand_id");
    setActiveBrandId(null);
    setBrands([]);

    workspacesApi
      .getBrands(workspaceId)
      .then((response) => {
        const data = response.data;
        setBrands(data);
        if (data.length > 0) {
          setActiveBrandId(data[0].id);
          localStorage.setItem("brand_id", data[0].id);
        }
      })
      .catch(() => {
        setIsDegraded(true);
        setBrands([]);
      });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-mesh-gradient">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-2xl gradient-bg flex items-center justify-center shadow-glow-sm animate-pulse-soft">
            <Loader2 className="w-6 h-6 animate-spin text-white" />
          </div>
          <span className="text-sm text-muted-foreground">Chargement...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50/80 via-white to-violet-50/30">
      <aside className="w-64 flex-shrink-0">
        <Sidebar
          brands={brands}
          activeBrandId={activeBrandId || undefined}
          onBrandChange={handleBrandChange}
          workspaces={workspaces}
          activeWorkspaceId={activeWorkspaceId || undefined}
          onWorkspaceChange={handleWorkspaceChange}
          currentUser={currentUser}
        />
      </aside>
      <main className="flex-1 overflow-auto">
        <DegradedBanner degraded={isDegraded} />
        <div className="p-8">
          <Breadcrumbs />
          {children}
        </div>
      </main>
      <InteractiveTour />
    </div>
  );
}
