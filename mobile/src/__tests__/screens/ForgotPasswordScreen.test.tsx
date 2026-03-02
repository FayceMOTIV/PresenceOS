/**
 * Tests du ForgotPasswordScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import { Alert } from "react-native";
import ForgotPasswordScreen from "@/screens/auth/ForgotPasswordScreen";
import { AuthContext } from "@/contexts/BrandContext";

jest.spyOn(Alert, "alert");

const mockResetPassword = jest.fn();
const mockAuth = { login: jest.fn(), register: jest.fn(), logout: jest.fn(), resetPassword: mockResetPassword };
const mockNavigate = jest.fn();
const navigation = { navigate: mockNavigate } as any;

function renderForgot(auth = mockAuth) {
  return render(
    <AuthContext.Provider value={auth}>
      <ForgotPasswordScreen navigation={navigation} />
    </AuthContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  mockResetPassword.mockResolvedValue({});
});

describe("ForgotPasswordScreen — Rendu", () => {
  test("affiche le logo RS3", () => {
    renderForgot();
    expect(screen.getByText("RS3")).toBeTruthy();
  });

  test("affiche 'Mot de passe oublié'", () => {
    renderForgot();
    expect(screen.getByText("Mot de passe oublié")).toBeTruthy();
  });

  test("affiche la description", () => {
    renderForgot();
    expect(screen.getByText(/Entrez votre adresse email/)).toBeTruthy();
  });

  test("affiche le champ email", () => {
    renderForgot();
    expect(screen.getByPlaceholderText("Email")).toBeTruthy();
  });

  test("affiche 'Envoyer le lien'", () => {
    renderForgot();
    expect(screen.getByText("Envoyer le lien")).toBeTruthy();
  });

  test("affiche le lien retour connexion", () => {
    renderForgot();
    expect(screen.getByText("connexion")).toBeTruthy();
  });
});

describe("ForgotPasswordScreen — Validation", () => {
  test("alerte si email vide", () => {
    renderForgot();
    fireEvent.press(screen.getByText("Envoyer le lien"));
    expect(Alert.alert).toHaveBeenCalledWith("Erreur", "Veuillez entrer votre email");
  });
});

describe("ForgotPasswordScreen — Envoi", () => {
  test("appelle resetPassword et affiche succès", async () => {
    renderForgot();
    fireEvent.changeText(screen.getByPlaceholderText("Email"), "jean@test.com");
    fireEvent.press(screen.getByText("Envoyer le lien"));
    await waitFor(() => {
      expect(mockResetPassword).toHaveBeenCalledWith("jean@test.com");
      expect(screen.getByText(/un lien de réinitialisation a été envoyé/)).toBeTruthy();
    });
  });

  test("affiche succès même en cas d'erreur (anti-enum)", async () => {
    mockResetPassword.mockRejectedValue(new Error("fail"));
    renderForgot();
    fireEvent.changeText(screen.getByPlaceholderText("Email"), "wrong@test.com");
    fireEvent.press(screen.getByText("Envoyer le lien"));
    await waitFor(() => {
      expect(screen.getByText(/un lien de réinitialisation a été envoyé/)).toBeTruthy();
    });
  });

  test("'Retour à la connexion' navigue vers Login", async () => {
    renderForgot();
    fireEvent.changeText(screen.getByPlaceholderText("Email"), "jean@test.com");
    fireEvent.press(screen.getByText("Envoyer le lien"));
    await waitFor(() => {
      expect(screen.getByText("Retour à la connexion")).toBeTruthy();
    });
    fireEvent.press(screen.getByText("Retour à la connexion"));
    expect(mockNavigate).toHaveBeenCalledWith("Login");
  });
});

describe("ForgotPasswordScreen — Navigation", () => {
  test("lien retour navigue vers Login", () => {
    renderForgot();
    fireEvent.press(screen.getByText("connexion"));
    expect(mockNavigate).toHaveBeenCalledWith("Login");
  });
});
