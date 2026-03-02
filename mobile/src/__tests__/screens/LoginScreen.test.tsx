/**
 * Tests du LoginScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import { Alert } from "react-native";
import LoginScreen from "@/screens/auth/LoginScreen";
import { AuthContext } from "@/contexts/BrandContext";

jest.spyOn(Alert, "alert");

const mockLogin = jest.fn();
const mockAuthContext = {
  login: mockLogin,
  register: jest.fn(),
  logout: jest.fn(),
  resetPassword: jest.fn(),
};

function renderWithAuth(props = {}) {
  return render(
    <AuthContext.Provider value={mockAuthContext}>
      <LoginScreen {...props} />
    </AuthContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe("LoginScreen — Rendu", () => {
  test("affiche le logo RS3", () => {
    renderWithAuth();
    expect(screen.getByText("RS3")).toBeTruthy();
  });

  test("affiche le sous-titre français", () => {
    renderWithAuth();
    expect(screen.getByText("Connectez-vous à votre compte")).toBeTruthy();
  });

  test("affiche les champs email et mot de passe", () => {
    renderWithAuth();
    expect(screen.getByPlaceholderText("Email")).toBeTruthy();
    expect(screen.getByPlaceholderText("Mot de passe")).toBeTruthy();
  });

  test("affiche le bouton de connexion", () => {
    renderWithAuth();
    expect(screen.getByText("Se connecter")).toBeTruthy();
  });
});

describe("LoginScreen — Validation", () => {
  test("affiche une alerte si email vide", () => {
    renderWithAuth();
    fireEvent.press(screen.getByText("Se connecter"));
    expect(Alert.alert).toHaveBeenCalledWith(
      "Erreur",
      "Veuillez entrer votre email et mot de passe"
    );
  });

  test("affiche une alerte si mot de passe vide", () => {
    renderWithAuth();
    fireEvent.changeText(screen.getByPlaceholderText("Email"), "test@test.com");
    fireEvent.press(screen.getByText("Se connecter"));
    expect(Alert.alert).toHaveBeenCalledWith(
      "Erreur",
      "Veuillez entrer votre email et mot de passe"
    );
  });
});

describe("LoginScreen — Connexion", () => {
  test("appelle login avec email et password", async () => {
    mockLogin.mockResolvedValue(undefined);
    renderWithAuth();

    fireEvent.changeText(screen.getByPlaceholderText("Email"), "test@test.com");
    fireEvent.changeText(
      screen.getByPlaceholderText("Mot de passe"),
      "password123"
    );
    fireEvent.press(screen.getByText("Se connecter"));

    await waitFor(
      () => {
        expect(mockLogin).toHaveBeenCalledWith("test@test.com", "password123");
      },
      { timeout: 10000 }
    );
  }, 15000);

  test("affiche l'erreur auth/wrong-password", async () => {
    const error: any = new Error("wrong");
    error.code = "auth/wrong-password";
    mockLogin.mockRejectedValue(error);

    renderWithAuth();

    fireEvent.changeText(screen.getByPlaceholderText("Email"), "test@test.com");
    fireEvent.changeText(
      screen.getByPlaceholderText("Mot de passe"),
      "wrong"
    );
    fireEvent.press(screen.getByText("Se connecter"));

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        "Connexion échouée",
        "Email ou mot de passe incorrect"
      );
    });
  });

  test("affiche l'erreur auth/too-many-requests", async () => {
    const error: any = new Error("rate-limited");
    error.code = "auth/too-many-requests";
    mockLogin.mockRejectedValue(error);

    renderWithAuth();

    fireEvent.changeText(screen.getByPlaceholderText("Email"), "a@b.com");
    fireEvent.changeText(screen.getByPlaceholderText("Mot de passe"), "x");
    fireEvent.press(screen.getByText("Se connecter"));

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        "Connexion échouée",
        "Trop de tentatives, réessayez plus tard"
      );
    });
  });
});

describe("LoginScreen — Navigation", () => {
  test("affiche les liens Register/ForgotPassword si navigation fournie", () => {
    const mockNav = { navigate: jest.fn() };
    renderWithAuth({ navigation: mockNav });

    expect(screen.getByText("Mot de passe oublié ?")).toBeTruthy();
    expect(screen.getByText(/Créer un compte/)).toBeTruthy();
  });

  test("navigue vers ForgotPassword", () => {
    const mockNav = { navigate: jest.fn() };
    renderWithAuth({ navigation: mockNav });

    fireEvent.press(screen.getByText("Mot de passe oublié ?"));
    expect(mockNav.navigate).toHaveBeenCalledWith("ForgotPassword");
  });

  test("navigue vers Register", () => {
    const mockNav = { navigate: jest.fn() };
    renderWithAuth({ navigation: mockNav });

    fireEvent.press(screen.getByText(/Créer un compte/));
    expect(mockNav.navigate).toHaveBeenCalledWith("Register");
  });
});

describe("LoginScreen — Sans AuthContext", () => {
  test("affiche 'Chargement...' sans AuthContext", () => {
    render(
      <AuthContext.Provider value={null}>
        <LoginScreen />
      </AuthContext.Provider>
    );
    expect(screen.getByText("Chargement...")).toBeTruthy();
  });
});
