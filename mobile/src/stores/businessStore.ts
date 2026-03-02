// PresenceOS Mobile — Business Store (Zustand + Firestore)
// Replaces brandStore for Firestore-backed business management.
// Maps Firestore businesses to v1-compatible Brand objects.

import { create } from "zustand";
import * as SecureStore from "expo-secure-store";
import type { Brand } from "@/types";
import {
  subscribeToMyBusinesses,
  FirestoreBusiness,
} from "@/services/businessService";
import type { Unsubscribe } from "firebase/firestore";

const ACTIVE_BIZ_KEY = "active_business_id";

/** Convert a Firestore business to a v1-compatible Brand object. */
function toBrand(biz: FirestoreBusiness): Brand {
  return {
    id: biz.id,
    name: biz.name,
    slug: biz.slug,
    brand_type: biz.businessType,
    description: biz.description,
    logo_url: biz.logoUrl,
  };
}

interface BusinessState {
  businesses: FirestoreBusiness[];
  activeBusiness: FirestoreBusiness | null;
  isLoading: boolean;

  // v1-compat accessors (computed)
  brands: Brand[];
  activeBrand: Brand | null;
}

interface BusinessActions {
  startListening: (uid: string) => void;
  stopListening: () => void;
  switchBusiness: (bizId: string) => void;
  getActiveBrand: () => Brand | null;
  getBrands: () => Brand[];
  reset: () => void;
}

type BusinessStore = BusinessState & BusinessActions;

let _unsubscribe: Unsubscribe | null = null;

export const useBusinessStore = create<BusinessStore>((set, get) => ({
  businesses: [],
  activeBusiness: null,
  isLoading: true,
  brands: [],
  activeBrand: null,

  startListening: (uid) => {
    // Prevent duplicate listeners
    if (_unsubscribe) _unsubscribe();

    _unsubscribe = subscribeToMyBusinesses(uid, async (businesses) => {
      const active = businesses.filter((b) => b.isActive);

      // Restore previously selected business
      let savedId: string | null = null;
      try {
        savedId = await SecureStore.getItemAsync(ACTIVE_BIZ_KEY);
      } catch {}

      const restored = savedId
        ? active.find((b) => b.id === savedId)
        : null;
      const activeBiz = restored || active[0] || null;

      set({
        businesses: active,
        activeBusiness: activeBiz,
        isLoading: false,
        brands: active.map(toBrand),
        activeBrand: activeBiz ? toBrand(activeBiz) : null,
      });

      // Persist active choice
      if (activeBiz) {
        SecureStore.setItemAsync(ACTIVE_BIZ_KEY, activeBiz.id).catch(() => {});
      }
    });
  },

  stopListening: () => {
    if (_unsubscribe) {
      _unsubscribe();
      _unsubscribe = null;
    }
  },

  switchBusiness: (bizId) => {
    const { businesses } = get();
    const found = businesses.find((b) => b.id === bizId);
    if (found) {
      set({
        activeBusiness: found,
        activeBrand: toBrand(found),
      });
      SecureStore.setItemAsync(ACTIVE_BIZ_KEY, bizId).catch(() => {});
    }
  },

  getActiveBrand: () => {
    const { activeBusiness } = get();
    return activeBusiness ? toBrand(activeBusiness) : null;
  },

  getBrands: () => {
    const { businesses } = get();
    return businesses.map(toBrand);
  },

  reset: () => {
    if (_unsubscribe) {
      _unsubscribe();
      _unsubscribe = null;
    }
    set({
      businesses: [],
      activeBusiness: null,
      isLoading: true,
      brands: [],
      activeBrand: null,
    });
    SecureStore.deleteItemAsync(ACTIVE_BIZ_KEY).catch(() => {});
  },
}));
