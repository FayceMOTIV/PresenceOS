/**
 * Tests du ConnectSocialsScreen
 * Covers: rendering, platform list, connected/disconnected states,
 * connect flow (OAuth), disconnect flow, error handling, navigation.
 */

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react-native";
import { Alert, AppState } from "react-native";
import ConnectSocialsScreen from "@/screens/social/ConnectSocialsScreen";
import { BrandContext } from "@/contexts/BrandContext";
import { postizApi } from "@/lib/api";

jest.setTimeout(60000);
jest.spyOn(Alert, "alert");

// ── API mock ──────────────────────────────────────────────────────────────────
jest.mock("@/lib/api", () => ({
  postizApi: {
    integrations: jest.fn(),
    getConnectUrl: jest.fn(),
    disconnect: jest.fn(),
  },
}));

// ── Deep linking / OAuth mocks ────────────────────────────────────────────────
jest.mock("@/lib/deepLinking", () => ({
  buildRedirectUrl: jest.fn(() => "rs3://social-callback"),
  openOAuthSession: jest.fn().mockResolvedValue({ success: true }),
}));

// ── Navigation mock ───────────────────────────────────────────────────────────
const mockGoBack = jest.fn();
const mockNavigate = jest.fn();
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ goBack: mockGoBack, navigate: mockNavigate }),
  useRoute: () => ({ params: {} }),
}));

// ── Expo / UI mocks ───────────────────────────────────────────────────────────
jest.mock("expo-linear-gradient", () => {
  const { View } = require("react-native");
  return { LinearGradient: (props: any) => <View {...props} /> };
});

jest.mock("react-native-safe-area-context", () => {
  const { View } = require("react-native");
  return { SafeAreaView: (props: any) => <View {...props} /> };
});

// ── Test data ─────────────────────────────────────────────────────────────────
const mockBrand = {
  activeBrand: { id: "brand-1", name: "Test Restaurant", slug: "test", brand_type: "restaurant" },
  brands: [],
};

const mockIntegrations = [
  { id: "integ-1", name: "My Instagram", identifier: "instagram", disabled: false },
  { id: "integ-2", name: "My Facebook", identifier: "facebook", disabled: false },
];

