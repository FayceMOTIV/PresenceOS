// PresenceOS Mobile — Brand Hook

import { useState, useEffect, useCallback } from "react";
import * as SecureStore from "expo-secure-store";
import api from "@/lib/api";
import { Brand } from "@/types";

export function useBrand() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [activeBrand, setActiveBrand] = useState<Brand | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadBrands();
  }, []);

  const loadBrands = async () => {
    try {
      const res = await api.get("/brands");
      const brandList = res.data.brands || res.data;
      setBrands(brandList);

      const savedId = await SecureStore.getItemAsync("brand_id");
      const active = brandList.find((b: Brand) => b.id === savedId) || brandList[0];
      if (active) {
        setActiveBrand(active);
        await SecureStore.setItemAsync("brand_id", active.id);
      }
    } catch {
      // silently fail
    } finally {
      setIsLoading(false);
    }
  };

  const switchBrand = useCallback(async (brandId: string) => {
    const brand = brands.find((b) => b.id === brandId);
    if (brand) {
      setActiveBrand(brand);
      await SecureStore.setItemAsync("brand_id", brandId);
    }
  }, [brands]);

  return { brands, activeBrand, isLoading, switchBrand };
}
