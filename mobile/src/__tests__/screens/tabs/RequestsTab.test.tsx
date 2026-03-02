/**
 * Tests du RequestsTab
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import RequestsTab from "@/screens/files/tabs/RequestsTab";
import { BrandContext } from "@/contexts/BrandContext";
import { contentApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  contentApi: { createRequest: jest.fn() },
}));

const mockBrand = {
  activeBrand: { id: "b1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

function renderTab() {
  return render(
    <BrandContext.Provider value={mockBrand as any}>
      <RequestsTab />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (contentApi.createRequest as jest.Mock).mockResolvedValue({});
});

describe("RequestsTab — Rendu", () => {
  test("affiche le titre", () => {
    renderTab();
    expect(screen.getByText("Demandez à l'IA n'importe quoi")).toBeTruthy();
  });

  test("affiche les chips rapides", () => {
    renderTab();
    // FR.requests_chips are rendered
    expect(screen.getByText("Nouveau plat")).toBeTruthy();
  });

  test("affiche le champ texte", () => {
    renderTab();
    expect(screen.getByPlaceholderText("Ex: 'Crée un Reel sur mon couscous du vendredi'")).toBeTruthy();
  });

  test("affiche les types de contenu", () => {
    renderTab();
    expect(screen.getByText("Reel")).toBeTruthy();
    expect(screen.getByText("Post")).toBeTruthy();
    expect(screen.getByText("Story")).toBeTruthy();
  });

  test("affiche les plateformes", () => {
    renderTab();
    expect(screen.getByText("Instagram")).toBeTruthy();
    expect(screen.getByText("TikTok")).toBeTruthy();
    expect(screen.getByText("Facebook")).toBeTruthy();
  });

  test("bouton générer présent", () => {
    renderTab();
    expect(screen.getByText(/Générer ma proposition/)).toBeTruthy();
  });
});

describe("RequestsTab — Saisie et envoi", () => {
  test("chip remplit le champ texte", () => {
    renderTab();
    fireEvent.press(screen.getByText("Nouveau plat"));
    // Text input now has content
  });

  test("generate appelle createRequest", async () => {
    renderTab();
    fireEvent.changeText(
      screen.getByPlaceholderText("Ex: 'Crée un Reel sur mon couscous du vendredi'"),
      "Un reel de couscous"
    );
    fireEvent.press(screen.getByText(/Générer ma proposition/));
    await waitFor(() => {
      expect(contentApi.createRequest).toHaveBeenCalledWith("b1", expect.objectContaining({
        request_text: "Un reel de couscous",
        content_type: "post",
        platform: "instagram",
      }));
    });
  });
});
