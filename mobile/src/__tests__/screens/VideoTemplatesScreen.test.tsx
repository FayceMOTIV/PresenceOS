/**
 * Tests du VideoTemplatesScreen
 * Covers: template list rendering, template selection, photo picker interaction,
 *         form fields (promo, showcase, story), generate calls, error state,
 *         preview/reset flow, no-brand guard.
 */

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react-native";
import { Alert } from "react-native";
import VideoTemplatesScreen from "@/screens/video/VideoTemplatesScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { videoTemplatesApi } from "@/lib/api";

jest.setTimeout(60000);
jest.spyOn(Alert, "alert");

jest.mock("@/lib/api", () => ({
  videoTemplatesApi: {
    generateBreakoutV4: jest.fn(),
    generateCinematic: jest.fn(),
    generatePromoFlash: jest.fn(),
    generateShowcase: jest.fn(),
    generateStory: jest.fn(),
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

// expo-image-picker mock
const mockPickerResult = {
  canceled: false,
  assets: [{ uri: "file:///mock/photo.jpg", mimeType: "image/jpeg", width: 800, height: 600 }],
};
jest.mock("expo-image-picker", () => ({
  requestMediaLibraryPermissionsAsync: jest.fn().mockResolvedValue({ status: "granted" }),
  requestCameraPermissionsAsync: jest.fn().mockResolvedValue({ status: "granted" }),
  launchImageLibraryAsync: jest.fn().mockResolvedValue(mockPickerResult),
  launchCameraAsync: jest.fn().mockResolvedValue(mockPickerResult),
}));

const mockBrand = {
  activeBrand: { id: "brand-99", name: "La Bonne Table", slug: "la-bonne-table", brand_type: "restaurant" },
  brands: [],
};

function renderScreen(brand = mockBrand) {
  return render(
    <BrandContext.Provider value={brand as any}>
      <VideoTemplatesScreen navigation={{ navigate: jest.fn(), goBack: jest.fn() } as any} />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  const ImagePicker = require("expo-image-picker");
  (ImagePicker.requestMediaLibraryPermissionsAsync as jest.Mock).mockResolvedValue({ status: "granted" });
  (ImagePicker.requestCameraPermissionsAsync as jest.Mock).mockResolvedValue({ status: "granted" });
  (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue(mockPickerResult);
  (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue(mockPickerResult);
});

// ─── Rendering ───────────────────────────────────────────────

describe("VideoTemplatesScreen — Rendu initial", () => {
  test("affiche le titre 'Templates Video'", () => {
    renderScreen();
    expect(screen.getByText("Templates Video")).toBeTruthy();
  });

  test("affiche le sous-titre", () => {
    renderScreen();
    expect(screen.getByText("Cree des videos virales a partir de photos")).toBeTruthy();
  });

  test("affiche les 5 templates", () => {
    renderScreen();
    expect(screen.getByText("Breakout V4")).toBeTruthy();
    expect(screen.getByText("Cinematic Food")).toBeTruthy();
    expect(screen.getByText("Promo Flash")).toBeTruthy();
    expect(screen.getByText("Showcase Plats")).toBeTruthy();
    expect(screen.getByText("Story Instagram")).toBeTruthy();
  });

  test("affiche les sous-titres des templates", () => {
    renderScreen();
    expect(screen.getByText("Le sujet sort du cadre Instagram")).toBeTruthy();
    expect(screen.getByText("Photo animee en video cinematique")).toBeTruthy();
    expect(screen.getByText("Video promo animee avec texte")).toBeTruthy();
    expect(screen.getByText("Presentez 3 plats en video")).toBeTruthy();
    expect(screen.getByText("Story animee avec 3 slides")).toBeTruthy();
  });

  test("affiche les couts", () => {
    renderScreen();
    const gratuits = screen.getAllByText("Gratuit");
    expect(gratuits.length).toBeGreaterThanOrEqual(4);
    expect(screen.getByText("$0.35")).toBeTruthy();
  });

  test("affiche les durees et temps", () => {
    renderScreen();
    expect(screen.getByText("3s")).toBeTruthy();
    expect(screen.getByText("5s")).toBeTruthy();
    // "8s" appears twice (Promo Flash + Showcase Plats both have 8s duration)
    expect(screen.getAllByText("8s").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("7s")).toBeTruthy();
  });

  test("affiche les infos multi-photos pour showcase et story", () => {
    renderScreen();
    const triplePhotos = screen.getAllByText("3 photos");
    expect(triplePhotos.length).toBeGreaterThanOrEqual(2);
  });

  test("n'affiche pas le bouton Generer sans selection", () => {
    renderScreen();
    expect(screen.queryByText("Generer la video")).toBeNull();
  });
});

// ─── Template Selection ───────────────────────────────────────

describe("VideoTemplatesScreen — Selection de template", () => {
  test("selectionner Breakout V4 affiche le picker photo", async () => {
    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => {
      expect(screen.getByText("Galerie")).toBeTruthy();
      expect(screen.getByText("Camera")).toBeTruthy();
    });
  });

  test("selectionner Cinematic Food affiche le picker photo", async () => {
    renderScreen();
    fireEvent.press(screen.getByText("Cinematic Food"));
    await waitFor(() => {
      expect(screen.getByText("Galerie")).toBeTruthy();
    });
  });

  test("selectionner Promo Flash affiche le picker photo", async () => {
    renderScreen();
    fireEvent.press(screen.getByText("Promo Flash"));
    await waitFor(() => {
      expect(screen.getByText("Galerie")).toBeTruthy();
    });
  });

  test("selectionner Showcase Plats affiche le picker multi-photos", async () => {
    renderScreen();
    fireEvent.press(screen.getByText("Showcase Plats"));
    await waitFor(() => {
      expect(screen.getByText("3 photos requises")).toBeTruthy();
      expect(screen.getByText("Photo 1")).toBeTruthy();
      expect(screen.getByText("Photo 2")).toBeTruthy();
      expect(screen.getByText("Photo 3")).toBeTruthy();
    });
  });

  test("selectionner Story Instagram affiche le picker multi-photos", async () => {
    renderScreen();
    fireEvent.press(screen.getByText("Story Instagram"));
    await waitFor(() => {
      expect(screen.getByText("3 photos requises")).toBeTruthy();
    });
  });
});

// ─── Breakout V4 Flow ─────────────────────────────────────────

describe("VideoTemplatesScreen — Breakout V4", () => {
  test("picker galerie lance launchImageLibraryAsync", async () => {
    const ImagePicker = require("expo-image-picker");
    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => {
      expect(ImagePicker.requestMediaLibraryPermissionsAsync).toHaveBeenCalled();
      expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalled();
    });
  });

  test("picker camera lance launchCameraAsync", async () => {
    const ImagePicker = require("expo-image-picker");
    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Camera")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Camera"));
    await waitFor(() => {
      expect(ImagePicker.requestCameraPermissionsAsync).toHaveBeenCalled();
      expect(ImagePicker.launchCameraAsync).toHaveBeenCalled();
    });
  });

  test("apres selection photo, affiche bouton Generer", async () => {
    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => {
      expect(screen.getByText("Generer la video")).toBeTruthy();
    });
  });

  test("permission galerie refusee affiche Alert", async () => {
    const ImagePicker = require("expo-image-picker");
    (ImagePicker.requestMediaLibraryPermissionsAsync as jest.Mock).mockResolvedValue({ status: "denied" });
    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith("Permission requise", expect.any(String));
    });
  });

  test("permission camera refusee affiche Alert", async () => {
    const ImagePicker = require("expo-image-picker");
    (ImagePicker.requestCameraPermissionsAsync as jest.Mock).mockResolvedValue({ status: "denied" });
    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Camera")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Camera"));
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith("Permission requise", expect.any(String));
    });
  });

  test("generate appelle videoTemplatesApi.generateBreakoutV4", async () => {
    (videoTemplatesApi.generateBreakoutV4 as jest.Mock).mockResolvedValue({
      data: { video_url: "https://cdn.example.com/breakout.mp4" },
    });
    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => { expect(screen.getByText("Generer la video")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Generer la video"));
    await waitFor(() => {
      expect(videoTemplatesApi.generateBreakoutV4).toHaveBeenCalledWith(
        "brand-99",
        expect.any(FormData)
      );
    });
  });

  test("generation reussie affiche video preview", async () => {
    (videoTemplatesApi.generateBreakoutV4 as jest.Mock).mockResolvedValue({
      data: { video_url: "https://cdn.example.com/breakout.mp4" },
    });
    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => { expect(screen.getByText("Generer la video")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Generer la video"));
    await waitFor(() => {
      expect(screen.getByText("Resultat")).toBeTruthy();
      expect(screen.getByText("Recommencer")).toBeTruthy();
    });
  });

  test("erreur generation affiche Alert", async () => {
    (videoTemplatesApi.generateBreakoutV4 as jest.Mock).mockRejectedValue({
      response: { data: { detail: "Erreur de rendu" } },
    });
    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => { expect(screen.getByText("Generer la video")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Generer la video"));
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith("Erreur", "Erreur de rendu");
    });
  });

  test("erreur generation sans detail affiche message generique", async () => {
    (videoTemplatesApi.generateBreakoutV4 as jest.Mock).mockRejectedValue(new Error("Network fail"));
    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => { expect(screen.getByText("Generer la video")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Generer la video"));
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith("Erreur", "Network fail");
    });
  });
});

// ─── Cinematic Food Flow ──────────────────────────────────────

describe("VideoTemplatesScreen — Cinematic Food", () => {
  test("affiche les chips de type de plat apres selection photo", async () => {
    renderScreen();
    fireEvent.press(screen.getByText("Cinematic Food"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => {
      expect(screen.getByText("Type de plat")).toBeTruthy();
      expect(screen.getByText("Auto")).toBeTruthy();
      expect(screen.getByText("Burger")).toBeTruthy();
      expect(screen.getByText("Pizza")).toBeTruthy();
      expect(screen.getByText("Dessert")).toBeTruthy();
      expect(screen.getByText("Boisson")).toBeTruthy();
    });
  });

  test("selection chip type de plat fonctionne", async () => {
    renderScreen();
    fireEvent.press(screen.getByText("Cinematic Food"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => { expect(screen.getByText("Burger")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Burger"));
    // No crash = success; chip state is internal
    expect(screen.getByText("Burger")).toBeTruthy();
  });

  test("generate appelle videoTemplatesApi.generateCinematic", async () => {
    (videoTemplatesApi.generateCinematic as jest.Mock).mockResolvedValue({
      data: { video_url: "https://cdn.example.com/cinematic.mp4" },
    });
    renderScreen();
    fireEvent.press(screen.getByText("Cinematic Food"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => { expect(screen.getByText("Generer la video")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Generer la video"));
    await waitFor(() => {
      expect(videoTemplatesApi.generateCinematic).toHaveBeenCalledWith(
        "brand-99",
        expect.any(FormData)
      );
    });
  });
});

// ─── Promo Flash Flow ─────────────────────────────────────────

describe("VideoTemplatesScreen — Promo Flash", () => {
  test("affiche les champs promo apres selection photo", async () => {
    renderScreen();
    fireEvent.press(screen.getByText("Promo Flash"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => {
      expect(screen.getByText("Personnaliser la promo")).toBeTruthy();
    });
  });

  test("affiche les inputs de promo avec valeurs par defaut", async () => {
    renderScreen();
    fireEvent.press(screen.getByText("Promo Flash"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => {
      expect(screen.getByDisplayValue("OFFRE SPECIALE")).toBeTruthy();
      expect(screen.getByDisplayValue("-20%")).toBeTruthy();
      expect(screen.getByDisplayValue("Reservez maintenant!")).toBeTruthy();
    });
  });

  test("modification du titre promo se reflete dans le champ", async () => {
    renderScreen();
    fireEvent.press(screen.getByText("Promo Flash"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => { expect(screen.getByDisplayValue("OFFRE SPECIALE")).toBeTruthy(); });
    fireEvent.changeText(screen.getByDisplayValue("OFFRE SPECIALE"), "HAPPY HOUR");
    expect(screen.getByDisplayValue("HAPPY HOUR")).toBeTruthy();
  });

  test("generate appelle videoTemplatesApi.generatePromoFlash", async () => {
    (videoTemplatesApi.generatePromoFlash as jest.Mock).mockResolvedValue({
      data: { video_url: "https://cdn.example.com/promo.mp4" },
    });
    renderScreen();
    fireEvent.press(screen.getByText("Promo Flash"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => { expect(screen.getByText("Generer la video")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Generer la video"));
    await waitFor(() => {
      expect(videoTemplatesApi.generatePromoFlash).toHaveBeenCalledWith(
        "brand-99",
        expect.any(FormData)
      );
    });
  });
});

// ─── Showcase Plats Flow ──────────────────────────────────────

describe("VideoTemplatesScreen — Showcase Plats", () => {
  test("affiche le picker multi-photos", async () => {
    renderScreen();
    fireEvent.press(screen.getByText("Showcase Plats"));
    await waitFor(() => {
      expect(screen.getByText("3 photos requises")).toBeTruthy();
      expect(screen.getByText("Photo 1")).toBeTruthy();
      expect(screen.getByText("Photo 2")).toBeTruthy();
      expect(screen.getByText("Photo 3")).toBeTruthy();
    });
  });

  test("appuyer sur slot photo 1 lance le picker", async () => {
    const ImagePicker = require("expo-image-picker");
    renderScreen();
    fireEvent.press(screen.getByText("Showcase Plats"));
    await waitFor(() => { expect(screen.getByText("Photo 1")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Photo 1"));
    await waitFor(() => {
      expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalled();
    });
  });

  test("affiche le formulaire showcase apres selection des 3 photos", async () => {
    // Pick all 3 slots to trigger step="configure"
    const ImagePicker = require("expo-image-picker");
    renderScreen();
    fireEvent.press(screen.getByText("Showcase Plats"));
    await waitFor(() => { expect(screen.getByText("Photo 1")).toBeTruthy(); });

    fireEvent.press(screen.getByText("Photo 1"));
    await waitFor(() => { expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledTimes(1); });

    fireEvent.press(screen.getByText("Photo 2"));
    await waitFor(() => { expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledTimes(2); });

    fireEvent.press(screen.getByText("Photo 3"));
    await waitFor(() => {
      expect(screen.getByText("Noms des plats")).toBeTruthy();
    });
  });

  test("generate appelle videoTemplatesApi.generateShowcase apres 3 photos", async () => {
    (videoTemplatesApi.generateShowcase as jest.Mock).mockResolvedValue({
      data: { video_url: "https://cdn.example.com/showcase.mp4" },
    });

    renderScreen();
    fireEvent.press(screen.getByText("Showcase Plats"));
    await waitFor(() => { expect(screen.getByText("Photo 1")).toBeTruthy(); });

    fireEvent.press(screen.getByText("Photo 1"));
    await waitFor(() => { expect(require("expo-image-picker").launchImageLibraryAsync).toHaveBeenCalledTimes(1); });
    fireEvent.press(screen.getByText("Photo 2"));
    await waitFor(() => { expect(require("expo-image-picker").launchImageLibraryAsync).toHaveBeenCalledTimes(2); });
    fireEvent.press(screen.getByText("Photo 3"));

    await waitFor(() => { expect(screen.getByText("Generer la video")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Generer la video"));

    await waitFor(() => {
      expect(videoTemplatesApi.generateShowcase).toHaveBeenCalledWith(
        "brand-99",
        expect.any(FormData)
      );
    });
  });
});

// ─── Story Instagram Flow ─────────────────────────────────────

describe("VideoTemplatesScreen — Story Instagram", () => {
  test("affiche le picker multi-photos", async () => {
    renderScreen();
    fireEvent.press(screen.getByText("Story Instagram"));
    await waitFor(() => {
      expect(screen.getByText("3 photos requises")).toBeTruthy();
    });
  });

  test("affiche le formulaire story apres selection des 3 photos", async () => {
    const ImagePicker = require("expo-image-picker");
    renderScreen();
    fireEvent.press(screen.getByText("Story Instagram"));
    await waitFor(() => { expect(screen.getByText("Photo 1")).toBeTruthy(); });

    fireEvent.press(screen.getByText("Photo 1"));
    await waitFor(() => { expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledTimes(1); });
    fireEvent.press(screen.getByText("Photo 2"));
    await waitFor(() => { expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledTimes(2); });
    fireEvent.press(screen.getByText("Photo 3"));

    await waitFor(() => {
      expect(screen.getByText("Textes des slides")).toBeTruthy();
    });
  });

  test("affiche les valeurs par defaut des textes story", async () => {
    const ImagePicker = require("expo-image-picker");
    renderScreen();
    fireEvent.press(screen.getByText("Story Instagram"));
    await waitFor(() => { expect(screen.getByText("Photo 1")).toBeTruthy(); });

    fireEvent.press(screen.getByText("Photo 1"));
    await waitFor(() => { expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledTimes(1); });
    fireEvent.press(screen.getByText("Photo 2"));
    await waitFor(() => { expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledTimes(2); });
    fireEvent.press(screen.getByText("Photo 3"));

    await waitFor(() => {
      expect(screen.getByDisplayValue("Decouvrez notre carte!")).toBeTruthy();
      expect(screen.getByDisplayValue("Prepare avec amour")).toBeTruthy();
      expect(screen.getByDisplayValue("Reservez votre table!")).toBeTruthy();
    });
  });

  test("modification du texte slide 1 fonctionne", async () => {
    const ImagePicker = require("expo-image-picker");
    renderScreen();
    fireEvent.press(screen.getByText("Story Instagram"));
    await waitFor(() => { expect(screen.getByText("Photo 1")).toBeTruthy(); });

    fireEvent.press(screen.getByText("Photo 1"));
    await waitFor(() => { expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledTimes(1); });
    fireEvent.press(screen.getByText("Photo 2"));
    await waitFor(() => { expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledTimes(2); });
    fireEvent.press(screen.getByText("Photo 3"));

    await waitFor(() => { expect(screen.getByDisplayValue("Decouvrez notre carte!")).toBeTruthy(); });
    fireEvent.changeText(screen.getByDisplayValue("Decouvrez notre carte!"), "Venez nous voir!");
    expect(screen.getByDisplayValue("Venez nous voir!")).toBeTruthy();
  });

  test("generate appelle videoTemplatesApi.generateStory", async () => {
    (videoTemplatesApi.generateStory as jest.Mock).mockResolvedValue({
      data: { video_url: "https://cdn.example.com/story.mp4" },
    });
    const ImagePicker = require("expo-image-picker");

    renderScreen();
    fireEvent.press(screen.getByText("Story Instagram"));
    await waitFor(() => { expect(screen.getByText("Photo 1")).toBeTruthy(); });

    fireEvent.press(screen.getByText("Photo 1"));
    await waitFor(() => { expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledTimes(1); });
    fireEvent.press(screen.getByText("Photo 2"));
    await waitFor(() => { expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledTimes(2); });
    fireEvent.press(screen.getByText("Photo 3"));

    await waitFor(() => { expect(screen.getByText("Generer la video")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Generer la video"));

    await waitFor(() => {
      expect(videoTemplatesApi.generateStory).toHaveBeenCalledWith(
        "brand-99",
        expect.any(FormData)
      );
    });
  });
});

// ─── Generating State ─────────────────────────────────────────

describe("VideoTemplatesScreen — Etat generating", () => {
  test("affiche spinner pendant generation (progressText specifique au template)", async () => {
    // Breakout V4 sets progressText="Detourage du sujet..." before the API call,
    // so the screen shows that text rather than the fallback "Generation en cours..."
    let resolvePromise: (val: any) => void;
    (videoTemplatesApi.generateBreakoutV4 as jest.Mock).mockImplementation(
      () => new Promise((resolve) => { resolvePromise = resolve; })
    );

    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => { expect(screen.getByText("Generer la video")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Generer la video"));

    await waitFor(() => {
      // Breakout uses "Detourage du sujet..." as its progress text
      expect(screen.getByText("Detourage du sujet...")).toBeTruthy();
    });

    act(() => { resolvePromise!({ data: { video_url: "https://cdn.example.com/v.mp4" } }); });
  });

  test("les cards template disparaissent pendant generation", async () => {
    let resolvePromise: (val: any) => void;
    (videoTemplatesApi.generateBreakoutV4 as jest.Mock).mockImplementation(
      () => new Promise((resolve) => { resolvePromise = resolve; })
    );

    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => { expect(screen.getByText("Generer la video")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Generer la video"));

    await waitFor(() => {
      // Cards hidden during generating step
      expect(screen.queryByText("Cinematic Food")).toBeNull();
      expect(screen.queryByText("Promo Flash")).toBeNull();
    });

    act(() => { resolvePromise!({ data: { video_url: "https://cdn.example.com/v.mp4" } }); });
  });
});

// ─── Preview & Reset ──────────────────────────────────────────

describe("VideoTemplatesScreen — Preview et Reset", () => {
  test("apres generation reussie, affiche Resultat et Recommencer", async () => {
    (videoTemplatesApi.generateBreakoutV4 as jest.Mock).mockResolvedValue({
      data: { video_url: "https://cdn.example.com/breakout.mp4" },
    });

    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => { expect(screen.getByText("Generer la video")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Generer la video"));

    await waitFor(() => {
      expect(screen.getByText("Resultat")).toBeTruthy();
      expect(screen.getByText("Recommencer")).toBeTruthy();
    });
  });

  test("bouton Recommencer remet l'ecran a zero", async () => {
    (videoTemplatesApi.generateBreakoutV4 as jest.Mock).mockResolvedValue({
      data: { video_url: "https://cdn.example.com/breakout.mp4" },
    });

    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => { expect(screen.getByText("Generer la video")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Generer la video"));

    await waitFor(() => { expect(screen.getByText("Recommencer")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Recommencer"));

    await waitFor(() => {
      // Back to initial state: all 5 template cards visible
      expect(screen.getByText("Breakout V4")).toBeTruthy();
      expect(screen.getByText("Cinematic Food")).toBeTruthy();
      expect(screen.queryByText("Resultat")).toBeNull();
    });
  });
});

// ─── No Brand ─────────────────────────────────────────────────

describe("VideoTemplatesScreen — Sans brand", () => {
  test("n'appelle pas l'API si aucun brandId", async () => {
    render(
      <BrandContext.Provider value={{ activeBrand: null, brands: [] } as any}>
        <VideoTemplatesScreen navigation={{ navigate: jest.fn(), goBack: jest.fn() } as any} />
      </BrandContext.Provider>
    );

    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });
    fireEvent.press(screen.getByText("Galerie"));

    // Even if image is picked, canGenerate() returns false without brandId
    await waitFor(() => {
      expect(videoTemplatesApi.generateBreakoutV4).not.toHaveBeenCalled();
    });
  });
});

// ─── Template Re-Selection ────────────────────────────────────

describe("VideoTemplatesScreen — Changement de template", () => {
  test("selectionner un autre template remet le picker a zero", async () => {
    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });

    // Switch to Promo Flash
    fireEvent.press(screen.getByText("Promo Flash"));
    await waitFor(() => {
      // Still shows single photo picker for Promo Flash
      expect(screen.getAllByText("Galerie").length).toBeGreaterThanOrEqual(1);
    });
  });

  test("selectionner Showcase depuis Breakout affiche picker 3 photos", async () => {
    renderScreen();
    fireEvent.press(screen.getByText("Breakout V4"));
    await waitFor(() => { expect(screen.getByText("Galerie")).toBeTruthy(); });

    fireEvent.press(screen.getByText("Showcase Plats"));
    await waitFor(() => {
      expect(screen.getByText("3 photos requises")).toBeTruthy();
    });
  });
});
