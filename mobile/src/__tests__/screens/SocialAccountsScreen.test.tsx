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
    connectUrl: jest.fn(),
    disconnect: jest.fn(),
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
  test("affiche le header 'Connecter mes reseaux'", async () => {
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("Connecter mes reseaux")).toBeTruthy();
    });
  });

  test("affiche les 6 plateformes", async () => {
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("Instagram")).toBeTruthy();
      expect(screen.getByText("Facebook")).toBeTruthy();
      expect(screen.getByText("TikTok")).toBeTruthy();
      expect(screen.getByText("LinkedIn")).toBeTruthy();
      expect(screen.getByText("X (Twitter)")).toBeTruthy();
      expect(screen.getByText("YouTube")).toBeTruthy();
    });
  });

  test("affiche le hint de connexion", async () => {
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText(/Appuie sur "Connecter"/)).toBeTruthy();
    });
  });
});

describe("SocialAccountsScreen — States", () => {
  test("affiche 'Non connecte' pour chaque plateforme deconnectee", async () => {
    renderSocial();
    await waitFor(() => {
      const disconnected = screen.getAllByText("Non connecte");
      expect(disconnected.length).toBe(6);
    });
  });

  test("affiche le username pour une plateforme connectee", async () => {
    (socialApi.accounts as jest.Mock).mockResolvedValue({
      data: {
        accounts: [{ platform: "instagram", username: "testinsta", connected: true }],
      },
    });
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("@testinsta")).toBeTruthy();
    });
  });

  test("affiche 'Connecter' boutons pour plateformes deconnectees", async () => {
    renderSocial();
    await waitFor(() => {
      const btns = screen.getAllByText("Connecter");
      expect(btns.length).toBe(6);
    });
  });

  test("affiche le footer info quand aucun reseau connecte", async () => {
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText(/Aucun reseau connecte/)).toBeTruthy();
    });
  });
});

describe("SocialAccountsScreen — Navigation", () => {
  test("back button appelle goBack", async () => {
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("Connecter mes reseaux")).toBeTruthy();
    });
    // The back button is the first TouchableOpacity in the header row
    const { TouchableOpacity } = require("react-native");
    const touchables = screen.UNSAFE_getAllByType(TouchableOpacity);
    fireEvent.press(touchables[0]); // first touchable = back button
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

  test("gere erreur API gracieusement", async () => {
    (socialApi.accounts as jest.Mock).mockRejectedValue(new Error("Network error"));
    renderSocial();
    await waitFor(() => {
      // Falls back to all disconnected
      const disconnected = screen.getAllByText("Non connecte");
      expect(disconnected.length).toBe(6);
    });
  });
});

describe("SocialAccountsScreen — Connexion individuelle", () => {
  test("press Connecter lance OAuth via connectUrl", async () => {
    const WebBrowser = require("expo-web-browser");
    (socialApi.connectUrl as jest.Mock).mockResolvedValue({
      data: { url: "https://auth.example.com/oauth" },
    });
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("Instagram")).toBeTruthy();
    });
    const connectBtns = screen.getAllByText("Connecter");
    fireEvent.press(connectBtns[0]); // Instagram
    await waitFor(() => {
      expect(socialApi.connectUrl).toHaveBeenCalledWith("brand-1", "instagram", expect.any(String));
      expect(WebBrowser.openAuthSessionAsync).toHaveBeenCalled();
    });
  });

  test("erreur connectUrl sans url affiche pas de crash", async () => {
    (socialApi.connectUrl as jest.Mock).mockResolvedValue({ data: {} });
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("Instagram")).toBeTruthy();
    });
    const connectBtns = screen.getAllByText("Connecter");
    fireEvent.press(connectBtns[0]);
    await waitFor(() => {
      expect(socialApi.connectUrl).toHaveBeenCalled();
    });
  });
});

describe("SocialAccountsScreen — Connect via Late", () => {
  test("connecte Facebook via Late OAuth", async () => {
    const WebBrowser = require("expo-web-browser");
    (WebBrowser.openAuthSessionAsync as jest.Mock).mockResolvedValue({ type: "success" });
    (socialApi.connectUrl as jest.Mock).mockResolvedValue({
      data: { url: "https://facebook.com/oauth/authorize" },
    });
    renderSocial();
    await waitFor(() => {
      expect(screen.getByText("Facebook")).toBeTruthy();
    });
    const connectBtns = screen.getAllByText("Connecter");
    fireEvent.press(connectBtns[1]); // Facebook
    await waitFor(() => {
      expect(socialApi.connectUrl).toHaveBeenCalledWith("brand-1", "facebook", expect.any(String));
    }, { timeout: 5000 });
  });
});
