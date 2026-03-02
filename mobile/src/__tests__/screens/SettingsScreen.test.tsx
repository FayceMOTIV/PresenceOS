/**
 * Tests du SettingsScreen
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react-native";
import { Alert } from "react-native";
import SettingsScreen from "@/screens/settings/SettingsScreen";
import { AuthContext, BrandContext } from "@/contexts/BrandContext";

jest.spyOn(Alert, "alert");

const mockGoBack = jest.fn();
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({ goBack: mockGoBack, navigate: jest.fn() }),
  useRoute: () => ({ params: {} }),
}));

const mockLogout = jest.fn();
const mockAuth = { login: jest.fn(), register: jest.fn(), logout: mockLogout, resetPassword: jest.fn() };
const mockBrand = {
  activeBrand: { id: "brand-1", name: "Le Family's", slug: "familys", brand_type: "restaurant" },
  brands: [],
};

function renderSettings(auth = mockAuth, brand = mockBrand) {
  return render(
    <AuthContext.Provider value={auth}>
      <BrandContext.Provider value={brand as any}>
        <SettingsScreen />
      </BrandContext.Provider>
    </AuthContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe("SettingsScreen — Rendu", () => {
  test("affiche le titre Paramètres", () => {
    renderSettings();
    expect(screen.getByText("Paramètres")).toBeTruthy();
  });

  test("affiche la section Compte", () => {
    renderSettings();
    expect(screen.getByText("Compte")).toBeTruthy();
  });

  test("affiche la marque active", () => {
    renderSettings();
    expect(screen.getByText("Marque active")).toBeTruthy();
    expect(screen.getByText("Le Family's")).toBeTruthy();
  });

  test("affiche Sécurité JWT", () => {
    renderSettings();
    expect(screen.getByText("Sécurité")).toBeTruthy();
    expect(screen.getByText("JWT")).toBeTruthy();
  });

  test("affiche la section Application", () => {
    renderSettings();
    expect(screen.getByText("Application")).toBeTruthy();
  });

  test("affiche la version", () => {
    renderSettings();
    expect(screen.getByText("Version")).toBeTruthy();
    // "v2.0.0" appears in both the row and the footer — use getAllByText
    expect(screen.getAllByText(/v2\.0\.0/).length).toBeGreaterThanOrEqual(1);
  });

  test("affiche Notifications activées", () => {
    renderSettings();
    expect(screen.getByText("Notifications")).toBeTruthy();
    expect(screen.getByText("Activées")).toBeTruthy();
  });

  test("affiche le footer avec version", () => {
    renderSettings();
    expect(screen.getByText(/PresenceOS v2\.0\.0/)).toBeTruthy();
  });
});

describe("SettingsScreen — Navigation", () => {
  test("back button appelle goBack", () => {
    renderSettings();
    fireEvent.press(screen.getByText("arrow-back"));
    expect(mockGoBack).toHaveBeenCalled();
  });
});

describe("SettingsScreen — Logout", () => {
  test("affiche la confirmation de déconnexion", () => {
    renderSettings();
    fireEvent.press(screen.getByText("Se déconnecter"));
    expect(Alert.alert).toHaveBeenCalledWith(
      "Déconnexion",
      "Voulez-vous vous déconnecter ?",
      expect.arrayContaining([
        expect.objectContaining({ text: "Annuler" }),
        expect.objectContaining({ text: "Se déconnecter", style: "destructive" }),
      ])
    );
  });

  test("confirmer la déconnexion appelle auth.logout", () => {
    renderSettings();
    fireEvent.press(screen.getByText("Se déconnecter"));
    const alertCall = (Alert.alert as jest.Mock).mock.calls[0];
    const buttons = alertCall[2];
    const destructiveBtn = buttons.find((b: any) => b.style === "destructive");
    destructiveBtn.onPress();
    expect(mockLogout).toHaveBeenCalled();
  });

  test("marque sans brand affiche —", () => {
    renderSettings(mockAuth, { activeBrand: null, brands: [] } as any);
    expect(screen.getByText("—")).toBeTruthy();
  });
});
