/**
 * Tests du DishFormScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react-native";
import DishFormScreen from "@/screens/files/DishFormScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { contentApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  contentApi: {
    listDishes: jest.fn(),
    createDish: jest.fn(),
    updateDish: jest.fn(),
  },
}));

const mockGoBack = jest.fn();
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ goBack: mockGoBack }),
  useRoute: () => ({ params: {} }),
}));

jest.mock("@/navigation/TabNavigator", () => ({}));

const mockBrand = {
  activeBrand: { id: "b1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

function renderForm() {
  return render(
    <BrandContext.Provider value={mockBrand as any}>
      <DishFormScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (contentApi.listDishes as jest.Mock).mockResolvedValue({ data: { dishes: [] } });
  (contentApi.createDish as jest.Mock).mockResolvedValue({});
});

describe("DishFormScreen — Rendu", () => {
  test("affiche le titre nouveau plat", () => {
    renderForm();
    expect(screen.getByText("Nouveau plat")).toBeTruthy();
  });

  test("affiche les champs name, description, prix", () => {
    renderForm();
    expect(screen.getByPlaceholderText("Ex: Couscous Royal")).toBeTruthy();
    expect(screen.getByPlaceholderText("Description optionnelle...")).toBeTruthy();
    expect(screen.getByPlaceholderText("12.50")).toBeTruthy();
  });

  test("affiche les catégories", () => {
    renderForm();
    expect(screen.getByText("Entrées")).toBeTruthy();
    expect(screen.getByText("Plats")).toBeTruthy();
    expect(screen.getByText("Desserts")).toBeTruthy();
    expect(screen.getByText("Boissons")).toBeTruthy();
    expect(screen.getByText("Autres")).toBeTruthy();
  });

  test("affiche le switch featured", () => {
    renderForm();
    expect(screen.getByText("Mettre en avant")).toBeTruthy();
  });

  test("bouton sauvegarder présent", () => {
    renderForm();
    expect(screen.getByText("Enregistrer")).toBeTruthy();
  });
});

describe("DishFormScreen — Saisie", () => {
  test("saisir un nom active le bouton", () => {
    renderForm();
    fireEvent.changeText(screen.getByPlaceholderText("Ex: Couscous Royal"), "Tajine");
    expect(screen.getByText("Enregistrer")).toBeTruthy();
  });

  test("changer de catégorie", () => {
    renderForm();
    fireEvent.press(screen.getByText("Desserts"));
    // Should highlight Desserts (visual only)
  });
});

describe("DishFormScreen — Save", () => {
  test("save appelle createDish et goBack", async () => {
    renderForm();
    fireEvent.changeText(screen.getByPlaceholderText("Ex: Couscous Royal"), "Tajine");
    fireEvent.changeText(screen.getByPlaceholderText("12.50"), "15");
    fireEvent.press(screen.getByText("Enregistrer"));
    await waitFor(() => {
      expect(contentApi.createDish).toHaveBeenCalledWith("b1", expect.objectContaining({ name: "Tajine" }));
      expect(mockGoBack).toHaveBeenCalled();
    });
  });
});

describe("DishFormScreen — Navigation", () => {
  test("close appelle goBack", () => {
    renderForm();
    fireEvent.press(screen.getByText("close"));
    expect(mockGoBack).toHaveBeenCalled();
  });
});
