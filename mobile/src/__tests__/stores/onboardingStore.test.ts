/**
 * Tests du Onboarding Store
 */

import * as SecureStore from "expo-secure-store";
import { useOnboardingStore } from "@/stores/onboardingStore";

beforeEach(() => {
  useOnboardingStore.setState({ completed: false, step: 0 });
  jest.clearAllMocks();
});

describe("OnboardingStore", () => {
  test("état initial: completed=false, step=0", () => {
    const state = useOnboardingStore.getState();
    expect(state.completed).toBe(false);
    expect(state.step).toBe(0);
  });

  test("setStep met à jour le step", () => {
    useOnboardingStore.getState().setStep(2);
    expect(useOnboardingStore.getState().step).toBe(2);
  });

  test("markCompleted persiste et met completed=true", async () => {
    await useOnboardingStore.getState().markCompleted();

    expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
      "onboarding_completed",
      "true"
    );
    expect(useOnboardingStore.getState().completed).toBe(true);
  });

  test("checkCompleted retourne true si SecureStore a 'true'", async () => {
    (SecureStore.getItemAsync as jest.Mock).mockResolvedValue("true");

    const result = await useOnboardingStore.getState().checkCompleted();

    expect(result).toBe(true);
    expect(useOnboardingStore.getState().completed).toBe(true);
  });

  test("checkCompleted retourne false si SecureStore est vide", async () => {
    (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(null);

    const result = await useOnboardingStore.getState().checkCompleted();

    expect(result).toBe(false);
    expect(useOnboardingStore.getState().completed).toBe(false);
  });

  test("checkCompleted retourne false en cas d'erreur", async () => {
    (SecureStore.getItemAsync as jest.Mock).mockRejectedValue(
      new Error("SecureStore error")
    );

    const result = await useOnboardingStore.getState().checkCompleted();

    expect(result).toBe(false);
  });
});
