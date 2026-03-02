/**
 * Tests du ProposalsListScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import ProposalsListScreen from "@/screens/proposals/ProposalsListScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { proposalsApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  proposalsApi: { list: jest.fn() },
}));

const mockNav = {
  navigate: jest.fn(),
  goBack: jest.fn(),
  getParent: jest.fn(() => ({ navigate: jest.fn() })),
};
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => mockNav,
  useRoute: () => ({ params: {} }),
}));

const mockBrand = {
  activeBrand: { id: "brand-1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

const mockProposals = [
  { id: "p1", status: "pending", caption: "Caption 1", platform: "instagram", proposal_type: "post", confidence_score: 0.85, created_at: "2026-01-01", brand_id: "brand-1", source: "brief" },
  { id: "p2", status: "approved", caption: "Caption 2", platform: "instagram", proposal_type: "reel", confidence_score: 0.9, created_at: "2026-01-02", brand_id: "brand-1", source: "brief" },
];

function renderWithBrand() {
  return render(
    <BrandContext.Provider value={mockBrand as any}>
      <ProposalsListScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (proposalsApi.list as jest.Mock).mockResolvedValue({ data: { proposals: mockProposals } });
});

describe("ProposalsListScreen — Rendu", () => {
  test("affiche le titre", async () => {
    renderWithBrand();
    expect(screen.getByText("Mes posts IA")).toBeTruthy();
  });

  test("affiche les filtres", () => {
    renderWithBrand();
    expect(screen.getByText("Tous")).toBeTruthy();
    expect(screen.getByText("À valider")).toBeTruthy();
    expect(screen.getByText("Approuvés")).toBeTruthy();
    expect(screen.getByText("Publiés")).toBeTruthy();
    expect(screen.getByText("Rejetés")).toBeTruthy();
  });
});

describe("ProposalsListScreen — Chargement", () => {
  test("appelle proposalsApi.list avec brandId", async () => {
    renderWithBrand();
    await waitFor(() => {
      expect(proposalsApi.list).toHaveBeenCalledWith("brand-1", undefined);
    });
  });

  test("affiche empty state si pas de proposals", async () => {
    (proposalsApi.list as jest.Mock).mockResolvedValue({ data: { proposals: [] } });
    renderWithBrand();
    await waitFor(() => {
      expect(screen.getByText("Votre premier post IA vous attend")).toBeTruthy();
    });
  });
});

describe("ProposalsListScreen — Filtres", () => {
  test("filtre par status appelle API avec params", async () => {
    (proposalsApi.list as jest.Mock).mockResolvedValue({ data: { proposals: [] } });
    renderWithBrand();
    await waitFor(() => {
      expect(proposalsApi.list).toHaveBeenCalled();
    });
    // "À valider" may appear as filter chip + in proposal card status — use getAllByText
    const filterChips = screen.getAllByText("À valider");
    fireEvent.press(filterChips[0]);
    await waitFor(() => {
      expect(proposalsApi.list).toHaveBeenCalledWith("brand-1", { status: "pending" });
    });
  });

  test("filtre Tous appelle sans params", async () => {
    (proposalsApi.list as jest.Mock).mockResolvedValue({ data: { proposals: [] } });
    renderWithBrand();
    await waitFor(() => {
      expect(proposalsApi.list).toHaveBeenCalled();
    });
    const filterChips = screen.getAllByText("À valider");
    fireEvent.press(filterChips[0]);
    await waitFor(() => {
      expect(proposalsApi.list).toHaveBeenCalledWith("brand-1", { status: "pending" });
    });
    fireEvent.press(screen.getByText("Tous"));
    await waitFor(() => {
      expect(proposalsApi.list).toHaveBeenLastCalledWith("brand-1", undefined);
    });
  });
});

describe("ProposalsListScreen — Sans brand", () => {
  test("ne charge pas sans brandId", () => {
    render(
      <BrandContext.Provider value={{ activeBrand: null, brands: [] } as any}>
        <ProposalsListScreen />
      </BrandContext.Provider>
    );
    expect(proposalsApi.list).not.toHaveBeenCalled();
  });
});
