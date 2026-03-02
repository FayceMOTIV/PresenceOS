// PresenceOS Mobile — Brand Store (Zustand)
// Manages multi-brand state + persists active brand ID to SecureStore

import { create } from "zustand";
import * as SecureStore from "expo-secure-store";
import type { Brand } from "@/types";

const ACTIVE_BRAND_KEY = "active_brand_id";

interface BrandStore {
  brands: Brand[];
  activeBrand: Brand | null;
  isLoading: boolean;

  // Actions
  setBrands: (brands: Brand[]) => void;
  switchBrand: (brandId: string) => void;
  loadBrands: (brands: Brand[]) => Promise<void>;
  reset: () => void;
}

export const useBrandStore = create<BrandStore>((set, get) => ({
  brands: [],
  activeBrand: null,
  isLoading: true,

  setBrands: (brands) => {
    set({ brands });
  },

  switchBrand: (brandId) => {
    const { brands } = get();
    const found = brands.find((b) => b.id === brandId);
    if (found) {
      set({ activeBrand: found });
      // Persist choice
      SecureStore.setItemAsync(ACTIVE_BRAND_KEY, brandId).catch(() => {});
    }
  },

  loadBrands: async (brands) => {
    if (brands.length === 0) {
      set({ brands: [], activeBrand: null, isLoading: false });
      return;
    }

    // Try to restore previously selected brand
    let savedId: string | null = null;
    try {
      savedId = await SecureStore.getItemAsync(ACTIVE_BRAND_KEY);
    } catch {}

    const restored = savedId ? brands.find((b) => b.id === savedId) : null;
    const active = restored || brands[0];

    set({ brands, activeBrand: active, isLoading: false });

    // Persist in case we picked the first one
    if (active) {
      SecureStore.setItemAsync(ACTIVE_BRAND_KEY, active.id).catch(() => {});
    }
  },

  reset: () => {
    set({ brands: [], activeBrand: null, isLoading: true });
    SecureStore.deleteItemAsync(ACTIVE_BRAND_KEY).catch(() => {});
  },
}));
