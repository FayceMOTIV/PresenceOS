/**
 * Tests du LoginScreen
 */

import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react-native";
import { Alert } from "react-native";
import LoginScreen from "@/screens/auth/LoginScreen";
import { AuthContext } from "@/contexts/BrandContext";
import * as Google from "expo-auth-session/providers/google";

jest.setTimeout(60000);
jest.spyOn(Alert, "alert");

// loginWithGoogle mock — must be defined before jest.mock factory (which is hoisted).
// We use a plain object so the factory can capture it by reference.
const mockGoogleLogin = { fn: jest.fn() };

jest.mock("@/stores/authStore", () => ({
  // useAuthStore is called with a selector: (state) => state.loginWithGoogle
  useAuthStore: (selector: (s: any) => any) =>
    selector({ loginWithGoogle: (...args: any[]) => mockGoogleLogin.fn(...args) }),
}));

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
  mockGoogleLogin.fn = jest.fn();
  // Reset Google.useAuthRequest to default (no response)
  (Google.useAuthRequest as jest.Mock).mockReturnValue([null, null, jest.fn()]);
});

describe("LoginScreen — Rendu", () => {
  test("affiche le logo RS3", () => {
    renderWithAuth();
    expect(screen.getByText("RS3")).toBeTruthy();
  });

  test("affiche le sous-titre français", () => {
    renderWithAuth();
    expect(screen.getByText("Connectez-vous a votre compte")).toBeTruthy();
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

    await act(async () => {
      fireEvent.changeText(screen.getByPlaceholderText("Email"), "test@test.com");
      fireEvent.changeText(
        screen.getByPlaceholderText("Mot de passe"),
        "password123"
      );
    });

    await act(async () => {
      fireEvent.press(screen.getByText("Se connecter"));
    });

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith("test@test.com", "password123");
    });
  });

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
        "Connexion echouee",
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
        "Connexion echouee",
        "Trop de tentatives, reessayez plus tard"
      );
    });
  });
});

describe("LoginScreen — Navigation", () => {
  test("affiche les liens Register/ForgotPassword si navigation fournie", () => {
    const mockNav = { navigate: jest.fn() };
    renderWithAuth({ navigation: mockNav });

    expect(screen.getByText("Mot de passe oublie ?")).toBeTruthy();
    expect(screen.getByText(/Creer un compte/)).toBeTruthy();
  });

  test("navigue vers ForgotPassword", () => {
    const mockNav = { navigate: jest.fn() };
    renderWithAuth({ navigation: mockNav });

    fireEvent.press(screen.getByText("Mot de passe oublie ?"));
    expect(mockNav.navigate).toHaveBeenCalledWith("ForgotPassword");
  });

  test("navigue vers Register", () => {
    const mockNav = { navigate: jest.fn() };
    renderWithAuth({ navigation: mockNav });

    fireEvent.press(screen.getByText(/Creer un compte/));
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

describe("LoginScreen — Codes d'erreur supplémentaires", () => {
  test("affiche l'erreur auth/user-not-found", async () => {
    const error: any = new Error("user not found");
    error.code = "auth/user-not-found";
    mockLogin.mockRejectedValue(error);

    renderWithAuth();
    fireEvent.changeText(screen.getByPlaceholderText("Email"), "notfound@test.com");
    fireEvent.changeText(screen.getByPlaceholderText("Mot de passe"), "pass123");
    fireEvent.press(screen.getByText("Se connecter"));

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        "Connexion echouee",
        "Email ou mot de passe incorrect"
      );
    });
  });

  test("affiche l'erreur auth/invalid-credential", async () => {
    const error: any = new Error("invalid credential");
    error.code = "auth/invalid-credential";
    mockLogin.mockRejectedValue(error);

    renderWithAuth();
    fireEvent.changeText(screen.getByPlaceholderText("Email"), "user@test.com");
    fireEvent.changeText(screen.getByPlaceholderText("Mot de passe"), "badpass");
    fireEvent.press(screen.getByText("Se connecter"));

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        "Connexion echouee",
        "Email ou mot de passe incorrect"
      );
    });
  });

  test("affiche l'erreur auth/user-disabled", async () => {
    const error: any = new Error("user disabled");
    error.code = "auth/user-disabled";
    mockLogin.mockRejectedValue(error);

    renderWithAuth();
    fireEvent.changeText(screen.getByPlaceholderText("Email"), "disabled@test.com");
    fireEvent.changeText(screen.getByPlaceholderText("Mot de passe"), "pass123");
    fireEvent.press(screen.getByText("Se connecter"));

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        "Connexion echouee",
        "Ce compte a ete desactive"
      );
    });
  });

  test("affiche l'erreur auth/invalid-email", async () => {
    const error: any = new Error("invalid email");
    error.code = "auth/invalid-email";
    mockLogin.mockRejectedValue(error);

    renderWithAuth();
    fireEvent.changeText(screen.getByPlaceholderText("Email"), "bademail");
    fireEvent.changeText(screen.getByPlaceholderText("Mot de passe"), "pass123");
    fireEvent.press(screen.getByText("Se connecter"));

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        "Connexion echouee",
        "Adresse email invalide"
      );
    });
  });

  test("affiche le message d'erreur de l'API (response.data.detail)", async () => {
    const error: any = new Error("API error");
    error.response = { data: { detail: "Compte suspendu par l'administrateur" } };
    mockLogin.mockRejectedValue(error);

    renderWithAuth();
    fireEvent.changeText(screen.getByPlaceholderText("Email"), "user@test.com");
    fireEvent.changeText(screen.getByPlaceholderText("Mot de passe"), "pass123");
    fireEvent.press(screen.getByText("Se connecter"));

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        "Connexion echouee",
        "Compte suspendu par l'administrateur"
      );
    });
  });

  test("affiche le message d'erreur générique pour les codes inconnus", async () => {
    const error: any = new Error("unknown error");
    error.code = "auth/unknown-code";
    mockLogin.mockRejectedValue(error);

    renderWithAuth();
    fireEvent.changeText(screen.getByPlaceholderText("Email"), "user@test.com");
    fireEvent.changeText(screen.getByPlaceholderText("Mot de passe"), "pass123");
    fireEvent.press(screen.getByText("Se connecter"));

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        "Connexion echouee",
        "Identifiants invalides"
      );
    });
  });
});

