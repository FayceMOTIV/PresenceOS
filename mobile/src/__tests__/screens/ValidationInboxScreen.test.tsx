/**
 * Tests du ValidationInboxScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import { Alert } from "react-native";
import ValidationInboxScreen from "@/screens/validation/ValidationInboxScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { proposalsApi } from "@/lib/api";

jest.spyOn(Alert, "alert");

jest.mock("@/lib/api", () => ({
  proposalsApi: {
    list: jest.fn(),
    approve: jest.fn(),
    reject: jest.fn(),
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

const mockProposals = [
  {
    id: "p1",
    caption: "Découvrez notre tajine !",
    hashtags: ["#tajine", "#restaurant"],
    platform: "instagram",
    proposal_type: "post",
    confidence_score: 0.85,
    status: "pending",
    brand_id: "brand-1",
    source: "autopilot",
    created_at: "2026-01-01",
  },
  {
    id: "p2",
    caption: "Story du week-end",
    hashtags: [],
    platform: "instagram",
    proposal_type: "story",
    confidence_score: 0.72,
    status: "pending",
    brand_id: "brand-1",
    source: "autopilot",
    created_at: "2026-01-02",
  },
];

function renderValidation(brand = mockBrand) {
  return render(
    <BrandContext.Provider value={brand as any}>
      <ValidationInboxScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (proposalsApi.list as jest.Mock).mockResolvedValue({
    data: { proposals: mockProposals },
  });
  (proposalsApi.approve as jest.Mock).mockResolvedValue({ data: { status: "approved" } });
  (proposalsApi.reject as jest.Mock).mockResolvedValue({ data: { status: "rejected" } });
});

describe("ValidationInboxScreen — Rendu", () => {
  test("affiche le titre Validation", async () => {
    renderValidation();
    await waitFor(() => {
      expect(screen.getByText("Validation")).toBeTruthy();
    });
  });

  test("affiche le sous-titre", async () => {
    renderValidation();
    await waitFor(() => {
      expect(screen.getByText(/Contenus générés par l'IA en attente/)).toBeTruthy();
    });
  });

  test("affiche le badge avec le nombre de proposals", async () => {
    renderValidation();
    await waitFor(() => {
      expect(screen.getByText("2")).toBeTruthy();
    });
  });
});

describe("ValidationInboxScreen — Cards", () => {
  test("affiche les captions", async () => {
    renderValidation();
    await waitFor(() => {
      expect(screen.getByText("Découvrez notre tajine !")).toBeTruthy();
      expect(screen.getByText("Story du week-end")).toBeTruthy();
    });
  });

  test("affiche les hashtags", async () => {
    renderValidation();
    await waitFor(() => {
      expect(screen.getByText("#tajine #restaurant")).toBeTruthy();
    });
  });

  test("affiche le type de contenu", async () => {
    renderValidation();
    await waitFor(() => {
      expect(screen.getAllByText("Post").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Story").length).toBeGreaterThanOrEqual(1);
    });
  });

  test("affiche le score IA", async () => {
    renderValidation();
    await waitFor(() => {
      expect(screen.getByText("Score IA : 85%")).toBeTruthy();
      expect(screen.getByText("Score IA : 72%")).toBeTruthy();
    });
  });

  test("affiche les boutons d'action", async () => {
    renderValidation();
    await waitFor(() => {
      const rejectBtns = screen.getAllByText("Rejeter");
      const scheduleBtns = screen.getAllByText("Planifier");
      const publishBtns = screen.getAllByText("Publier");
      expect(rejectBtns.length).toBe(2);
      expect(scheduleBtns.length).toBe(2);
      expect(publishBtns.length).toBe(2);
    });
  });
});

describe("ValidationInboxScreen — Actions", () => {
  test("publier appelle proposalsApi.approve", async () => {
    renderValidation();
    await waitFor(() => {
      expect(screen.getByText("Découvrez notre tajine !")).toBeTruthy();
    });
    const publishBtns = screen.getAllByText("Publier");
    fireEvent.press(publishBtns[0]);
    await waitFor(() => {
      expect(proposalsApi.approve).toHaveBeenCalledWith("brand-1", "p1");
    });
  });

  test("rejeter affiche confirmation Alert", async () => {
    renderValidation();
    await waitFor(() => {
      expect(screen.getByText("Découvrez notre tajine !")).toBeTruthy();
    });
    const rejectBtns = screen.getAllByText("Rejeter");
    fireEvent.press(rejectBtns[0]);
    expect(Alert.alert).toHaveBeenCalledWith(
      "Rejeter ce post ?",
      "Cette action est irréversible.",
      expect.arrayContaining([
        expect.objectContaining({ text: "Annuler" }),
        expect.objectContaining({ text: "Rejeter", style: "destructive" }),
      ])
    );
  });

  test("confirmer rejet appelle proposalsApi.reject", async () => {
    renderValidation();
    await waitFor(() => {
      expect(screen.getByText("Découvrez notre tajine !")).toBeTruthy();
    });
    const rejectBtns = screen.getAllByText("Rejeter");
    fireEvent.press(rejectBtns[0]);
    const alertCall = (Alert.alert as jest.Mock).mock.calls[0];
    const buttons = alertCall[2];
    const destructiveBtn = buttons.find((b: any) => b.style === "destructive");
    await destructiveBtn.onPress();
    expect(proposalsApi.reject).toHaveBeenCalledWith("brand-1", "p1");
  });

  test("planifier appelle proposalsApi.approve avec date", async () => {
    renderValidation();
    await waitFor(() => {
      expect(screen.getByText("Découvrez notre tajine !")).toBeTruthy();
    });
    const scheduleBtns = screen.getAllByText("Planifier");
    fireEvent.press(scheduleBtns[0]);
    await waitFor(() => {
      expect(proposalsApi.approve).toHaveBeenCalledWith(
        "brand-1",
        "p1",
        expect.any(String) // ISO date string
      );
    });
  });
});

describe("ValidationInboxScreen — Empty state", () => {
  test("affiche 'Tout est validé !' quand pas de proposals", async () => {
    (proposalsApi.list as jest.Mock).mockResolvedValue({
      data: { proposals: [] },
    });
    renderValidation();
    await waitFor(() => {
      expect(screen.getByText("Tout est validé !")).toBeTruthy();
      expect(screen.getByText(/Aucun contenu en attente/)).toBeTruthy();
    });
  });
});

describe("ValidationInboxScreen — API", () => {
  test("appelle proposalsApi.list avec status pending", async () => {
    renderValidation();
    await waitFor(() => {
      expect(proposalsApi.list).toHaveBeenCalledWith("brand-1", { status: "pending" });
    });
  });

  test("ne charge pas sans activeBrand", async () => {
    render(
      <BrandContext.Provider value={{ activeBrand: null, brands: [] } as any}>
        <ValidationInboxScreen />
      </BrandContext.Provider>
    );
    await waitFor(() => {
      expect(proposalsApi.list).not.toHaveBeenCalled();
    });
  });
});
