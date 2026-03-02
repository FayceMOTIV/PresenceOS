/**
 * Tests du RegisterScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react-native";
import { Alert } from "react-native";
import RegisterScreen from "@/screens/auth/RegisterScreen";
import { AuthContext } from "@/contexts/BrandContext";

jest.spyOn(Alert, "alert");

const mockRegister = jest.fn();
const mockAuth = { login: jest.fn(), register: mockRegister, logout: jest.fn(), resetPassword: jest.fn() };
const mockNavigate = jest.fn();
const navigation = { navigate: mockNavigate } as any;

function renderRegister(auth = mockAuth) {
  return render(
    <AuthContext.Provider value={auth}>
      <RegisterScreen navigation={navigation} />
    </AuthContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  mockRegister.mockResolvedValue({});
});

describe("RegisterScreen — Rendu", () => {
  test("affiche le logo RS3", () => {
    renderRegister();
    expect(screen.getByText("RS3")).toBeTruthy();
  });

  test("affiche 'Créer un compte'", () => {
    renderRegister();
    expect(screen.getByText("Créer un compte")).toBeTruthy();
  });

  test("affiche les 4 champs", () => {
    renderRegister();
    expect(screen.getByPlaceholderText("Nom complet")).toBeTruthy();
    expect(screen.getByPlaceholderText("Email")).toBeTruthy();
    expect(screen.getByPlaceholderText("Mot de passe (min. 8 caractères)")).toBeTruthy();
    expect(screen.getByPlaceholderText("Nom du restaurant (optionnel)")).toBeTruthy();
  });

  test("affiche le bouton 'Créer mon compte'", () => {
    renderRegister();
    expect(screen.getByText("Créer mon compte")).toBeTruthy();
  });

  test("affiche le lien 'Se connecter'", () => {
    renderRegister();
    expect(screen.getByText("Se connecter")).toBeTruthy();
  });
});

describe("RegisterScreen — Validation", () => {
  test("alerte si nom vide", () => {
    renderRegister();
    fireEvent.press(screen.getByText("Créer mon compte"));
    expect(Alert.alert).toHaveBeenCalledWith("Erreur", "Veuillez entrer votre nom complet");
  });

  test("alerte si email vide", () => {
    renderRegister();
    fireEvent.changeText(screen.getByPlaceholderText("Nom complet"), "Jean Dupont");
    fireEvent.press(screen.getByText("Créer mon compte"));
    expect(Alert.alert).toHaveBeenCalledWith("Erreur", "Veuillez entrer votre email");
  });

  test("alerte si mot de passe trop court", () => {
    renderRegister();
    fireEvent.changeText(screen.getByPlaceholderText("Nom complet"), "Jean");
    fireEvent.changeText(screen.getByPlaceholderText("Email"), "jean@test.com");
    fireEvent.changeText(screen.getByPlaceholderText("Mot de passe (min. 8 caractères)"), "short");
    fireEvent.press(screen.getByText("Créer mon compte"));
    expect(Alert.alert).toHaveBeenCalledWith("Erreur", "Le mot de passe doit contenir au moins 8 caractères");
  });
});

describe("RegisterScreen — Inscription", () => {
  test("appelle register avec les bons params", async () => {
    renderRegister();
    fireEvent.changeText(screen.getByPlaceholderText("Nom complet"), "Jean Dupont");
    fireEvent.changeText(screen.getByPlaceholderText("Email"), "jean@test.com");
    fireEvent.changeText(screen.getByPlaceholderText("Mot de passe (min. 8 caractères)"), "password123");
    fireEvent.changeText(screen.getByPlaceholderText("Nom du restaurant (optionnel)"), "Chez Jean");
    fireEvent.press(screen.getByText("Créer mon compte"));
    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith("jean@test.com", "password123", "Jean Dupont", "Chez Jean");
    });
  });

  test("affiche erreur email-already-in-use", async () => {
    mockRegister.mockRejectedValue({ code: "auth/email-already-in-use" });
    renderRegister();
    fireEvent.changeText(screen.getByPlaceholderText("Nom complet"), "Jean");
    fireEvent.changeText(screen.getByPlaceholderText("Email"), "jean@test.com");
    fireEvent.changeText(screen.getByPlaceholderText("Mot de passe (min. 8 caractères)"), "password123");
    fireEvent.press(screen.getByText("Créer mon compte"));
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith("Inscription échouée", "Un compte existe déjà avec cet email");
    });
  });
});

describe("RegisterScreen — Navigation", () => {
  test("'Se connecter' navigue vers Login", () => {
    renderRegister();
    fireEvent.press(screen.getByText("Se connecter"));
    expect(mockNavigate).toHaveBeenCalledWith("Login");
  });
});
