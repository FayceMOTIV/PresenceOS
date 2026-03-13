/**
 * Tests du AIVideoScreen
 * Covers: rendering, model/duration/ratio chip selection,
 *         prompt validation, generate call, result display,
 *         error state, reset, no-brand guard.
 */

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react-native";
import { Alert } from "react-native";
import AIVideoScreen from "@/screens/video/AIVideoScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { aiVideoApi } from "@/lib/api";

jest.setTimeout(60000);
jest.useFakeTimers();
jest.spyOn(Alert, "alert");

jest.mock("@/lib/api", () => ({
  aiVideoApi: {
    textToVideo: jest.fn(),
  },
}));

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ navigate: jest.fn(), goBack: jest.fn() }),
  useRoute: () => ({ params: {} }),
}));

// expo-av Video mock
jest.mock("expo-av", () => ({
  Video: "Video",
  ResizeMode: { CONTAIN: "contain" },
}));

const mockBrand = {
  activeBrand: { id: "brand-42", name: "Le Bistrot", slug: "le-bistrot", brand_type: "restaurant" },
  brands: [],
};

function renderScreen(brand = mockBrand) {
  return render(
    <BrandContext.Provider value={brand as any}>
      <AIVideoScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

afterEach(() => {
  act(() => { jest.runOnlyPendingTimers(); });
});

// ─── Rendering ───────────────────────────────────────────────

describe("AIVideoScreen — Rendu initial", () => {
  test("affiche le titre AI Vidéo", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("AI Vidéo")).toBeTruthy();
  });

  test("affiche le sous-titre avec les modeles", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Kling 2.6 Pro · Wan 2.6")).toBeTruthy();
  });

  test("affiche la section Description", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Description")).toBeTruthy();
  });

  test("affiche la section Modele", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Modèle")).toBeTruthy();
  });

  test("affiche les deux modeles Kling 2.6 Pro et Wan 2.6", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Kling 2.6 Pro")).toBeTruthy();
    expect(screen.getByText("Wan 2.6")).toBeTruthy();
  });

  test("affiche les descriptions de modeles", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Qualité max")).toBeTruthy();
    expect(screen.getByText("Budget")).toBeTruthy();
  });

  test("affiche la section Duree", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Durée")).toBeTruthy();
  });

  test("affiche les chips de duree 5s et 10s", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("5s")).toBeTruthy();
    expect(screen.getByText("10s")).toBeTruthy();
  });

  test("affiche les labels de duree (pas de desc dans les chips duree)", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    // Duration chips render only label, not desc (by design in the source)
    expect(screen.getByText("5s")).toBeTruthy();
    expect(screen.getByText("10s")).toBeTruthy();
  });

  test("affiche la section Format", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Format")).toBeTruthy();
  });

  test("affiche les trois ratios", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("9:16")).toBeTruthy();
    expect(screen.getByText("1:1")).toBeTruthy();
    expect(screen.getByText("16:9")).toBeTruthy();
  });

  test("affiche les descriptions de ratio", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Reel / Story")).toBeTruthy();
    expect(screen.getByText("Post carré")).toBeTruthy();
    expect(screen.getByText("Paysage")).toBeTruthy();
  });

  test("affiche le bouton Generer la video", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.getByText("Générer la vidéo")).toBeTruthy();
  });

  test("le bouton Generer est desactive sans prompt", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const btn = screen.getByText("Générer la vidéo");
    // Confirm the button exists but is not callable without prompt
    expect(btn).toBeTruthy();
    // Pressing without prompt should NOT call the API
    fireEvent.press(btn);
    expect(aiVideoApi.textToVideo).not.toHaveBeenCalled();
  });
});

// ─── Prompt Validation ───────────────────────────────────────

describe("AIVideoScreen — Validation du prompt", () => {
  test("affiche hint 'Minimum 5 caracteres' si prompt 1-4 chars", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Abc");
    expect(screen.getByText("Minimum 5 caractères")).toBeTruthy();
  });

  test("pas de hint si prompt vide", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    expect(screen.queryByText("Minimum 5 caractères")).toBeNull();
  });

  test("pas de hint si prompt >= 5 chars", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Burger avec frites");
    expect(screen.queryByText("Minimum 5 caractères")).toBeNull();
  });

  test("affiche le footer hint quand prompt valide", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Burger avec frites croustillantes");
    // Footer hint: "{duration}s · {model} · {ratio}"
    expect(screen.getByText("5s · Kling 2.6 Pro · 9:16")).toBeTruthy();
  });
});

