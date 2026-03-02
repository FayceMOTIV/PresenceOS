/**
 * Tests du HomeScreen
 */

import React from "react";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react-native";
import HomeScreen from "@/screens/home/HomeScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { kbApi, proposalsApi, briefApi, socialApi, videoApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  kbApi: { completeness: jest.fn() },
  proposalsApi: { list: jest.fn() },
  briefApi: { getToday: jest.fn() },
  socialApi: { accounts: jest.fn() },
  videoApi: { credits: jest.fn() },
}));

jest.mock("@/components/BrandSwitcher", () => {
  const { View } = require("react-native");
  return (props: any) => <View testID="brand-switcher" />;
});

const mockNav = {
  navigate: jest.fn(),
  goBack: jest.fn(),
  getParent: jest.fn(() => ({ navigate: jest.fn() })),
};
jest.mock("@react-navigation/native", () => ({
  ...jest.requireActual("@react-navigation/native"),
  useNavigation: () => mockNav,
}));

const mockBrandContext = {
  activeBrand: { id: "brand-1", name: "Le Family's", slug: "familys", brand_type: "restaurant" },
  brands: [{ id: "brand-1", name: "Le Family's", slug: "familys", brand_type: "restaurant" }],
};

function renderWithContext(brandCtx = mockBrandContext) {
  return render(
    <BrandContext.Provider value={brandCtx as any}>
      <HomeScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (kbApi.completeness as jest.Mock).mockResolvedValue({ data: { completeness_score: 72 } });
  (proposalsApi.list as jest.Mock).mockResolvedValue({
    data: {
      proposals: [
        { id: "p1", status: "pending", caption: "Test", platform: "instagram", proposal_type: "post", confidence_score: 0.85, created_at: "2026-01-01", brand_id: "brand-1", source: "brief" },
        { id: "p2", status: "approved", caption: "Test 2", platform: "instagram", proposal_type: "reel", confidence_score: 0.9, created_at: "2026-01-02", brand_id: "brand-1", source: "brief" },
        { id: "p3", status: "published", caption: "Test 3", platform: "instagram", proposal_type: "post", confidence_score: 0.7, created_at: "2026-01-03", brand_id: "brand-1", source: "brief" },
      ],
    },
  });
  (briefApi.getToday as jest.Mock).mockResolvedValue({ data: { status: "pending" } });
  (socialApi.accounts as jest.Mock).mockResolvedValue({ data: { accounts: [{ connected: true }] } });
  (videoApi.credits as jest.Mock).mockResolvedValue({ data: { credits_remaining: 5 } });
});

describe("HomeScreen — Rendu", () => {
  test("affiche le nom du restaurant", async () => {
    renderWithContext();
    await waitFor(() => {
      expect(screen.getByText("Le Family's")).toBeTruthy();
    });
  });

  test("affiche le greeting", async () => {
    renderWithContext();
    expect(screen.getByText(/Bonjour/)).toBeTruthy();
  });

  test("affiche l'initiale dans l'avatar", async () => {
    renderWithContext();
    expect(screen.getByText("L")).toBeTruthy();
  });

  test("affiche les stats pending/approved/published", async () => {
    renderWithContext();
    await waitFor(() => {
      expect(screen.getByText("En attente")).toBeTruthy();
      expect(screen.getByText("Approuvés")).toBeTruthy();
      expect(screen.getByText("Publiés")).toBeTruthy();
    });
  });

  test("affiche la carte vidéo IA", async () => {
    renderWithContext();
    expect(screen.getByText(/Créer une vidéo IA/)).toBeTruthy();
  });
});

describe("HomeScreen — Brief card", () => {
  test("affiche le brief quand pas encore répondu", async () => {
    renderWithContext();
    await waitFor(() => {
      expect(screen.getByText(/Brief du matin/)).toBeTruthy();
    });
  });

  test("masque le brief quand déjà répondu", async () => {
    (briefApi.getToday as jest.Mock).mockResolvedValue({ data: { status: "answered" } });
    const { unmount } = renderWithContext();
    // Wait for loadData to fully resolve (all Promise.allSettled results processed)
    await act(async () => {
      await new Promise((r) => setTimeout(r, 50));
    });
    expect(screen.queryByText(/Brief du matin/)).toBeNull();
    unmount();
  });
});

describe("HomeScreen — Proposals", () => {
  test("affiche les proposals quand il y en a", async () => {
    renderWithContext();
    await waitFor(() => {
      expect(screen.getByText("Mes derniers posts IA")).toBeTruthy();
      expect(screen.getByText("Tout voir")).toBeTruthy();
    });
  });

  test("affiche empty state quand pas de proposals", async () => {
    (proposalsApi.list as jest.Mock).mockResolvedValue({ data: { proposals: [] } });
    renderWithContext();
    await waitFor(() => {
      expect(screen.getByText(/Votre premier post IA vous attend/)).toBeTruthy();
    });
  });
});

describe("HomeScreen — Navigation", () => {
  test("navigue vers Settings", async () => {
    renderWithContext();
    const settingsBtn = screen.getByText("settings-outline");
    fireEvent.press(settingsBtn);
    expect(mockNav.navigate).toHaveBeenCalledWith("Settings");
  });

  test("navigue vers SocialAccounts", async () => {
    renderWithContext();
    fireEvent.press(screen.getByText("🔗"));
    expect(mockNav.navigate).toHaveBeenCalledWith("SocialAccounts");
  });
});

describe("HomeScreen — API", () => {
  test("appelle les 5 APIs au montage", async () => {
    renderWithContext();
    await waitFor(() => {
      expect(kbApi.completeness).toHaveBeenCalledWith("brand-1");
      expect(proposalsApi.list).toHaveBeenCalledWith("brand-1");
      expect(briefApi.getToday).toHaveBeenCalledWith("brand-1");
      expect(socialApi.accounts).toHaveBeenCalledWith("brand-1");
      expect(videoApi.credits).toHaveBeenCalledWith("brand-1");
    });
  });

  test("ne charge pas sans brandId", async () => {
    render(
      <BrandContext.Provider value={{ activeBrand: null, brands: [] } as any}>
        <HomeScreen />
      </BrandContext.Provider>
    );
    expect(kbApi.completeness).not.toHaveBeenCalled();
  });
});
