/**
 * Tests du AssetCard
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react-native";
import AssetCard from "@/components/AssetCard";
import { MediaAsset } from "@/types";

const baseAsset: MediaAsset = {
  id: "a1",
  brand_id: "b1",
  media_type: "image",
  public_url: "https://cdn.example.com/photo.jpg",
  thumbnail_url: "https://cdn.example.com/thumb.jpg",
  improved_url: null,
  asset_label: "Test",
  ai_description: null,
  quality_score: null,
  used_in_posts: 0,
  created_at: "2026-01-01",
};

describe("AssetCard — Rendu", () => {
  test("affiche l'image", () => {
    const onPress = jest.fn();
    render(<AssetCard asset={baseAsset} onPress={onPress} />);
    // Component renders without error
    expect(onPress).not.toHaveBeenCalled();
  });

  test("press appelle onPress", () => {
    const onPress = jest.fn();
    const { root } = render(<AssetCard asset={baseAsset} onPress={onPress} />);
    fireEvent.press(root);
    expect(onPress).toHaveBeenCalled();
  });

  test("affiche badge HD si quality_score >= 0.8", () => {
    const onPress = jest.fn();
    const hdAsset = { ...baseAsset, quality_score: 0.95 };
    render(<AssetCard asset={hdAsset} onPress={onPress} />);
    expect(screen.getByText("HD")).toBeTruthy();
  });

  test("pas de badge HD si quality_score < 0.8", () => {
    const onPress = jest.fn();
    const lowAsset = { ...baseAsset, quality_score: 0.5 };
    render(<AssetCard asset={lowAsset} onPress={onPress} />);
    expect(screen.queryByText("HD")).toBeNull();
  });

  test("affiche emoji improved si improved_url", () => {
    const onPress = jest.fn();
    const improved = { ...baseAsset, improved_url: "https://cdn.example.com/improved.jpg" };
    render(<AssetCard asset={improved} onPress={onPress} />);
    expect(screen.getByText("✨")).toBeTruthy();
  });

  test("affiche play icon pour vidéo", () => {
    const onPress = jest.fn();
    const video = { ...baseAsset, media_type: "video" as const };
    render(<AssetCard asset={video} onPress={onPress} />);
    expect(screen.getByText("play")).toBeTruthy();
  });
});
