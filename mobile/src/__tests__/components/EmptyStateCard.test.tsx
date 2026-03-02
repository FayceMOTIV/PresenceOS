/**
 * Tests du composant EmptyStateCard
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react-native";
import EmptyStateCard from "@/components/EmptyStateCard";

describe("EmptyStateCard", () => {
  test("affiche emoji, titre et body", () => {
    render(
      <EmptyStateCard
        emoji="🤖"
        title="Aucune proposition"
        body="Ajoutez du contenu pour commencer"
      />
    );
    expect(screen.getByText("🤖")).toBeTruthy();
    expect(screen.getByText("Aucune proposition")).toBeTruthy();
    expect(screen.getByText("Ajoutez du contenu pour commencer")).toBeTruthy();
  });

  test("affiche le CTA et gère le press", () => {
    const onCta = jest.fn();
    render(
      <EmptyStateCard
        emoji="📷"
        title="Titre"
        body="Body"
        ctaLabel="Ajouter"
        onCta={onCta}
      />
    );
    const cta = screen.getByText("Ajouter");
    expect(cta).toBeTruthy();
    fireEvent.press(cta);
    expect(onCta).toHaveBeenCalledTimes(1);
  });

  test("affiche le bouton secondaire", () => {
    const onSecondary = jest.fn();
    render(
      <EmptyStateCard
        emoji="✨"
        title="Titre"
        body="Body"
        secondaryLabel="Plus tard"
        onSecondary={onSecondary}
      />
    );
    const secondary = screen.getByText("Plus tard");
    fireEvent.press(secondary);
    expect(onSecondary).toHaveBeenCalledTimes(1);
  });

  test("ne rend pas le CTA si pas de ctaLabel", () => {
    const { toJSON } = render(
      <EmptyStateCard emoji="🎯" title="Titre" body="Body" />
    );
    expect(toJSON()).toBeTruthy();
    expect(screen.queryByText("Ajouter")).toBeNull();
  });
});
