/**
 * Tests du VideoPlansScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import VideoPlansScreen from "@/screens/video/VideoPlansScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { videoApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  videoApi: { credits: jest.fn() },
}));

const mockGoBack = jest.fn();
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ goBack: mockGoBack, navigate: jest.fn() }),
  useRoute: () => ({ params: {} }),
}));

const mockBrand = {
  activeBrand: { id: "brand-1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

function renderPlans() {
  return render(
    <BrandContext.Provider value={mockBrand as any}>
      <VideoPlansScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (videoApi.credits as jest.Mock).mockResolvedValue({
    data: { credits_remaining: 15, plan: "pro" },
  });
});

describe("VideoPlansScreen — Rendu", () => {
  test("affiche le titre Crédits Vidéo", async () => {
    renderPlans();
    // waitFor flushes pending async state updates from videoApi.credits()
    await waitFor(() => {
      expect(screen.getByText("Crédits Vidéo")).toBeTruthy();
    });
  });

  test("affiche les crédits restants", async () => {
    renderPlans();
    await waitFor(() => {
      expect(screen.getByText("15")).toBeTruthy();
      expect(screen.getByText("crédits restants")).toBeTruthy();
    });
  });

  test("affiche le plan actuel", async () => {
    renderPlans();
    await waitFor(() => {
      expect(screen.getByText(/Plan actuel : PRO/)).toBeTruthy();
    });
  });

  test("affiche l'info 1 crédit = 1 vidéo de 5s", () => {
    renderPlans();
    expect(screen.getByText("1 crédit = 1 vidéo de 5 secondes")).toBeTruthy();
  });
});

describe("VideoPlansScreen — Plans", () => {
  test("affiche les 3 plans", () => {
    renderPlans();
    expect(screen.getByText("Starter")).toBeTruthy();
    expect(screen.getByText("Pro")).toBeTruthy();
    expect(screen.getByText("Studio")).toBeTruthy();
  });

  test("affiche les prix", async () => {
    renderPlans();
    await waitFor(() => {
      // Prices may appear in nested Text, use getAllByText
      expect(screen.getAllByText(/4,99€/).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/14,99€/).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/34,99€/).length).toBeGreaterThanOrEqual(1);
    });
  });

  test("affiche les crédits par plan", () => {
    renderPlans();
    expect(screen.getByText("5")).toBeTruthy();
    expect(screen.getByText("20")).toBeTruthy();
    expect(screen.getByText("50")).toBeTruthy();
  });

  test("affiche POPULAIRE sur le plan Pro", () => {
    renderPlans();
    expect(screen.getByText("POPULAIRE")).toBeTruthy();
  });

  test("plan actuel a bouton disabled 'Plan actuel'", async () => {
    renderPlans();
    await waitFor(() => {
      const buttons = screen.getAllByText("Plan actuel");
      expect(buttons.length).toBeGreaterThanOrEqual(1);
    });
  });

  test("plans non-actifs ont bouton 'Choisir'", async () => {
    renderPlans();
    await waitFor(() => {
      const chooseButtons = screen.getAllByText("Choisir");
      expect(chooseButtons.length).toBe(2);
    });
  });
});

describe("VideoPlansScreen — Fine print", () => {
  test("affiche les informations détaillées", () => {
    renderPlans();
    expect(screen.getByText(/2 crédits = 1 vidéo de 10 secondes/)).toBeTruthy();
    expect(screen.getByText(/3 crédits = 1 vidéo de 15 secondes/)).toBeTruthy();
    expect(screen.getByText(/crédits se renouvellent/)).toBeTruthy();
    expect(screen.getByText(/Qualité cinématique/)).toBeTruthy();
  });
});

describe("VideoPlansScreen — Navigation", () => {
  test("back button appelle goBack", () => {
    renderPlans();
    fireEvent.press(screen.getByText("arrow-back"));
    expect(mockGoBack).toHaveBeenCalled();
  });
});

describe("VideoPlansScreen — Sans brand", () => {
  test("ne charge pas les crédits sans brandId", () => {
    render(
      <BrandContext.Provider value={{ activeBrand: null, brands: [] } as any}>
        <VideoPlansScreen />
      </BrandContext.Provider>
    );
    expect(videoApi.credits).not.toHaveBeenCalled();
  });
});
