/**
 * Tests du composant Badge
 */

import React from "react";
import { render, screen } from "@testing-library/react-native";
import Badge from "@/components/ui/Badge";

describe("Badge", () => {
  test("affiche le label par défaut pour 'pending'", () => {
    render(<Badge status="pending" />);
    expect(screen.getByText("En attente")).toBeTruthy();
  });

  test("affiche le label par défaut pour 'approved'", () => {
    render(<Badge status="approved" />);
    expect(screen.getByText("Approuve")).toBeTruthy();
  });

  test("affiche le label par défaut pour 'published'", () => {
    render(<Badge status="published" />);
    expect(screen.getByText("Publie")).toBeTruthy();
  });

  test("affiche le label par défaut pour 'rejected'", () => {
    render(<Badge status="rejected" />);
    expect(screen.getByText("Rejete")).toBeTruthy();
  });

  test("affiche un label custom quand fourni", () => {
    render(<Badge status="pending" label="Personnalisé" />);
    expect(screen.getByText("Personnalisé")).toBeTruthy();
  });

  test("gère un statut inconnu gracieusement", () => {
    render(<Badge status="unknown_status" />);
    expect(screen.getByText("unknown_status")).toBeTruthy();
  });

  test("supporte la taille sm", () => {
    const { toJSON } = render(<Badge status="pending" size="sm" />);
    expect(toJSON()).toBeTruthy();
  });
});
