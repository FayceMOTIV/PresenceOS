// PresenceOS Mobile — Onboarding Store (Zustand + SecureStore)

import { create } from "zustand";
import * as SecureStore from "expo-secure-store";

const STORE_KEY = "onboarding_completed";

interface OnboardingState {
  completed: boolean;
  step: number;
  setStep: (step: number) => void;
  markCompleted: () => Promise<void>;
  checkCompleted: () => Promise<boolean>;
}

export const useOnboardingStore = create<OnboardingState>((set) => ({
  completed: false,
  step: 0,

  setStep: (step: number) => set({ step }),

  markCompleted: async () => {
    await SecureStore.setItemAsync(STORE_KEY, "true");
    set({ completed: true });
  },

  checkCompleted: async () => {
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
