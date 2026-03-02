/**
 * Tests du Auth Store (Zustand + Firebase)
 */

import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  sendPasswordResetEmail,
  updateProfile,
  onAuthStateChanged,
} from "firebase/auth";

jest.mock("@/lib/firebase", () => ({
  auth: {},
}));

import { useAuthStore } from "@/stores/authStore";

const mockUser = {
  uid: "user-123",
  email: "test@presenceos.dev",
  displayName: "Test User",
  getIdToken: jest.fn().mockResolvedValue("firebase-token-abc"),
};

beforeEach(() => {
  useAuthStore.setState({
    user: null,
    token: null,
    isLoading: true,
    isAuthenticated: false,
  });
  jest.clearAllMocks();
});

describe("AuthStore — Login", () => {
  test("login réussit et met à jour le state", async () => {
    (signInWithEmailAndPassword as jest.Mock).mockResolvedValue({
      user: mockUser,
    });

    await useAuthStore.getState().login("test@presenceos.dev", "password");

    const state = useAuthStore.getState();
    expect(state.user).toBe(mockUser);
    expect(state.token).toBe("firebase-token-abc");
    expect(state.isAuthenticated).toBe(true);
    expect(state.isLoading).toBe(false);
  });

  test("login échoué lance une erreur", async () => {
    (signInWithEmailAndPassword as jest.Mock).mockRejectedValue(
      new Error("auth/wrong-password")
    );

    await expect(
      useAuthStore.getState().login("test@x.com", "wrong")
    ).rejects.toThrow("auth/wrong-password");

    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});

describe("AuthStore — Register", () => {
  test("register crée l'utilisateur et met à jour le state", async () => {
    (createUserWithEmailAndPassword as jest.Mock).mockResolvedValue({
      user: mockUser,
    });
    (updateProfile as jest.Mock).mockResolvedValue(undefined);

    await useAuthStore.getState().register("a@b.com", "pass", "John Doe");

    expect(updateProfile).toHaveBeenCalledWith(mockUser, {
      displayName: "John Doe",
    });
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.token).toBe("firebase-token-abc");
  });
});

describe("AuthStore — Logout", () => {
  test("logout reset le state", async () => {
    // Set logged in state first
    useAuthStore.setState({
      user: mockUser as any,
      token: "token",
      isAuthenticated: true,
      isLoading: false,
    });
    (signOut as jest.Mock).mockResolvedValue(undefined);

    await useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });
});

describe("AuthStore — Token Refresh", () => {
  test("refreshToken retourne un nouveau token si user connecté", async () => {
    useAuthStore.setState({
      user: mockUser as any,
      token: "old-token",
      isAuthenticated: true,
      isLoading: false,
    });
    mockUser.getIdToken.mockResolvedValue("new-token-xyz");

    const token = await useAuthStore.getState().refreshToken();

    expect(token).toBe("new-token-xyz");
    expect(useAuthStore.getState().token).toBe("new-token-xyz");
  });

  test("refreshToken retourne null si pas d'user", async () => {
    const token = await useAuthStore.getState().refreshToken();
    expect(token).toBeNull();
  });
});

describe("AuthStore — Reset Password", () => {
  test("resetPassword appelle Firebase", async () => {
    (sendPasswordResetEmail as jest.Mock).mockResolvedValue(undefined);

    await useAuthStore.getState().resetPassword("test@test.com");

    expect(sendPasswordResetEmail).toHaveBeenCalled();
  });
});

describe("AuthStore — Auth Listener", () => {
  test("_initListener s'abonne à onAuthStateChanged", () => {
    (onAuthStateChanged as jest.Mock).mockReturnValue(jest.fn());

    const unsub = useAuthStore.getState()._initListener();

    expect(onAuthStateChanged).toHaveBeenCalled();
    expect(typeof unsub).toBe("function");
  });

  test("_setUser met à jour le state avec un user", async () => {
    mockUser.getIdToken.mockResolvedValue("firebase-token-abc");
    await useAuthStore.getState()._setUser(mockUser as any);

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.token).toBe("firebase-token-abc");
  });

  test("_setUser null déconnecte", async () => {
    useAuthStore.setState({
      user: mockUser as any,
      token: "t",
      isAuthenticated: true,
      isLoading: false,
    });

    await useAuthStore.getState()._setUser(null);

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
  });
});
