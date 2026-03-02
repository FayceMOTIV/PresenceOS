/**
 * Tests du ScanMenuScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import ScanMenuScreen from "@/screens/files/ScanMenuScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { menuApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  menuApi: { scan: jest.fn(), importDishes: jest.fn() },
}));

jest.mock("expo-image-picker", () => ({
  requestCameraPermissionsAsync: jest.fn().mockResolvedValue({ status: "granted" }),
  requestMediaLibraryPermissionsAsync: jest.fn().mockResolvedValue({ status: "granted" }),
  launchCameraAsync: jest.fn().mockResolvedValue({
    canceled: false,
    assets: [{ uri: "file://menu.jpg" }],
  }),
  launchImageLibraryAsync: jest.fn().mockResolvedValue({
    canceled: false,
    assets: [{ uri: "file://gallery-menu.jpg" }],
  }),
}));

const mockGoBack = jest.fn();
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ goBack: mockGoBack }),
}));

const mockBrand = {
  activeBrand: { id: "b1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

function renderScan() {
  return render(
    <BrandContext.Provider value={mockBrand as any}>
      <ScanMenuScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (menuApi.scan as jest.Mock).mockResolvedValue({
    data: {
      dishes: [
        { name: "Couscous", category: "plats", price: 12, description: "Semoule fine" },
        { name: "Limonade", category: "boissons", price: 3, description: "" },
      ],
    },
  });
  (menuApi.importDishes as jest.Mock).mockResolvedValue({});
});

describe("ScanMenuScreen — Pick step", () => {
  test("affiche le titre", () => {
    renderScan();
    expect(screen.getByText("Scanner le menu")).toBeTruthy();
  });

  test("affiche le titre de l'étape pick", () => {
    renderScan();
    expect(screen.getByText("Scannez votre menu")).toBeTruthy();
  });

  test("affiche les boutons caméra et galerie", () => {
    renderScan();
    expect(screen.getByText("Caméra")).toBeTruthy();
    expect(screen.getByText("Galerie")).toBeTruthy();
  });
});

describe("ScanMenuScreen — Scan flow", () => {
  test("caméra lance scan et affiche review", async () => {
    renderScan();
    fireEvent.press(screen.getByText("Caméra"));
    await waitFor(() => {
      expect(screen.getByText("2 plats trouvés")).toBeTruthy();
    });
    expect(screen.getByDisplayValue("Couscous")).toBeTruthy();
    expect(screen.getByDisplayValue("Limonade")).toBeTruthy();
  });

  test("galerie lance scan et affiche review", async () => {
    renderScan();
    fireEvent.press(screen.getByText("Galerie"));
    await waitFor(() => {
      expect(screen.getByText("2 plats trouvés")).toBeTruthy();
    });
  });
});

describe("ScanMenuScreen — Navigation", () => {
  test("close appelle goBack", () => {
    renderScan();
    fireEvent.press(screen.getByText("close"));
    expect(mockGoBack).toHaveBeenCalled();
  });
});
