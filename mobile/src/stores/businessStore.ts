// PresenceOS Mobile — Business Store (Zustand + Backend API)
// Fetches brands from PostgreSQL via /api/v2/me/brands.
// PostgreSQL brand IDs are the source of truth for all API calls.

import { create } from "zustand";
import * as SecureStore from "expo-secure-store";
import type { Brand } from "@/types";
import { brandsV2Api } from "@/lib/api";

const ACTIVE_BIZ_KEY = "active_business_id";

interface BusinessState {
  brands: Brand[];
  activeBrand: Brand | null;
  isLoading: boolean;
  error: string | null;
}

interface BusinessActions {
  fetchBrands: () => Promise<void>;
  switchBusiness: (bizId: string) => void;
  getActiveBrand: () => Brand | null;
  getBrands: () => Brand[];
  reset: () => void;
}

type BusinessStore = BusinessState & BusinessActions;

export const useBusinessStore = create<BusinessStore>((set, get) => ({
  brands: [],
  activeBrand: null,
  isLoading: true,
  error: null,

  fetchBrands: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await brandsV2Api.mine();
      const brands: Brand[] = (res.data.brands ?? []).map((b: any) => ({
        id: b.id,
        name: b.name,
        slug: b.slug,
        brand_type: b.brand_type,
        description: b.description,
        logo_url: b.logo_url,
      }));

      // Restore previously selected brand
      let savedId: string | null = null;
      try {
        savedId = await SecureStore.getItemAsync(ACTIVE_BIZ_KEY);
      } catch {}

      const restored = savedId ? brands.find((b) => b.id === savedId) : null;
      const activeBrand = restored || brands[0] || null;

      set({ brands, activeBrand, isLoading: false });

      if (activeBrand) {
        SecureStore.setItemAsync(ACTIVE_BIZ_KEY, activeBrand.id).catch(() => {});
      }
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.message || "Erreur chargement des marques",
      });
    }
  },

  switchBusiness: (bizId) => {
    const { brands } = get();
    const found = brands.find((b) => b.id === bizId);
    if (found) {
      set({ activeBrand: found });
      SecureStore.setItemAsync(ACTIVE_BIZ_KEY, bizId).catch(() => {});
    }
  },

  getActiveBrand: () => get().activeBrand,
  getBrands: () => get().brands,

  reset: () => {
    set({
      brands: [],
      activeBrand: null,
      isLoading: true,
      error: null,
    });
    SecureStore.deleteItemAsync(ACTIVE_BIZ_KEY).catch(() => {});
  },
}));
