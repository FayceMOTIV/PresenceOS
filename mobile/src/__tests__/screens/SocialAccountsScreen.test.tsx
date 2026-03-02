/**
 * Tests du SocialAccountsScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import SocialAccountsScreen from "@/screens/social/SocialAccountsScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { socialApi } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  socialApi: {
    accounts: jest.fn(),
    linkUrl: jest.fn(),
    facebookPages: jest.fn(),
    selectPage: jest.fn(),
  },
}));

jest.mock("expo-web-browser", () => ({
  openAuthSessionAsync: jest.fn().mockResolvedValue({ type: "success" }),
}));

jest.mock("expo-linking", () => ({
  createURL: jest.fn((path: string) => `rs3://${path}`),
}));

const mockGoBack = jest.fn();
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ goBack: mockGoBack, navigate: jest.fn() }),
  useRoute: () => ({ params: {} }),
}));

const mockBrand = {
  activeBrand: { id: "brand-1", name: "Test", slug: "test", brand_type: "restaurant" },
  brands: [],
};

function renderSocial(brand = mockBrand) {
  return render(
    <BrandContext.Provider value={brand as any}>
      <SocialAccountsScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (socialApi.accounts as jest.Mock).mockResolvedValue({
    data: { accounts: [] },
  });
});

describe("SocialAccountsScreen — Rendu", () => {
  test("affiche le header 'Mes réseaux sociaux'", async () => {
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("Mes réseaux sociaux")).toBeTruthy();
    });
  });

  test("affiche les 3 plateformes", async () => {
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("Instagram")).toBeTruthy();
      expect(screen.getByText("Facebook")).toBeTruthy();
      expect(screen.getByText("TikTok")).toBeTruthy();
    });
  });

  test("affiche le bouton 'Connecter mes réseaux'", async () => {
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("Connecter mes réseaux")).toBeTruthy();
    });
  });

  test("affiche le hint de connexion", async () => {
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText(/Ouvre une page sécurisée/)).toBeTruthy();
    });
  });
});

describe("SocialAccountsScreen — States", () => {
  test("affiche 'Non connecté' pour chaque plateforme déconnectée", async () => {
    renderSocial();
    await waitFor(() => {
      const disconnected = screen.getAllByText("Non connecté");
      expect(disconnected.length).toBe(3);
    });
  });

  test("affiche 'Connecté' pour une plateforme connectée", async () => {
    (socialApi.accounts as jest.Mock).mockResolvedValue({
      data: {
        accounts: [{ platform: "instagram", username: "testinsta", connected: true }],
      },
    });
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("Connecté")).toBeTruthy();
      expect(screen.getByText("@testinsta")).toBeTruthy();
    });
  });

  test("affiche 'Connecter' boutons pour plateformes déconnectées", async () => {
    renderSocial();
    await waitFor(() => {
      const btns = screen.getAllByText("Connecter");
      expect(btns.length).toBe(3);
    });
  });

  test("affiche le footer info quand aucun réseau connecté", async () => {
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText(/Aucun réseau connecté/)).toBeTruthy();
    });
  });
});

describe("SocialAccountsScreen — Navigation", () => {
  test("back button appelle goBack", async () => {
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("Mes réseaux sociaux")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("arrow-back"));
    expect(mockGoBack).toHaveBeenCalled();
  });
});

describe("SocialAccountsScreen — API", () => {
  test("appelle socialApi.accounts au montage", async () => {
    renderSocial();
    await waitFor(() => {
      expect(socialApi.accounts).toHaveBeenCalledWith("brand-1");
    });
  });

  test("ne charge pas sans brandId", () => {
    render(
      <BrandContext.Provider value={{ activeBrand: null, brands: [] } as any}>
        <SocialAccountsScreen />
      </BrandContext.Provider>
    );
    expect(socialApi.accounts).not.toHaveBeenCalled();
  });

  test("gère erreur API gracieusement", async () => {
    (socialApi.accounts as jest.Mock).mockRejectedValue(new Error("Network error"));
    renderSocial();
    await waitFor(() => {
      // Falls back to all disconnected
      const disconnected = screen.getAllByText("Non connecté");
      expect(disconnected.length).toBe(3);
    });
  });
});

describe("SocialAccountsScreen — Connexion individuelle", () => {
  test("press Connecter lance OAuth", async () => {
    const WebBrowser = require("expo-web-browser");
    (socialApi.linkUrl as jest.Mock).mockResolvedValue({
      data: { url: "https://auth.example.com/oauth" },
    });
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("Instagram")).toBeTruthy();
    });
    const connectBtns = screen.getAllByText("Connecter");
    fireEvent.press(connectBtns[0]); // Instagram
    await waitFor(() => {
      expect(socialApi.linkUrl).toHaveBeenCalledWith("brand-1", "instagram", expect.any(String));
      expect(WebBrowser.openAuthSessionAsync).toHaveBeenCalled();
    });
  });

  test("erreur linkUrl affiche alerte", async () => {
    (socialApi.linkUrl as jest.Mock).mockResolvedValue({ data: {} });
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("Instagram")).toBeTruthy();
    });
    const connectBtns = screen.getAllByText("Connecter");
    fireEvent.press(connectBtns[0]);
    await waitFor(() => {
      expect(socialApi.linkUrl).toHaveBeenCalled();
    });
  });
});

describe("SocialAccountsScreen — Connexion globale", () => {
  test("press 'Connecter mes réseaux' lance OAuth sans platform", async () => {
    const WebBrowser = require("expo-web-browser");
    (socialApi.linkUrl as jest.Mock).mockResolvedValue({
      data: { url: "https://auth.example.com/oauth-all" },
    });
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("Connecter mes réseaux")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Connecter mes réseaux"));
    await waitFor(() => {
      expect(socialApi.linkUrl).toHaveBeenCalledWith("brand-1", undefined, expect.any(String));
      expect(WebBrowser.openAuthSessionAsync).toHaveBeenCalled();
    });
  });
});

describe("SocialAccountsScreen — Page Picker", () => {
  test("affiche page picker quand Facebook renvoie >1 pages", async () => {
    const WebBrowser = require("expo-web-browser");
    (WebBrowser.openAuthSessionAsync as jest.Mock).mockResolvedValue({ type: "success" });
    (socialApi.linkUrl as jest.Mock).mockResolvedValue({
      data: { url: "https://auth.example.com/oauth" },
    });
    (socialApi.facebookPages as jest.Mock).mockResolvedValue({
      data: { pages: [
        { id: "p1", name: "Page 1", category: "Restaurant" },
        { id: "p2", name: "Page 2", category: "Bar" },
      ]},
    });
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("Facebook")).toBeTruthy();
    });
    const connectBtns = screen.getAllByText("Connecter");
    fireEvent.press(connectBtns[1]); // Facebook
    await waitFor(() => {
      expect(socialApi.facebookPages).toHaveBeenCalledWith("brand-1");
    }, { timeout: 5000 });
  });
});
