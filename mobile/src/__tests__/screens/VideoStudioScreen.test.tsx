/**
 * Tests du VideoStudioScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react-native";
import { Alert } from "react-native";
import VideoStudioScreen from "@/screens/video/VideoStudioScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { videoApi } from "@/lib/api";

jest.useFakeTimers();
jest.spyOn(Alert, "alert");

jest.mock("@/lib/api", () => ({
  videoApi: { credits: jest.fn(), generate: jest.fn() },
}));

const mockNav = {
  navigate: jest.fn(),
  goBack: jest.fn(),
  getParent: jest.fn(() => ({ navigate: jest.fn() })),
};
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => mockNav,
  useRoute: () => ({ params: {} }),
}));

const mockBrand = {
  activeBrand: { id: "brand-1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

function renderStudio() {
  return render(
    <BrandContext.Provider value={mockBrand as any}>
      <VideoStudioScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (videoApi.credits as jest.Mock).mockResolvedValue({
    data: { credits_remaining: 10, credits_total: 20, plan: "pro" },
  });
});

afterEach(() => {
  act(() => { jest.runOnlyPendingTimers(); });
});

describe("VideoStudioScreen — Rendu", () => {
  test("affiche le titre Studio Vidéo", async () => {
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Studio Vidéo")).toBeTruthy();
  });

  test("affiche le sous-titre", () => {
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Créez des Reels IA en 45s")).toBeTruthy();
  });

  test("affiche les crédits", async () => {
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });
    await waitFor(() => {
      expect(screen.getByText("10")).toBeTruthy();
    });
  });

  test("affiche la section Description", () => {
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Description")).toBeTruthy();
  });

  test("affiche la section Durée", () => {
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Durée")).toBeTruthy();
  });

  test("affiche les chips de durée", () => {
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("5s")).toBeTruthy();
    expect(screen.getByText("10s")).toBeTruthy();
    expect(screen.getByText("15s")).toBeTruthy();
  });

  test("affiche la section Style", () => {
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Style")).toBeTruthy();
  });

  test("affiche les styles", () => {
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Cinematic")).toBeTruthy();
    expect(screen.getByText("Naturel")).toBeTruthy();
    expect(screen.getByText("Vibrant")).toBeTruthy();
    expect(screen.getByText("Minimal")).toBeTruthy();
  });

  test("affiche la section Format", () => {
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Format")).toBeTruthy();
  });

  test("affiche les ratios", () => {
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("9:16")).toBeTruthy();
    expect(screen.getByText("1:1")).toBeTruthy();
    expect(screen.getByText("16:9")).toBeTruthy();
  });
});

describe("VideoStudioScreen — Validation prompt", () => {
  test("affiche hint si prompt < 5 chars", () => {
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });
    fireEvent.changeText(screen.getByPlaceholderText(/Gros plan/), "Abc");
    expect(screen.getByText("Minimum 5 caractères")).toBeTruthy();
  });

  test("pas de hint si prompt >= 5 chars", () => {
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });
    fireEvent.changeText(screen.getByPlaceholderText(/Gros plan/), "Un beau burger");
    expect(screen.queryByText("Minimum 5 caractères")).toBeNull();
  });
});

describe("VideoStudioScreen — Génération", () => {
  test("generate appelle videoApi.generate", async () => {
    (videoApi.generate as jest.Mock).mockResolvedValue({
      data: { video_url: "https://example.com/video.mp4", status: "completed", credits_remaining: 9, credits_used: 1, duration: 5 },
    });
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });

    await waitFor(() => {
      expect(screen.getByText("10")).toBeTruthy();
    });

    fireEvent.changeText(screen.getByPlaceholderText(/Gros plan/), "Un beau burger juteux avec du fromage");
    fireEvent.press(screen.getByText(/Générer/));

    await waitFor(() => {
      expect(videoApi.generate).toHaveBeenCalledWith("brand-1", "Un beau burger juteux avec du fromage", 5, "cinematic", "9:16");
    });
  });

  test("affiche résultat après génération réussie", async () => {
    (videoApi.generate as jest.Mock).mockResolvedValue({
      data: { video_url: "https://example.com/video.mp4", status: "completed", credits_remaining: 9, credits_used: 1, duration: 5 },
    });
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });

    await waitFor(() => {
      expect(screen.getByText("10")).toBeTruthy();
    });

    fireEvent.changeText(screen.getByPlaceholderText(/Gros plan/), "Un beau burger juteux avec du fromage");
    fireEvent.press(screen.getByText(/Générer/));

    await waitFor(() => {
      expect(screen.getByText("Vidéo prête !")).toBeTruthy();
      expect(screen.getByText("Publier")).toBeTruthy();
      expect(screen.getByText("Sauvegarder")).toBeTruthy();
      expect(screen.getByText("Nouvelle vidéo")).toBeTruthy();
    });
  });

  test("affiche erreur si génération échoue", async () => {
    (videoApi.generate as jest.Mock).mockRejectedValue({ response: { data: { detail: "Erreur serveur" } } });
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });

    await waitFor(() => {
      expect(screen.getByText("10")).toBeTruthy();
    });

    fireEvent.changeText(screen.getByPlaceholderText(/Gros plan/), "Un beau burger juteux avec du fromage");
    fireEvent.press(screen.getByText(/Générer/));

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith("Échec de la génération", "Erreur serveur");
    });
  });
});

describe("VideoStudioScreen — No credits", () => {
  test("affiche banner Plus de crédits quand 0", async () => {
    (videoApi.credits as jest.Mock).mockResolvedValue({
      data: { credits_remaining: 0, credits_total: 0, plan: "trial" },
    });
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });

    await waitFor(() => {
      expect(screen.getByText("Plus de crédits")).toBeTruthy();
    });
  });
});

describe("VideoStudioScreen — Credits badge navigation", () => {
  test("credits badge navigue vers VideoPlans", async () => {
    renderStudio();
    act(() => { jest.advanceTimersByTime(500); });
    await waitFor(() => {
      expect(screen.getByText("10")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("10"));
    expect(mockNav.navigate).toHaveBeenCalledWith("VideoPlans");
  });
});
