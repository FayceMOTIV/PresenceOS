/**
 * Tests du DishCard
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react-native";
import DishCard from "@/components/DishCard";
import { Dish } from "@/types";

const baseDish: Dish = {
  id: "d1",
  brand_id: "b1",
  name: "Couscous Royal",
  description: "Semoule, merguez, poulet",
  price: 14.5,
  category: "plats",
  is_available: true,
  is_featured: false,
  ai_post_count: 0,
  display_order: 0,
};

describe("DishCard — Rendu", () => {
  test("affiche le nom du plat", () => {
    render(<DishCard dish={baseDish} onPress={jest.fn()} />);
    expect(screen.getByText("Couscous Royal")).toBeTruthy();
  });

  test("affiche la description", () => {
    render(<DishCard dish={baseDish} onPress={jest.fn()} />);
    expect(screen.getByText("Semoule, merguez, poulet")).toBeTruthy();
  });

  test("affiche le prix", () => {
    render(<DishCard dish={baseDish} onPress={jest.fn()} />);
    expect(screen.getByText("14.5 €")).toBeTruthy();
  });

  test("affiche étoile si featured", () => {
    render(<DishCard dish={{ ...baseDish, is_featured: true }} onPress={jest.fn()} />);
    expect(screen.getByText("⭐")).toBeTruthy();
  });

  test("pas d'étoile si pas featured", () => {
    render(<DishCard dish={baseDish} onPress={jest.fn()} />);
    expect(screen.queryByText("⭐")).toBeNull();
  });

  test("affiche image si cover_asset_id est URL", () => {
    const dish = { ...baseDish, cover_asset_id: "https://cdn.example.com/dish.jpg" };
    render(<DishCard dish={dish} onPress={jest.fn()} />);
    // Image renders without error
  });

  test("affiche icône restaurant si pas d'image", () => {
    render(<DishCard dish={baseDish} onPress={jest.fn()} />);
    expect(screen.getByText("restaurant-outline")).toBeTruthy();
  });
});

describe("DishCard — Interactions", () => {
  test("press appelle onPress", () => {
    const onPress = jest.fn();
    render(<DishCard dish={baseDish} onPress={onPress} />);
    fireEvent.press(screen.getByText("Couscous Royal"));
    expect(onPress).toHaveBeenCalled();
  });

  test("delete visible si onDelete fourni", () => {
    const onDelete = jest.fn();
    render(<DishCard dish={baseDish} onPress={jest.fn()} onDelete={onDelete} />);
    expect(screen.getByText("trash-outline")).toBeTruthy();
  });

  test("delete appelle onDelete", () => {
    const onDelete = jest.fn();
    render(<DishCard dish={baseDish} onPress={jest.fn()} onDelete={onDelete} />);
    fireEvent.press(screen.getByText("trash-outline"));
    expect(onDelete).toHaveBeenCalled();
  });

  test("pas de bouton delete sans onDelete", () => {
    render(<DishCard dish={baseDish} onPress={jest.fn()} />);
    expect(screen.queryByText("trash-outline")).toBeNull();
  });
});