describe("LoginScreen — Google Sign-In", () => {
  test("affiche le bouton 'Continuer avec Google'", () => {
    renderWithAuth();
    expect(screen.getByText("Continuer avec Google")).toBeTruthy();
  });

  // GOOGLE_WEB_CLIENT_ID is read from process.env at module parse time.
  // In the test environment the env var is not set, so it defaults to "".
  // The handleGoogleLogin guard `if (!GOOGLE_WEB_CLIENT_ID)` will always trigger
  // in these tests, showing "Google Sign-In non configure".
  test("affiche une alerte quand GOOGLE_WEB_CLIENT_ID n'est pas configuré (comportement de test)", async () => {
    renderWithAuth();

    await act(async () => {
      fireEvent.press(screen.getByText("Continuer avec Google"));
    });

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        "Erreur",
        "Google Sign-In non configure"
      );
    });
  });

  // Since GOOGLE_WEB_CLIENT_ID is always "" in tests, promptGoogleAsync is never
  // reached via the button. We test it by providing a response directly via
  // the useAuthRequest mock (simulating a completed OAuth flow).
  test("appelle loginWithGoogle quand googleResponse.type === 'success' avec idToken", async () => {
    mockGoogleLogin.fn.mockResolvedValue(undefined);

    const successResponse = {
      type: "success",
      authentication: { idToken: "google-id-token-xyz" },
    };
    (Google.useAuthRequest as jest.Mock).mockReturnValue([null, successResponse, jest.fn()]);

    renderWithAuth();

    await waitFor(() => {
      expect(mockGoogleLogin.fn).toHaveBeenCalledWith("google-id-token-xyz");
    });
  });

  test("affiche une alerte quand loginWithGoogle échoue", async () => {
    const googleError = new Error("Google auth failed");
    mockGoogleLogin.fn.mockRejectedValue(googleError);

    const successResponse = {
      type: "success",
      authentication: { idToken: "bad-token" },
    };
    (Google.useAuthRequest as jest.Mock).mockReturnValue([null, successResponse, jest.fn()]);

    renderWithAuth();

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        "Erreur Google",
        "Google auth failed"
      );
    });
  });

  test("ne déclenche pas loginWithGoogle si googleResponse.type !== 'success'", async () => {
    const cancelResponse = { type: "dismiss" };
    (Google.useAuthRequest as jest.Mock).mockReturnValue([null, cancelResponse, jest.fn()]);

    renderWithAuth();

    // Wait a tick to let any useEffect run
    await act(async () => {});

    expect(mockGoogleLogin.fn).not.toHaveBeenCalled();
  });

  test("ne déclenche pas loginWithGoogle si googleResponse est null", async () => {
    (Google.useAuthRequest as jest.Mock).mockReturnValue([null, null, jest.fn()]);

    renderWithAuth();

    await act(async () => {});

    expect(mockGoogleLogin.fn).not.toHaveBeenCalled();
  });

  test("ne déclenche pas loginWithGoogle si idToken est null", async () => {
    const successResponseNoToken = {
      type: "success",
      authentication: { idToken: null },
    };
    (Google.useAuthRequest as jest.Mock).mockReturnValue([null, successResponseNoToken, jest.fn()]);

    renderWithAuth();

    await act(async () => {});

    expect(mockGoogleLogin.fn).not.toHaveBeenCalled();
  });
});