// ─── Chip Selection ───────────────────────────────────────────

describe("AIVideoScreen — Selection des chips", () => {
  test("selection du modele Wan 2.6 met a jour le footer hint", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    // Switch model to Wan
    fireEvent.press(screen.getByText("Wan 2.6"));
    expect(screen.getByText("5s · Wan 2.6 · 9:16")).toBeTruthy();
  });

  test("selection duree 10s met a jour le footer hint", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("10s"));
    expect(screen.getByText("10s · Kling 2.6 Pro · 9:16")).toBeTruthy();
  });

  test("selection ratio 1:1 met a jour le footer hint", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("1:1"));
    expect(screen.getByText("5s · Kling 2.6 Pro · 1:1")).toBeTruthy();
  });

  test("selection ratio 16:9 met a jour le footer hint", () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("16:9"));
    expect(screen.getByText("5s · Kling 2.6 Pro · 16:9")).toBeTruthy();
  });
});

// ─── Generation ───────────────────────────────────────────────

describe("AIVideoScreen — Generation reussie", () => {
  const mockResult = {
    url: "https://cdn.example.com/video.mp4",
    model: "fal-ai/kling-video/v2.1/pro/text-to-video",
    duration: 5,
    aspect_ratio: "9:16",
    persisted: true,
    generated_at: "2026-03-13T10:00:00Z",
  };

  beforeEach(() => {
    (aiVideoApi.textToVideo as jest.Mock).mockResolvedValue({ data: mockResult });
  });

  test("appelle aiVideoApi.textToVideo avec les bons parametres par defaut", async () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("Générer la vidéo"));

    await waitFor(() => {
      expect(aiVideoApi.textToVideo).toHaveBeenCalledWith(
        "brand-42",
        "Un burger juteux et doré",
        5,
        "9:16",
        "kling"
      );
    });
  });

  test("appelle textToVideo avec duree 10s apres selection", async () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("10s"));
    fireEvent.press(screen.getByText("Générer la vidéo"));

    await waitFor(() => {
      expect(aiVideoApi.textToVideo).toHaveBeenCalledWith(
        "brand-42",
        "Un burger juteux et doré",
        10,
        "9:16",
        "kling"
      );
    });
  });

  test("appelle textToVideo avec modele wan apres selection", async () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("Wan 2.6"));
    fireEvent.press(screen.getByText("Générer la vidéo"));

    await waitFor(() => {
      expect(aiVideoApi.textToVideo).toHaveBeenCalledWith(
        "brand-42",
        "Un burger juteux et doré",
        5,
        "9:16",
        "wan"
      );
    });
  });

  test("affiche badge 'Video prete !' apres generation", async () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("Générer la vidéo"));

    await waitFor(() => {
      expect(screen.getByText("Vidéo prête !")).toBeTruthy();
    });
  });

  test("affiche le meta de la video apres generation", async () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("Générer la vidéo"));

    await waitFor(() => {
      // model.split("/").pop() = "text-to-video", duration=5, aspect_ratio="9:16"
      expect(screen.getByText(/text-to-video · 5s · 9:16/)).toBeTruthy();
    });
  });

  test("affiche le bouton 'Nouvelle video' apres generation", async () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("Générer la vidéo"));

    await waitFor(() => {
      expect(screen.getByText("Nouvelle vidéo")).toBeTruthy();
    });
  });

  test("le bouton 'Generer' disparait apres generation", async () => {
    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("Générer la vidéo"));

    await waitFor(() => {
      expect(screen.queryByText("Générer la vidéo")).toBeNull();
    });
  });
});

// ─── Loading State ────────────────────────────────────────────

