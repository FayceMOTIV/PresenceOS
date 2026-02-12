"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { DegradedBanner } from "@/components/DegradedBanner";
import { workspacesApi } from "@/lib/api";
import { Brand } from "@/types";
import { Loader2 } from "lucide-react";

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

  useEffect(() => {
    // AUTH DISABLED FOR TESTING
    const workspaceId = localStorage.getItem("workspace_id");

    if (workspaceId) {
      // Try loading real brands
      workspacesApi
        .getBrands(workspaceId)
        .then((response) => {
          const data = response.data;
          // Detect degraded mode from API response
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
        })
        .catch(() => {
          // Fallback to mock brand
          setIsDegraded(true);
          const mock = [{ id: "test-brand", name: "Test Brand" }];
          setBrands(mock as Brand[]);
          setActiveBrandId("test-brand");
        })
        .finally(() => setIsLoading(false));
    } else {
      // No workspace — use mock data
      setIsDegraded(true);
      const mock = [{ id: "test-brand", name: "Test Brand" }];
      setBrands(mock as Brand[]);
      setActiveBrandId("test-brand");
      setIsLoading(false);
    }
  }, [router]);

  const handleBrandChange = (brandId: string) => {
    setActiveBrandId(brandId);
    localStorage.setItem("brand_id", brandId);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-background">
      <aside className="w-64 flex-shrink-0">
        <Sidebar
          brands={brands}
          activeBrandId={activeBrandId || undefined}
          onBrandChange={handleBrandChange}
        />
      </aside>
      <main className="flex-1 overflow-auto">
        <DegradedBanner degraded={isDegraded} />
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