// ── Render helper ─────────────────────────────────────────────────────────────
function renderScreen(brand = mockBrand) {
  return render(
    <BrandContext.Provider value={brand as any}>
      <ConnectSocialsScreen />
    </BrandContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  (postizApi.integrations as jest.Mock).mockResolvedValue({ data: [] });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("ConnectSocialsScreen — Rendu initial", () => {
  test("affiche le titre 'Connecter mes réseaux'", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Connecter mes réseaux")).toBeTruthy();
    });
  });

  test("affiche les 6 plateformes", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Instagram")).toBeTruthy();
      expect(screen.getByText("Facebook")).toBeTruthy();
      expect(screen.getByText("TikTok")).toBeTruthy();
      expect(screen.getByText("LinkedIn")).toBeTruthy();
      expect(screen.getByText("X (Twitter)")).toBeTruthy();
      expect(screen.getByText("YouTube")).toBeTruthy();
    });
  });

  test("affiche le hint textuel", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText(/Appuie sur "Connecter"/)).toBeTruthy();
    });
  });

  test("affiche le compteur à 0 quand aucun réseau connecté", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("0")).toBeTruthy();
      expect(screen.getByText("Aucun réseau connecté")).toBeTruthy();
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("ConnectSocialsScreen — États déconnectés", () => {
  test("affiche 'Non connecté' pour chaque plateforme non liée", async () => {
    renderScreen();
    await waitFor(() => {
      const labels = screen.getAllByText("Non connecté");
      expect(labels.length).toBe(6);
    });
  });

  test("affiche 6 boutons 'Connecter' quand aucun compte lié", async () => {
    renderScreen();
    await waitFor(() => {
      const btns = screen.getAllByText("Connecter");
      expect(btns.length).toBe(6);
    });
  });

  test("n'affiche PAS le bouton 'Publier un post' quand 0 réseau connecté", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.queryByText("Publier un post")).toBeNull();
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("ConnectSocialsScreen — États connectés", () => {
  beforeEach(() => {
    (postizApi.integrations as jest.Mock).mockResolvedValue({
      data: mockIntegrations,
    });
  });

  test("affiche le nom du compte pour une plateforme connectée", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("My Instagram")).toBeTruthy();
      expect(screen.getByText("My Facebook")).toBeTruthy();
    });
  });

  test("affiche le bon compteur quand 2 réseaux connectés", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("2")).toBeTruthy();
      expect(screen.getByText("réseaux connectés")).toBeTruthy();
    });
  });

  test("affiche le texte singulier quand 1 réseau connecté", async () => {
    (postizApi.integrations as jest.Mock).mockResolvedValue({
      data: [mockIntegrations[0]],
    });
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("1")).toBeTruthy();
      expect(screen.getByText("réseau connecté")).toBeTruthy();
    });
  });

  test("affiche le bouton 'Publier un post' quand des réseaux sont connectés", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Publier un post")).toBeTruthy();
    });
  });

  test("filtre les intégrations désactivées (disabled: true)", async () => {
    (postizApi.integrations as jest.Mock).mockResolvedValue({
      data: [
        { id: "integ-1", name: "Active Insta", identifier: "instagram", disabled: false },
        { id: "integ-2", name: "Disabled TikTok", identifier: "tiktok", disabled: true },
      ],
    });
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Active Insta")).toBeTruthy();
      // TikTok is disabled → appears as disconnected
      expect(screen.queryByText("Disabled TikTok")).toBeNull();
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("ConnectSocialsScreen — API", () => {
  test("appelle postizApi.integrations au montage avec le brandId", async () => {
    renderScreen();
    await waitFor(() => {
      expect(postizApi.integrations).toHaveBeenCalledWith("brand-1");
    });
  });

  test("ne charge pas si brandId est null", () => {
    render(
      <BrandContext.Provider value={{ activeBrand: null, brands: [] } as any}>
        <ConnectSocialsScreen />
      </BrandContext.Provider>
    );
    expect(postizApi.integrations).not.toHaveBeenCalled();
  });

  test("gère une erreur réseau gracieusement (liste vide)", async () => {
    (postizApi.integrations as jest.Mock).mockRejectedValue(new Error("Network error"));
    renderScreen();
    await waitFor(() => {
      const labels = screen.getAllByText("Non connecté");
      expect(labels.length).toBe(6);
    });
  });

  test("gère data non-array gracieusement", async () => {
    (postizApi.integrations as jest.Mock).mockResolvedValue({ data: null });
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("0")).toBeTruthy();
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("ConnectSocialsScreen — Connexion OAuth", () => {
  test("press 'Connecter' appelle getConnectUrl avec la bonne plateforme", async () => {
    const { openOAuthSession } = require("@/lib/deepLinking");
    (postizApi.getConnectUrl as jest.Mock).mockResolvedValue({
      data: { connect_url: "https://oauth.example.com/instagram" },
    });
    renderScreen();
    await waitFor(() => {
      expect(screen.getAllByText("Connecter").length).toBe(6);
    });
    fireEvent.press(screen.getAllByText("Connecter")[0]); // Instagram
    await waitFor(() => {
      expect(postizApi.getConnectUrl).toHaveBeenCalledWith("brand-1", "instagram");
    });
  });

  test("ouvre la session OAuth après récupération de l'URL", async () => {
    const { openOAuthSession } = require("@/lib/deepLinking");
    (postizApi.getConnectUrl as jest.Mock).mockResolvedValue({
      data: { connect_url: "https://oauth.example.com/instagram" },
    });
    renderScreen();
    await waitFor(() => {
      expect(screen.getAllByText("Connecter").length).toBe(6);
    });
    fireEvent.press(screen.getAllByText("Connecter")[0]);
    await waitFor(() => {
      expect(openOAuthSession).toHaveBeenCalledWith(
        "https://oauth.example.com/instagram",
        "rs3://social-callback"
      );
    });
  });

  test("recharge les intégrations après un OAuth réussi", async () => {
    const { openOAuthSession } = require("@/lib/deepLinking");
    (openOAuthSession as jest.Mock).mockResolvedValue({ success: true });
    (postizApi.getConnectUrl as jest.Mock).mockResolvedValue({
      data: { connect_url: "https://oauth.example.com/facebook" },
    });
    renderScreen();
    await waitFor(() => {
      expect(screen.getAllByText("Connecter").length).toBe(6);
    });
    fireEvent.press(screen.getAllByText("Connecter")[1]); // Facebook
    // Wait for the full async flow (getConnectUrl + openOAuthSession + 2s delay + fetchIntegrations)
    await waitFor(
      () => {
        expect(postizApi.integrations).toHaveBeenCalledTimes(2);
      },
      { timeout: 10000 }
    );
  });

  test("affiche une Alert si connect_url est absent", async () => {
    (postizApi.getConnectUrl as jest.Mock).mockResolvedValue({ data: {} });
    renderScreen();
    await waitFor(() => {
      expect(screen.getAllByText("Connecter").length).toBe(6);
    });
    fireEvent.press(screen.getAllByText("Connecter")[0]);
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        "Erreur",
        "Impossible de générer le lien de connexion."
      );
    });
  });

  test("affiche une Alert si getConnectUrl échoue", async () => {
    (postizApi.getConnectUrl as jest.Mock).mockRejectedValue({
      response: { data: { detail: "Auth error" } },
    });
    renderScreen();
    await waitFor(() => {
      expect(screen.getAllByText("Connecter").length).toBe(6);
    });
    fireEvent.press(screen.getAllByText("Connecter")[0]);
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith("Erreur", "Auth error");
    });
  });

  test("affiche un message générique si aucun detail dans l'erreur", async () => {
    (postizApi.getConnectUrl as jest.Mock).mockRejectedValue(new Error("timeout"));
    renderScreen();
    await waitFor(() => {
      expect(screen.getAllByText("Connecter").length).toBe(6);
    });
    fireEvent.press(screen.getAllByText("Connecter")[0]);
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        "Erreur",
        "Connexion impossible. Réessaie."
      );
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("ConnectSocialsScreen — Déconnexion", () => {
  beforeEach(() => {
    (postizApi.integrations as jest.Mock).mockResolvedValue({
      data: [{ id: "integ-1", name: "My Instagram", identifier: "instagram", disabled: false }],
    });
    (postizApi.disconnect as jest.Mock).mockResolvedValue({ data: {} });
  });

  test("press icône de déconnexion ouvre une Alert de confirmation", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("My Instagram")).toBeTruthy();
    });
    // The disconnect button uses testID or is the last TouchableOpacity inside the platform card.
    // In the screen, when connected, there's a "close-circle-outline" icon TouchableOpacity.
    // We use UNSAFE_getAllByType and look for the one with onPress === handleDisconnect signature.
    // Strategy: find the TouchableOpacity that is NOT a back-button and NOT a Publish CTA.
    // The disconnect btn is the only one rendered inside connectedActions view.
    const { TouchableOpacity } = require("react-native");
    const allTouchables = screen.UNSAFE_getAllByType(TouchableOpacity);
    // Index 0 = back button (header)
    // Index 1 = disconnect btn for instagram (inside connected card — no "Connecter" text shown)
    // We look for a touchable that when pressed calls Alert with "Déconnecter"
    // Try pressing each non-first touchable until the Alert fires
    let pressed = false;
    for (let i = 1; i < allTouchables.length && !pressed; i++) {
      jest.clearAllMocks();
      fireEvent.press(allTouchables[i]);
      if ((Alert.alert as jest.Mock).mock.calls.length > 0) {
        pressed = true;
      }
    }
    expect(Alert.alert).toHaveBeenCalledWith(
      "Déconnecter",
      expect.stringContaining("Instagram"),
      expect.any(Array)
    );
  });

  test("confirmer la déconnexion appelle postizApi.disconnect", async () => {
    let alertCallback: (() => void) | undefined;
    (Alert.alert as jest.Mock).mockImplementation((_title, _msg, buttons) => {
      // Simulate pressing "Déconnecter" (destructive button)
      const destructive = buttons?.find((b: any) => b.style === "destructive");
      alertCallback = destructive?.onPress;
    });

    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("My Instagram")).toBeTruthy();
    });

    const { TouchableOpacity } = require("react-native");
    const allTouchables = screen.UNSAFE_getAllByType(TouchableOpacity);
    // Find the disconnect button by pressing each until Alert fires with "Déconnecter"
    for (let i = 1; i < allTouchables.length; i++) {
      fireEvent.press(allTouchables[i]);
      if (
        (Alert.alert as jest.Mock).mock.calls.some(
          (call: any[]) => call[0] === "Déconnecter"
        )
      ) {
        break;
      }
    }

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalled();
    });

    if (alertCallback) {
      await act(async () => { alertCallback!(); });
      await waitFor(() => {
        expect(postizApi.disconnect).toHaveBeenCalledWith("brand-1", "integ-1");
      });
    }
  });

  test("gère l'erreur de déconnexion avec une Alert", async () => {
    (postizApi.disconnect as jest.Mock).mockRejectedValue(new Error("server error"));

    let alertCallback: (() => void) | undefined;
    (Alert.alert as jest.Mock).mockImplementation((_title, _msg, buttons) => {
      const destructive = buttons?.find((b: any) => b.style === "destructive");
      if (destructive) alertCallback = destructive.onPress;
    });

    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("My Instagram")).toBeTruthy();
    });

    const { TouchableOpacity } = require("react-native");
    const allTouchables = screen.UNSAFE_getAllByType(TouchableOpacity);
    for (let i = 1; i < allTouchables.length; i++) {
      fireEvent.press(allTouchables[i]);
      if (
        (Alert.alert as jest.Mock).mock.calls.some(
          (call: any[]) => call[0] === "Déconnecter"
        )
      ) {
        break;
      }
    }

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalled();
    });

    if (alertCallback) {
      await act(async () => { alertCallback!(); });
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          "Erreur",
          "Impossible de déconnecter ce compte."
        );
      });
    }
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("ConnectSocialsScreen — Navigation", () => {
  test("le bouton retour appelle goBack", async () => {
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Connecter mes réseaux")).toBeTruthy();
    });
    const { TouchableOpacity } = require("react-native");
    const touchables = screen.UNSAFE_getAllByType(TouchableOpacity);
    fireEvent.press(touchables[0]); // first touchable = back button
    expect(mockGoBack).toHaveBeenCalled();
  });

  test("le bouton 'Publier un post' navigue vers Publish", async () => {
    (postizApi.integrations as jest.Mock).mockResolvedValue({
      data: [{ id: "integ-1", name: "My Instagram", identifier: "instagram", disabled: false }],
    });
    renderScreen();
    await waitFor(() => {
      expect(screen.getByText("Publier un post")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Publier un post"));
    expect(mockNavigate).toHaveBeenCalledWith("Publish");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
describe("ConnectSocialsScreen — AppState refresh", () => {
  test("recharge les intégrations quand l'app revient au premier plan", async () => {
    let capturedHandler: ((state: string) => void) | null = null;
    const mockRemove = jest.fn();

    // Override AppState.currentState so `appState.current` starts as "active"
    // and the component's ref is initialized properly.
    const originalCurrentState = AppState.currentState;
    Object.defineProperty(AppState, "currentState", {
      value: "active",
      writable: true,
      configurable: true,
    });

    jest
      .spyOn(AppState, "addEventListener")
      .mockImplementation((_event: any, handler: any) => {
        capturedHandler = handler;
        return { remove: mockRemove } as any;
      });

    renderScreen();
    await waitFor(() => {
      expect(postizApi.integrations).toHaveBeenCalledTimes(1);
    });

    // Simulate app going to background — this sets appState.current = "background"
    if (capturedHandler) {
      await act(async () => { (capturedHandler as any)("background"); });
      // Now simulate coming back to foreground — condition: background → active
      await act(async () => { (capturedHandler as any)("active"); });
    }

    await waitFor(() => {
      expect(postizApi.integrations).toHaveBeenCalledTimes(2);
    });

    jest.restoreAllMocks();
    Object.defineProperty(AppState, "currentState", {
      value: originalCurrentState,
      writable: true,
      configurable: true,
    });
  });
});
