/**
 * Tests du BriefDuJourScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import { Alert } from "react-native";
import BriefDuJourScreen from "@/screens/brief/BriefDuJourScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { briefApi } from "@/lib/api";

jest.spyOn(Alert, "alert");

jest.mock("@/lib/api", () => ({
  briefApi: { respond: jest.fn() },
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

function renderWithBrand(brandCtx = mockBrand) {
  return render(
    <BrandContext.Provider value={brandCtx as any}>
      <BriefDuJourScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe("BriefDuJourScreen — Rendu", () => {
  test("affiche le titre", () => {
    renderWithBrand();
    expect(screen.getByText("Votre brief du matin")).toBeTruthy();
  });

  test("affiche le sous-titre", () => {
    renderWithBrand();
    expect(screen.getByText(/L'IA crée un post sur mesure/)).toBeTruthy();
  });

  test("affiche le placeholder du champ texte", () => {
    renderWithBrand();
    expect(screen.getByPlaceholderText(/Spécial vendredi/)).toBeTruthy();
  });

  test("affiche les chips de raccourci", () => {
    renderWithBrand();
    expect(screen.getByText("Plat du jour")).toBeTruthy();
    expect(screen.getByText("Promotion")).toBeTruthy();
    expect(screen.getByText("Événement")).toBeTruthy();
    expect(screen.getByText("Rien de spécial")).toBeTruthy();
  });

  test("affiche le bouton Générer", () => {
    renderWithBrand();
    expect(screen.getByText("Générer mon post →")).toBeTruthy();
  });
});

describe("BriefDuJourScreen — Interactions", () => {
  test("chip ajoute du texte au champ", () => {
    renderWithBrand();
    fireEvent.press(screen.getByText("Plat du jour"));
    const input = screen.getByPlaceholderText(/Spécial vendredi/);
    expect(input.props.value).toBe("Plat du jour");
  });

  test("plusieurs chips s'ajoutent avec virgule", () => {
    renderWithBrand();
    fireEvent.press(screen.getByText("Plat du jour"));
    fireEvent.press(screen.getByText("Promotion"));
    const input = screen.getByPlaceholderText(/Spécial vendredi/);
    expect(input.props.value).toBe("Plat du jour, promotion");
  });

  test("close button appelle goBack", () => {
    renderWithBrand();
    fireEvent.press(screen.getByText("close"));
    expect(mockGoBack).toHaveBeenCalled();
  });
});

describe("BriefDuJourScreen — Envoi", () => {
  test("envoie le brief et affiche done", async () => {
    (briefApi.respond as jest.Mock).mockResolvedValue({});
    renderWithBrand();
    fireEvent.changeText(screen.getByPlaceholderText(/Spécial vendredi/), "Tajine agneau");
    fireEvent.press(screen.getByText("Générer mon post →"));

    await waitFor(() => {
      expect(briefApi.respond).toHaveBeenCalledWith("brand-1", "Tajine agneau");
      expect(screen.getByText("Post généré !")).toBeTruthy();
      expect(screen.getByText(/L'IA prépare votre post/)).toBeTruthy();
    });
  });

  test("affiche alerte si erreur API", async () => {
    (briefApi.respond as jest.Mock).mockRejectedValue(new Error("fail"));
    renderWithBrand();
    fireEvent.changeText(screen.getByPlaceholderText(/Spécial vendredi/), "Test");
    fireEvent.press(screen.getByText("Générer mon post →"));

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith("Une erreur est survenue — réessayez");
    });
  });

  test("ne soumet pas si champ vide", () => {
    renderWithBrand();
    fireEvent.press(screen.getByText("Générer mon post →"));
    expect(briefApi.respond).not.toHaveBeenCalled();
  });

  test("ne soumet pas sans brandId", () => {
    render(
      <BrandContext.Provider value={{ activeBrand: null, brands: [] } as any}>
        <BriefDuJourScreen />
      </BrandContext.Provider>
    );
    fireEvent.changeText(screen.getByPlaceholderText(/Spécial vendredi/), "test");
    fireEvent.press(screen.getByText("Générer mon post →"));
    expect(briefApi.respond).not.toHaveBeenCalled();
  });
});

describe("BriefDuJourScreen — Done state", () => {
  test("bouton Retour appelle goBack", async () => {
    (briefApi.respond as jest.Mock).mockResolvedValue({});
    renderWithBrand();
    fireEvent.changeText(screen.getByPlaceholderText(/Spécial vendredi/), "Test");
    fireEvent.press(screen.getByText("Générer mon post →"));

    await waitFor(() => {
      expect(screen.getByText("← Retour")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("← Retour"));
    expect(mockGoBack).toHaveBeenCalled();
  });
});
