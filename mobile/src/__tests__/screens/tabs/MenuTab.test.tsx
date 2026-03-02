/**
 * Tests du MenuTab
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react-native";
import MenuTab from "@/screens/files/tabs/MenuTab";
import { BrandContext } from "@/contexts/BrandContext";
import { contentApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  contentApi: { listDishes: jest.fn(), deleteDish: jest.fn() },
}));

jest.mock("@/components/DishCard", () => {
  const { Text } = require("react-native");
  return ({ dish, onPress }: any) => <Text onPress={onPress}>{dish.name}</Text>;
});

jest.mock("@/components/EmptyStateCard", () => {
  const { Text } = require("react-native");
  return ({ title, onCta }: any) => <Text onPress={onCta}>{title}</Text>;
});

jest.mock("@/navigation/TabNavigator", () => ({}));

const mockNavigate = jest.fn();
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ navigate: mockNavigate }),
}));

const mockBrand = {
  activeBrand: { id: "b1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

function renderTab() {
  return render(
    <BrandContext.Provider value={mockBrand as any}>
      <MenuTab />
    </BrandContext.Provider>
  );
}

const mockDishes = [
  { id: "d1", brand_id: "b1", name: "Couscous", description: "Semoule", price: 12, category: "plats", is_featured: true, cover_asset_id: null, created_at: "2026-01-01" },
  { id: "d2", brand_id: "b1", name: "Tiramisu", description: "Mascarpone", price: 8, category: "desserts", is_featured: false, cover_asset_id: null, created_at: "2026-01-01" },
];

beforeEach(() => {
  jest.clearAllMocks();
  (contentApi.listDishes as jest.Mock).mockResolvedValue({ data: { dishes: mockDishes } });
});

describe("MenuTab — Rendu", () => {
  test("affiche les plats après chargement", async () => {
    renderTab();
    await waitFor(() => {
      expect(screen.getByText("Couscous")).toBeTruthy();
      expect(screen.getByText("Tiramisu")).toBeTruthy();
    });
  });

  test("affiche les sections par catégorie", async () => {
    renderTab();
    await waitFor(() => {
      expect(screen.getByText("Plats")).toBeTruthy();
      expect(screen.getByText("Desserts")).toBeTruthy();
    });
  });

  test("affiche le bouton scanner", async () => {
    renderTab();
    await waitFor(() => {
      expect(screen.getByText("Scanner ma carte")).toBeTruthy();
    });
  });

  test("empty state si aucun plat", async () => {
    (contentApi.listDishes as jest.Mock).mockResolvedValue({ data: { dishes: [] } });
    renderTab();
    await waitFor(() => {
      expect(screen.getByText("Votre menu = le cœur de l'IA")).toBeTruthy();
    });
  });
});

describe("MenuTab — API", () => {
  test("appelle listDishes au montage", async () => {
    renderTab();
    await waitFor(() => {
      expect(contentApi.listDishes).toHaveBeenCalledWith("b1");
    });
  });
});
