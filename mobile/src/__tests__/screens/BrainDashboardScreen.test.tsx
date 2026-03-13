/**
 * Tests du BrainDashboardScreen
 */

import React from "react";
import { render, renderAsync, screen, waitFor } from "@testing-library/react-native";
import BrainDashboardScreen from "@/screens/brain/BrainDashboardScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { brainApi } from "@/lib/api";

jest.setTimeout(60000);

jest.mock("@/lib/api", () => ({
  brainApi: {
    status: jest.fn(),
    visualStatus: jest.fn(),
    recall: jest.fn(),
  },
}));

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ goBack: jest.fn(), navigate: jest.fn() }),
  useRoute: () => ({ params: {} }),
}));

const mockBrand = {
  activeBrand: { id: "brand-1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

const mockBrainStatus = {
  total_memories: 42,
  memory_counts: { episodic: 15, semantic: 12, procedural: 8, reflection: 7 },
  maturity: 65,
  maturity_label: "Compétent",
};

const mockVisualStatus = {
  total_visuals: 30,
  scored_visuals: 18,
  active_templates: 5,
  maturity: 45,
};

const mockMemories = [
  {
    id: "mem-1",
    brand_id: "brand-1",
    memory_type: "episodic",
    content: "Le client a aimé le tajine",
    confidence: 0.85,
    access_count: 3,
    similarity: 0.92,
    created_at: "2026-01-01",
  },
  {
    id: "mem-2",
    brand_id: "brand-1",
    memory_type: "semantic",
    content: "Le restaurant est connu pour ses couscous",
    confidence: 0.9,
    access_count: 5,
    created_at: "2026-01-02",
  },
];

async function renderBrain(brand = mockBrand) {
  return renderAsync(
    <BrandContext.Provider value={brand as any}>
      <BrainDashboardScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (brainApi.status as jest.Mock).mockResolvedValue({ data: mockBrainStatus });
  (brainApi.visualStatus as jest.Mock).mockResolvedValue({ data: mockVisualStatus });
  (brainApi.recall as jest.Mock).mockResolvedValue({ data: { memories: mockMemories } });
});

describe("BrainDashboardScreen — Rendu", () => {
  test("affiche le titre 'Cerveau IA'", async () => {
    await renderBrain();
    expect(screen.getByText("Cerveau IA")).toBeTruthy();
  });

  test("affiche le sous-titre", async () => {
    await renderBrain();
    expect(screen.getByText("Mémoire et apprentissage de votre marque")).toBeTruthy();
  });
});

describe("BrainDashboardScreen — BrandBrain", () => {
  test("affiche BrandBrain — Texte", async () => {
    await renderBrain();
    expect(screen.getByText("BrandBrain — Texte")).toBeTruthy();
  });

  test("affiche le label de maturité", async () => {
    await renderBrain();
    expect(screen.getByText("Compétent")).toBeTruthy();
    expect(screen.getByText("65%")).toBeTruthy();
  });

  test("affiche les compteurs de mémoire", async () => {
    await renderBrain();
    expect(screen.getByText("Épisodiques")).toBeTruthy();
    expect(screen.getByText("Sémantiques")).toBeTruthy();
    expect(screen.getByText("Procédurales")).toBeTruthy();
    expect(screen.getByText("Réflexions")).toBeTruthy();
  });

  test("affiche le total souvenirs", async () => {
    await renderBrain();
    expect(screen.getByText("42 souvenirs au total")).toBeTruthy();
  });
});

describe("BrainDashboardScreen — VisualBrain", () => {
  test("affiche VisualBrain — Images", async () => {
    await renderBrain();
    expect(screen.getByText("VisualBrain — Images")).toBeTruthy();
  });

  test("affiche les stats visuelles", async () => {
    await renderBrain();
    expect(screen.getByText("Visuels")).toBeTruthy();
    expect(screen.getByText("Évalués")).toBeTruthy();
    expect(screen.getByText("Templates")).toBeTruthy();
  });

  test("affiche Maturité visuelle", async () => {
    await renderBrain();
    expect(screen.getByText("Maturité visuelle")).toBeTruthy();
    expect(screen.getByText("45%")).toBeTruthy();
  });
});

describe("BrainDashboardScreen — Souvenirs récents", () => {
  test("affiche les souvenirs récents", async () => {
    await renderBrain();
    expect(screen.getByText("Souvenirs récents")).toBeTruthy();
    expect(screen.getByText("Le client a aimé le tajine")).toBeTruthy();
    expect(screen.getByText("Le restaurant est connu pour ses couscous")).toBeTruthy();
  });

  test("affiche la confiance en pourcentage", async () => {
    await renderBrain();
    expect(screen.getByText(/Confiance: 85%/)).toBeTruthy();
    expect(screen.getByText(/Confiance: 90%/)).toBeTruthy();
  });

  test("affiche la similarité quand présente", async () => {
    await renderBrain();
    expect(screen.getByText(/Similarité: 92%/)).toBeTruthy();
  });
});

describe("BrainDashboardScreen — Empty state", () => {
  test("affiche empty state quand pas de données", async () => {
    (brainApi.status as jest.Mock).mockRejectedValue(new Error("fail"));
    (brainApi.visualStatus as jest.Mock).mockRejectedValue(new Error("fail"));
    (brainApi.recall as jest.Mock).mockRejectedValue(new Error("fail"));
    await renderBrain();
    expect(screen.getByText("Cerveau en cours d'initialisation")).toBeTruthy();
  });
});

describe("BrainDashboardScreen — Sans brand", () => {
  test("ne charge pas sans activeBrand", async () => {
    render(
      <BrandContext.Provider value={{ activeBrand: null, brands: [] } as any}>
        <BrainDashboardScreen />
      </BrandContext.Provider>
    );
    // Wait for loading to finish
    await waitFor(() => {
      expect(brainApi.status).not.toHaveBeenCalled();
    });
  });
});
