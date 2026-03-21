// PresenceOS Mobile — Onboarding Store (Zustand + SecureStore)
// Sprint 7: Backend-first check to handle cross-device login

import { create } from "zustand";
import * as SecureStore from "expo-secure-store";
import { onboardingApi } from "@/lib/api";

const STORE_KEY = "onboarding_completed";

interface OnboardingState {
  completed: boolean;
  step: number;
  setStep: (step: number) => void;
  markCompleted: () => Promise<void>;
  checkCompleted: (brandId?: string) => Promise<boolean>;
}

export const useOnboardingStore = create<OnboardingState>((set) => ({
  completed: false,
  step: 0,

  setStep: (step: number) => set({ step }),

  markCompleted: async () => {
    await SecureStore.setItemAsync(STORE_KEY, "true");
    set({ completed: true });
  },

  checkCompleted: async (brandId?: string) => {
    // 1. Try backend first (handles cross-device login)
    if (brandId) {
      try {
        const res = await onboardingApi.getState(brandId);
        if (res.data?.is_complete) {
          // Backend says completed — sync to local SecureStore
          await SecureStore.setItemAsync(STORE_KEY, "true");
          set({ completed: true });
          return true;
        }
      } catch {
        // Backend unreachable — fall through to local check
      }
    }

    // 2. Fallback: local SecureStore (original behavior)
    try {
      const val = await SecureStore.getItemAsync(STORE_KEY);
      const done = val === "true";
      set({ completed: done });
      return done;
    } catch {
      return false;
    }
  },
}));
