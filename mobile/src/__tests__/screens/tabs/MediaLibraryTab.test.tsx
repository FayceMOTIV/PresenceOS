/**
 * Tests du MediaLibraryTab
 */

import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react-native";
import MediaLibraryTab from "@/screens/files/tabs/MediaLibraryTab";
import { BrandContext } from "@/contexts/BrandContext";
import { assetsApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  assetsApi: { list: jest.fn(), improve: jest.fn(), generatePost: jest.fn() },
}));

jest.mock("@/components/AssetCard", () => {
  const { Text } = require("react-native");
  return ({ asset, onPress }: any) => <Text onPress={onPress}>{asset.asset_label}</Text>;
});

jest.mock("@/components/AssetDetailSheet", () => {
  const { Text } = require("react-native");
  return ({ asset, visible }: any) => visible ? <Text>Detail: {asset?.asset_label}</Text> : null;
});

jest.mock("@/components/FAB", () => {
  const { Text } = require("react-native");
  return ({ onPress }: any) => <Text onPress={onPress}>FAB</Text>;
});

jest.mock("@/components/EmptyStateCard", () => {
  const { Text } = require("react-native");
  return ({ title, onCta }: any) => <Text onPress={onCta}>{title}</Text>;
});

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
      <MediaLibraryTab />
    </BrandContext.Provider>
  );
}

const mockAssets = [
  { id: "a1", brand_id: "b1", media_type: "image", public_url: "https://cdn.test/1.jpg", thumbnail_url: null, improved_url: null, asset_label: "Photo 1", ai_description: null, quality_score: null, used_in_posts: 0, created_at: "2026-01-01" },
  { id: "a2", brand_id: "b1", media_type: "video", public_url: "https://cdn.test/2.mp4", thumbnail_url: null, improved_url: null, asset_label: "Vidéo 1", ai_description: null, quality_score: null, used_in_posts: 0, created_at: "2026-01-01" },
];

beforeEach(() => {
  jest.clearAllMocks();
  (assetsApi.list as jest.Mock).mockResolvedValue({ data: { assets: mockAssets } });
});

describe("MediaLibraryTab — Rendu", () => {
  test("affiche les assets après chargement", async () => {
    renderTab();
    await waitFor(() => {
      expect(screen.getByText("Photo 1")).toBeTruthy();
      expect(screen.getByText("Vidéo 1")).toBeTruthy();
    });
  });

  test("affiche le FAB", async () => {
    renderTab();
    await waitFor(() => {
      expect(screen.getByText("FAB")).toBeTruthy();
    });
  });

  test("empty state si aucun asset", async () => {
    (assetsApi.list as jest.Mock).mockResolvedValue({ data: { assets: [] } });
    renderTab();
    await waitFor(() => {
      expect(screen.getByText("Vos photos font la différence")).toBeTruthy();
    });
  });
});

describe("MediaLibraryTab — Interactions", () => {
  test("press asset ouvre le detail sheet", async () => {
    renderTab();
    await waitFor(() => {
      expect(screen.getByText("Photo 1")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Photo 1"));
    await waitFor(() => {
      expect(screen.getByText("Detail: Photo 1")).toBeTruthy();
    });
  });

  test("FAB navigue vers AssetUpload", async () => {
    renderTab();
    await waitFor(() => {
      expect(screen.getByText("FAB")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("FAB"));
    expect(mockNavigate).toHaveBeenCalledWith("AssetUpload");
  });
});