describe("AIVideoScreen — Etat de chargement", () => {
  test("affiche 'Generation en cours...' pendant le chargement", async () => {
    // Keep the promise pending to observe loading state
    let resolvePromise: (val: any) => void;
    (aiVideoApi.textToVideo as jest.Mock).mockImplementation(
      () => new Promise((resolve) => { resolvePromise = resolve; })
    );

    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("Générer la vidéo"));

    await waitFor(() => {
      expect(screen.getByText("Génération en cours...")).toBeTruthy();
    });

    // Resolve to avoid timer leaks
    act(() => { resolvePromise!({ data: { url: "", model: "m", duration: 5, aspect_ratio: "9:16", persisted: true, generated_at: "" } }); });
  });

  test("affiche le hint de temps (60s) pendant chargement 5s", async () => {
    let resolvePromise: (val: any) => void;
    (aiVideoApi.textToVideo as jest.Mock).mockImplementation(
      () => new Promise((resolve) => { resolvePromise = resolve; })
    );

    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("Générer la vidéo"));

    await waitFor(() => {
      expect(screen.getByText("Environ 60 secondes")).toBeTruthy();
    });

    act(() => { resolvePromise!({ data: { url: "", model: "m", duration: 5, aspect_ratio: "9:16", persisted: true, generated_at: "" } }); });
  });

  test("affiche hint 90s pour duree 10s", async () => {
    let resolvePromise: (val: any) => void;
    (aiVideoApi.textToVideo as jest.Mock).mockImplementation(
      () => new Promise((resolve) => { resolvePromise = resolve; })
    );

    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    fireEvent.press(screen.getByText("10s"));
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("Générer la vidéo"));

    await waitFor(() => {
      expect(screen.getByText("Environ 90 secondes")).toBeTruthy();
    });

    act(() => { resolvePromise!({ data: { url: "", model: "m", duration: 10, aspect_ratio: "9:16", persisted: true, generated_at: "" } }); });
  });
});

// ─── Error State ──────────────────────────────────────────────

describe("AIVideoScreen — Gestion des erreurs", () => {
  test("affiche Alert avec message detail en cas d'echec", async () => {
    (aiVideoApi.textToVideo as jest.Mock).mockRejectedValue({
      response: { data: { detail: "Quota dépassé" } },
    });

    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("Générer la vidéo"));

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith("Erreur", "Quota dépassé");
    });
  });

  test("affiche message generique si pas de detail dans l'erreur", async () => {
    (aiVideoApi.textToVideo as jest.Mock).mockRejectedValue(new Error("Network error"));

    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("Générer la vidéo"));

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith("Erreur", "La génération vidéo a échoué.");
    });
  });

  test("le bouton Generer reapparait apres une erreur", async () => {
    (aiVideoApi.textToVideo as jest.Mock).mockRejectedValue(new Error("Network error"));

    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("Générer la vidéo"));

    await waitFor(() => {
      expect(screen.getByText("Générer la vidéo")).toBeTruthy();
    });
  });
});

// ─── Reset ────────────────────────────────────────────────────

describe("AIVideoScreen — Reset", () => {
  test("bouton 'Nouvelle video' remet l'ecran a zero", async () => {
    (aiVideoApi.textToVideo as jest.Mock).mockResolvedValue({
      data: {
        url: "https://cdn.example.com/video.mp4",
        model: "kling",
        duration: 5,
        aspect_ratio: "9:16",
        persisted: true,
        generated_at: "2026-03-13T10:00:00Z",
      },
    });

    renderScreen();
    act(() => { jest.advanceTimersByTime(500); });
    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("Générer la vidéo"));

    await waitFor(() => {
      expect(screen.getByText("Nouvelle vidéo")).toBeTruthy();
    });

    fireEvent.press(screen.getByText("Nouvelle vidéo"));

    await waitFor(() => {
      expect(screen.getByText("Générer la vidéo")).toBeTruthy();
      expect(screen.queryByText("Vidéo prête !")).toBeNull();
    });
  });
});

// ─── No Brand ─────────────────────────────────────────────────

describe("AIVideoScreen — Sans brand", () => {
  test("ne fait pas d'appel API si aucun brandId", async () => {
    render(
      <BrandContext.Provider value={{ activeBrand: null, brands: [] } as any}>
        <AIVideoScreen />
      </BrandContext.Provider>
    );
    act(() => { jest.advanceTimersByTime(500); });

    const input = screen.getByPlaceholderText(/Un plat de pâtes/);
    fireEvent.changeText(input, "Un burger juteux et doré");
    fireEvent.press(screen.getByText("Générer la vidéo"));

    await waitFor(() => {
      expect(aiVideoApi.textToVideo).not.toHaveBeenCalled();
    });
  });
});
