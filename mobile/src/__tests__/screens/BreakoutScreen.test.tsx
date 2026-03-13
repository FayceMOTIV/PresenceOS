/**
 * Tests du BreakoutScreen
 */

import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react-native";
import { Alert } from "react-native";
import BreakoutScreen from "@/screens/breakout/BreakoutScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { breakoutApi } from "@/lib/api";

jest.setTimeout(60000);
jest.useFakeTimers();
jest.spyOn(Alert, "alert");

jest.mock("@/lib/api", () => ({
  breakoutApi: { generate: jest.fn() },
}));

jest.mock("expo-image-picker", () => ({
  launchImageLibraryAsync: jest.fn().mockResolvedValue({
    canceled: false,
    assets: [{ uri: "file://photo.jpg" }],
  }),
  MediaTypeOptions: { Images: "Images" },
}));

const mockBrand = {
  activeBrand: {
    id: "brand-1",
    name: "Le Bistrot",
    slug: "lebistrot",
    brand_type: "restaurant",
  },
  brands: [],
};

function renderBreakout(brand = mockBrand) {
  return render(
    <BrandContext.Provider value={brand as any}>
      <BreakoutScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

afterEach(() => {
  act(() => {
    jest.runOnlyPendingTimers();
  });
});

// ─── Input step ────────────────────────────────────────────────────────────

describe("BreakoutScreen — Rendu initial (input)", () => {
  test("affiche le titre Breakout", () => {
    renderBreakout();
    expect(screen.getByText("Breakout")).toBeTruthy();
  });

  test("affiche le sous-titre effet 3D", () => {
    renderBreakout();
    expect(
      screen.getByText("Effet 3D viral — ton contenu sort du cadre")
    ).toBeTruthy();
  });

  test("affiche l'icône layers-outline", () => {
    renderBreakout();
    expect(screen.getByTestId("icon-layers-outline")).toBeTruthy();
  });

  test("affiche le placeholder de la zone photo", () => {
    renderBreakout();
    expect(
      screen.getByText("Choisis une photo de plat ou produit")
    ).toBeTruthy();
  });

  test("affiche l'icone caméra", () => {
    renderBreakout();
    expect(screen.getByTestId("icon-camera-outline")).toBeTruthy();
  });

  test("affiche le bouton Generer Breakout", () => {
    renderBreakout();
    expect(screen.getByText("Generer Breakout")).toBeTruthy();
  });

  test("affiche le hint de coût", () => {
    renderBreakout();
    expect(screen.getByText("Gratuit · ~1 minute")).toBeTruthy();
  });
});

// ─── Image picker ──────────────────────────────────────────────────────────

describe("BreakoutScreen — Photo picker", () => {
  test("appuyer sur la zone photo ouvre le picker", async () => {
    const ImagePicker = require("expo-image-picker");
    renderBreakout();
    fireEvent.press(
      screen.getByText("Choisis une photo de plat ou produit")
    );
    await waitFor(() => {
      expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledWith({
        mediaTypes: "Images",
        quality: 0.9,
      });
    });
  });

  test("après sélection, affiche le bouton Changer la photo", async () => {
    const ImagePicker = require("expo-image-picker");
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({
      canceled: false,
      assets: [{ uri: "file://burger.jpg" }],
    });
    renderBreakout();
    fireEvent.press(
      screen.getByText("Choisis une photo de plat ou produit")
    );
    await waitFor(() => {
      expect(screen.getByText("Changer la photo")).toBeTruthy();
    });
  });

  test("annuler le picker ne change pas la photo", async () => {
    const ImagePicker = require("expo-image-picker");
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({
      canceled: true,
      assets: [],
    });
    renderBreakout();
    fireEvent.press(
      screen.getByText("Choisis une photo de plat ou produit")
    );
    await waitFor(() => {
      expect(screen.queryByText("Changer la photo")).toBeNull();
    });
  });

  test("Changer la photo appelle de nouveau le picker", async () => {
    const ImagePicker = require("expo-image-picker");
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({
      canceled: false,
      assets: [{ uri: "file://photo1.jpg" }],
    });
    renderBreakout();
    // First pick
    fireEvent.press(
      screen.getByText("Choisis une photo de plat ou produit")
    );
    await waitFor(() => {
      expect(screen.getByText("Changer la photo")).toBeTruthy();
    });
    // Change
    fireEvent.press(screen.getByText("Changer la photo"));
    await waitFor(() => {
      expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledTimes(2);
    });
  });
});

// ─── Validation ────────────────────────────────────────────────────────────

describe("BreakoutScreen — Validation avant génération", () => {
  test("affiche alerte si pas de brandId", async () => {
    const ImagePicker = require("expo-image-picker");
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({
      canceled: false,
      assets: [{ uri: "file://photo.jpg" }],
    });
    render(
      <BrandContext.Provider
        value={{ activeBrand: null, brands: [] } as any}
      >
        <BreakoutScreen />
      </BrandContext.Provider>
    );
    // Pick a photo first
    fireEvent.press(
      screen.getByText("Choisis une photo de plat ou produit")
    );
    await waitFor(() => {
      expect(screen.getByText("Changer la photo")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Generer Breakout"));
    expect(Alert.alert).toHaveBeenCalledWith(
      "Erreur",
      "Aucune marque selectionnee"
    );
  });

  test("le bouton Generer est disabled quand aucune photo n'est sélectionnée", () => {
    renderBreakout();
    // When no photo, the button has disabled={true}
    // fireEvent.press on a disabled element is a no-op — Alert is NOT called
    fireEvent.press(screen.getByText("Generer Breakout"));
    expect(Alert.alert).not.toHaveBeenCalled();
  });
});

// ─── Generating step ───────────────────────────────────────────────────────

describe("BreakoutScreen — Étape generating", () => {
  async function pickPhotoAndGenerate() {
    const ImagePicker = require("expo-image-picker");
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({
      canceled: false,
      assets: [{ uri: "file://dish.jpg" }],
    });

    renderBreakout();

    fireEvent.press(
      screen.getByText("Choisis une photo de plat ou produit")
    );
    await waitFor(() => {
      expect(screen.getByText("Changer la photo")).toBeTruthy();
    });

    // Delay API response so we can observe generating state
    (breakoutApi.generate as jest.Mock).mockReturnValue(
      new Promise(() => {}) // never resolves
    );

    fireEvent.press(screen.getByText("Generer Breakout"));
  }

  test("affiche l'indicateur de progression", async () => {
    await pickPhotoAndGenerate();
    await waitFor(() => {
      expect(screen.getByText("0%")).toBeTruthy();
    });
  });

  test("affiche le label ETA ~1 minute", async () => {
    await pickPhotoAndGenerate();
    await waitFor(() => {
      expect(screen.getByText("~1 minute")).toBeTruthy();
    });
  });

  test("avance le pourcentage avec le timer", async () => {
    await pickPhotoAndGenerate();
    await waitFor(() => {
      expect(screen.getByText("0%")).toBeTruthy();
    });
    act(() => {
      jest.advanceTimersByTime(2400); // 2 ticks × 1200ms
    });
    await waitFor(() => {
      expect(screen.getByText("2%")).toBeTruthy();
    });
  });
});

// ─── Preview step ──────────────────────────────────────────────────────────

describe("BreakoutScreen — Étape preview", () => {
  async function pickAndGenerateSuccess() {
    const ImagePicker = require("expo-image-picker");
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({
      canceled: false,
      assets: [{ uri: "file://dish.jpg" }],
    });
    (breakoutApi.generate as jest.Mock).mockResolvedValue({
      data: { video_url: "https://cdn.example.com/breakout.mp4" },
    });

    renderBreakout();
    fireEvent.press(
      screen.getByText("Choisis une photo de plat ou produit")
    );
    await waitFor(() => {
      expect(screen.getByText("Changer la photo")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Generer Breakout"));
  }

  test("affiche le titre Preview Breakout après succès", async () => {
    await pickAndGenerateSuccess();
    await waitFor(() => {
      expect(screen.getByText("Preview Breakout")).toBeTruthy();
    });
  });

  test("affiche le bouton Refaire", async () => {
    await pickAndGenerateSuccess();
    await waitFor(() => {
      expect(screen.getByText("Refaire")).toBeTruthy();
    });
  });

  test("affiche le bouton Sauvegarder", async () => {
    await pickAndGenerateSuccess();
    await waitFor(() => {
      expect(screen.getByText("Sauvegarder")).toBeTruthy();
    });
  });

  test("Refaire remet le step à input", async () => {
    await pickAndGenerateSuccess();
    await waitFor(() => {
      expect(screen.getByText("Refaire")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Refaire"));
    await waitFor(() => {
      expect(screen.getByText("Breakout")).toBeTruthy();
      expect(screen.queryByText("Preview Breakout")).toBeNull();
    });
  });

  test("Sauvegarder affiche l'alerte de confirmation", async () => {
    await pickAndGenerateSuccess();
    await waitFor(() => {
      expect(screen.getByText("Sauvegarder")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Sauvegarder"));
    expect(Alert.alert).toHaveBeenCalledWith(
      "Video sauvegardee",
      "Ta video Breakout a ete enregistree dans ta mediatheque."
    );
  });

  test("Sauvegarder puis reset remet l'écran à input", async () => {
    await pickAndGenerateSuccess();
    await waitFor(() => {
      expect(screen.getByText("Sauvegarder")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Sauvegarder"));
    await waitFor(() => {
      expect(screen.getByText("Breakout")).toBeTruthy();
    });
  });
});

// ─── Error step ─────────────────────────────────────────────────────────────

describe("BreakoutScreen — Étape erreur", () => {
  async function pickAndGenerateFail(errorPayload: any) {
    const ImagePicker = require("expo-image-picker");
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({
      canceled: false,
      assets: [{ uri: "file://dish.jpg" }],
    });
    (breakoutApi.generate as jest.Mock).mockRejectedValue(errorPayload);

    renderBreakout();
    fireEvent.press(
      screen.getByText("Choisis une photo de plat ou produit")
    );
    await waitFor(() => {
      expect(screen.getByText("Changer la photo")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Generer Breakout"));
  }

  test("affiche le message Generation echouee", async () => {
    await pickAndGenerateFail(new Error("Network error"));
    await waitFor(() => {
      expect(screen.getByText("Generation echouee")).toBeTruthy();
    });
  });

  test("affiche le détail de l'erreur (message)", async () => {
    await pickAndGenerateFail(new Error("Connection refused"));
    await waitFor(() => {
      expect(screen.getByText("Connection refused")).toBeTruthy();
    });
  });

  test("affiche le détail de l'erreur (response.data.detail)", async () => {
    await pickAndGenerateFail({
      response: { data: { detail: "Server is overloaded" } },
    });
    await waitFor(() => {
      expect(screen.getByText("Server is overloaded")).toBeTruthy();
    });
  });

  test("affiche le bouton Reessayer", async () => {
    await pickAndGenerateFail(new Error("fail"));
    await waitFor(() => {
      expect(screen.getByText("Reessayer")).toBeTruthy();
    });
  });

  test("Reessayer remet l'écran à l'état input", async () => {
    await pickAndGenerateFail(new Error("fail"));
    await waitFor(() => {
      expect(screen.getByText("Reessayer")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Reessayer"));
    await waitFor(() => {
      expect(screen.getByText("Breakout")).toBeTruthy();
      expect(screen.queryByText("Generation echouee")).toBeNull();
    });
  });

  test("affiche l'icône alert-circle en cas d'erreur", async () => {
    await pickAndGenerateFail(new Error("fail"));
    await waitFor(() => {
      expect(screen.getByTestId("icon-alert-circle")).toBeTruthy();
    });
  });

  test("erreur sans video_url throw et affiche le fallback", async () => {
    const ImagePicker = require("expo-image-picker");
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({
      canceled: false,
      assets: [{ uri: "file://dish.jpg" }],
    });
    (breakoutApi.generate as jest.Mock).mockResolvedValue({
      data: { video_url: null },
    });

    renderBreakout();
    fireEvent.press(
      screen.getByText("Choisis une photo de plat ou produit")
    );
    await waitFor(() => {
      expect(screen.getByText("Changer la photo")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Generer Breakout"));

    await waitFor(() => {
      expect(screen.getByText("Generation echouee")).toBeTruthy();
    });
  });
});

// ─── API call shape ─────────────────────────────────────────────────────────

describe("BreakoutScreen — Appel API", () => {
  test("breakoutApi.generate est appelé avec brandId et formData", async () => {
    const ImagePicker = require("expo-image-picker");
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({
      canceled: false,
      assets: [{ uri: "file://dish.jpg" }],
    });
    (breakoutApi.generate as jest.Mock).mockResolvedValue({
      data: { video_url: "https://cdn.example.com/out.mp4" },
    });

    renderBreakout();
    fireEvent.press(
      screen.getByText("Choisis une photo de plat ou produit")
    );
    await waitFor(() => {
      expect(screen.getByText("Changer la photo")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Generer Breakout"));

    await waitFor(() => {
      expect(breakoutApi.generate).toHaveBeenCalledWith(
        "brand-1",
        expect.any(FormData)
      );
    });
  });
});
