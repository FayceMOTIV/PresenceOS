/**
 * Tests du FileHubScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import FileHubScreen from "@/screens/files/FileHubScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { kbApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  kbApi: { completeness: jest.fn() },
}));

// Mock tab components to simple text
jest.mock("@/screens/files/tabs/MediaLibraryTab", () => {
  const React = require("react");
  const { Text } = require("react-native");
  return () => <Text>MediaLibraryTab</Text>;
});

jest.mock("@/screens/files/tabs/MenuTab", () => {
  const React = require("react");
  const { Text } = require("react-native");
  return () => <Text>MenuTab</Text>;
});

jest.mock("@/screens/files/tabs/RequestsTab", () => {
  const React = require("react");
  const { Text } = require("react-native");
  return () => <Text>RequestsTab</Text>;
});

// Mock KBCompletenessBar
jest.mock("@/components/KBCompletenessBar", () => {
  const React = require("react");
  const { Text, TouchableOpacity } = require("react-native");
  return function MockKBBar({ score, onPress }: any) {
    return (
      <TouchableOpacity onPress={onPress}>
        <Text>KB Score: {score}%</Text>
      </TouchableOpacity>
    );
  };
});

const mockBrand = {
  activeBrand: { id: "brand-1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

function renderHub(brand = mockBrand) {
  return render(
    <BrandContext.Provider value={brand as any}>
      <FileHubScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (kbApi.completeness as jest.Mock).mockResolvedValue({
    data: { completeness_score: 42 },
  });
});

describe("FileHubScreen — Rendu", () => {
  test("affiche le titre Ma médiathèque", () => {
    renderHub();
    expect(screen.getByText("Ma médiathèque")).toBeTruthy();
  });

  test("affiche les 3 onglets", () => {
    renderHub();
    expect(screen.getByText("Photos & Vidéos")).toBeTruthy();
    expect(screen.getByText("Mon menu")).toBeTruthy();
    expect(screen.getByText("Demandes IA")).toBeTruthy();
  });

  test("affiche le KB completeness bar", async () => {
    renderHub();
    await waitFor(() => {
      expect(screen.getByText("KB Score: 42%")).toBeTruthy();
    });
  });
});

describe("FileHubScreen — Tabs", () => {
  test("affiche MediaLibraryTab par défaut", () => {
    renderHub();
    expect(screen.getByText("MediaLibraryTab")).toBeTruthy();
  });

  test("switch vers Mon menu", () => {
    renderHub();
    fireEvent.press(screen.getByText("Mon menu"));
    expect(screen.getByText("MenuTab")).toBeTruthy();
  });

  test("switch vers Demandes IA", () => {
    renderHub();
    fireEvent.press(screen.getByText("Demandes IA"));
    expect(screen.getByText("RequestsTab")).toBeTruthy();
  });

  test("KBCompletenessBar onPress switch vers menu", async () => {
    renderHub();
    await waitFor(() => {
      expect(screen.getByText("KB Score: 42%")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("KB Score: 42%"));
    // After press, menu tab should be active (MenuTab visible)
    expect(screen.getByText("MenuTab")).toBeTruthy();
  });
});

describe("FileHubScreen — API", () => {
  test("appelle kbApi.completeness avec brandId", async () => {
    renderHub();
    await waitFor(() => {
      expect(kbApi.completeness).toHaveBeenCalledWith("brand-1");
    });
  });

  test("ne charge pas sans brandId", () => {
    render(
      <BrandContext.Provider value={{ activeBrand: null, brands: [] } as any}>
        <FileHubScreen />
      </BrandContext.Provider>
    );
    expect(kbApi.completeness).not.toHaveBeenCalled();
  });
});
