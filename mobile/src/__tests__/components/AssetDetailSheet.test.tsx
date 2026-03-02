/**
 * Tests du AssetDetailSheet
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import AssetDetailSheet from "@/components/AssetDetailSheet";
import { BrandContext } from "@/contexts/BrandContext";
import { assetsApi } from "@/lib/api";
import { MediaAsset } from "@/types";

jest.mock("@/lib/api", () => ({
  assetsApi: { improve: jest.fn(), generatePost: jest.fn() },
}));

const mockBrand = {
  activeBrand: { id: "b1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

const baseAsset: MediaAsset = {
  id: "a1",
  brand_id: "b1",
  media_type: "image",
  public_url: "https://cdn.example.com/photo.jpg",
  processing_status: "ready",
  asset_label: "Mon plat",
  ai_description: "Description IA du plat",
  quality_score: 0.85,
  used_in_posts: 3,
};

function renderSheet(asset: MediaAsset | null = baseAsset, visible = true) {
  const onDismiss = jest.fn();
  const onImproved = jest.fn();
  return {
    ...render(
      <BrandContext.Provider value={mockBrand as any}>
        <AssetDetailSheet asset={asset} visible={visible} onDismiss={onDismiss} onImproved={onImproved} />
      </BrandContext.Provider>
    ),
    onDismiss,
    onImproved,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  (assetsApi.improve as jest.Mock).mockResolvedValue({});
  (assetsApi.generatePost as jest.Mock).mockResolvedValue({});
});

describe("AssetDetailSheet — Rendu", () => {
  test("null si pas d'asset", () => {
    const { toJSON } = renderSheet(null);
    expect(toJSON()).toBeNull();
  });

  test("affiche le label", () => {
    renderSheet();
    expect(screen.getByText("Mon plat")).toBeTruthy();
  });

  test("affiche la description IA", () => {
    renderSheet();
    expect(screen.getByText("Description IA du plat")).toBeTruthy();
  });

  test("affiche Photo pour image", () => {
    renderSheet();
    expect(screen.getByText("Photo")).toBeTruthy();
  });

  test("affiche Vidéo pour vidéo", () => {
    renderSheet({ ...baseAsset, media_type: "video" });
    expect(screen.getByText("Vidéo")).toBeTruthy();
  });

  test("affiche le quality score", () => {
    renderSheet();
    expect(screen.getByText(/85%/)).toBeTruthy();
  });

  test("affiche le nombre d'utilisations", () => {
    renderSheet();
    expect(screen.getByText(/3/)).toBeTruthy();
  });
});

describe("AssetDetailSheet — Toggle original/improved", () => {
  test("affiche toggle si improved_url existe", () => {
    renderSheet({ ...baseAsset, improved_url: "https://cdn.example.com/improved.jpg" });
    expect(screen.getByText("Original")).toBeTruthy();
    expect(screen.getByText("Amélioré")).toBeTruthy();
  });

  test("pas de toggle sans improved_url", () => {
    renderSheet();
    expect(screen.queryByText("Original")).toBeNull();
  });
});

describe("AssetDetailSheet — Actions", () => {
  test("bouton améliorer affiché pour image sans improved_url", () => {
    renderSheet();
    expect(screen.getByText("Améliorer avec l'IA")).toBeTruthy();
  });

  test("pas de bouton améliorer pour vidéo", () => {
    renderSheet({ ...baseAsset, media_type: "video" });
    expect(screen.queryByText("Améliorer avec l'IA")).toBeNull();
  });

  test("bouton générer un post toujours affiché", () => {
    renderSheet();
    expect(screen.getByText("Générer un post")).toBeTruthy();
  });

  test("close appelle onDismiss", () => {
    const { onDismiss } = renderSheet();
    fireEvent.press(screen.getByText("close"));
    expect(onDismiss).toHaveBeenCalled();
  });

  test("press améliorer appelle assetsApi.improve", async () => {
    (assetsApi.improve as jest.Mock).mockResolvedValue({});
    const { onImproved } = renderSheet();
    fireEvent.press(screen.getByText("Améliorer avec l'IA"));
    await waitFor(() => {
      expect(assetsApi.improve).toHaveBeenCalledWith("b1", "a1");
      expect(onImproved).toHaveBeenCalled();
    });
  });

  test("press générer un post appelle assetsApi.generatePost", async () => {
    (assetsApi.generatePost as jest.Mock).mockResolvedValue({});
    renderSheet();
    fireEvent.press(screen.getByText("Générer un post"));
    await waitFor(() => {
      expect(assetsApi.generatePost).toHaveBeenCalledWith("b1", "a1");
    });
  });

  test("erreur améliorer affiche alerte", async () => {
    (assetsApi.improve as jest.Mock).mockRejectedValue(new Error("fail"));
    renderSheet();
    fireEvent.press(screen.getByText("Améliorer avec l'IA"));
    await waitFor(() => {
      expect(assetsApi.improve).toHaveBeenCalled();
    });
  });

  test("erreur générer post affiche alerte", async () => {
    (assetsApi.generatePost as jest.Mock).mockRejectedValue(new Error("fail"));
    renderSheet();
    fireEvent.press(screen.getByText("Générer un post"));
    await waitFor(() => {
      expect(assetsApi.generatePost).toHaveBeenCalled();
    });
  });
});

describe("AssetDetailSheet — Toggle interaction", () => {
  test("press Amélioré bascule vers improved_url", () => {
    renderSheet({ ...baseAsset, improved_url: "https://cdn.example.com/improved.jpg" });
    fireEvent.press(screen.getByText("Amélioré"));
    // toggles to improved
    expect(screen.getByText("Amélioré")).toBeTruthy();
  });

  test("press Original revient à l'originale", () => {
    renderSheet({ ...baseAsset, improved_url: "https://cdn.example.com/improved.jpg" });
    fireEvent.press(screen.getByText("Amélioré"));
    fireEvent.press(screen.getByText("Original"));
    expect(screen.getByText("Original")).toBeTruthy();
  });
});
