// PresenceOS Mobile — Firebase Auth Store (Zustand)
// Wraps Firebase Auth with a Zustand store for reactive state.

import { create } from "zustand";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  sendPasswordResetEmail,
  updateProfile,
  onAuthStateChanged,
  signInWithCredential,
  GoogleAuthProvider,
  User as FirebaseUser,
} from "firebase/auth";
import { auth } from "@/lib/firebase";

interface AuthState {
  user: FirebaseUser | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthActions {
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: (idToken: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<string | null>;
  resetPassword: (email: string) => Promise<void>;
  _initListener: () => () => void;
  _setUser: (user: FirebaseUser | null) => Promise<void>;
}

type AuthStore = AuthState & AuthActions;

export const useAuthStore = create<AuthStore>((set, get) => ({
  user: null,
  token: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email, password) => {
    const credential = await signInWithEmailAndPassword(auth, email, password);
    const token = await credential.user.getIdToken();
    set({
      user: credential.user,
      token,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  loginWithGoogle: async (idToken) => {
    const credential = GoogleAuthProvider.credential(idToken);
    const result = await signInWithCredential(auth, credential);
    const token = await result.user.getIdToken();
    set({
      user: result.user,
      token,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  register: async (email, password, fullName) => {
    const credential = await createUserWithEmailAndPassword(auth, email, password);
    await updateProfile(credential.user, { displayName: fullName });
    const token = await credential.user.getIdToken();
    set({
      user: credential.user,
      token,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  logout: async () => {
    await signOut(auth);
    set({ user: null, token: null, isAuthenticated: false, isLoading: false });
  },

  refreshToken: async () => {
    const { user } = get();
    if (!user) return null;
    const token = await user.getIdToken(true);
    set({ token });
    return token;
  },

  resetPassword: async (email) => {
    await sendPasswordResetEmail(auth, email);
  },

  _initListener: () => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (user) {
        const token = await user.getIdToken();
        set({ user, token, isAuthenticated: true, isLoading: false });
      } else {
        set({ user: null, token: null, isAuthenticated: false, isLoading: false });
      }
    });
    return unsubscribe;
  },

  _setUser: async (user) => {
    if (user) {
      const token = await user.getIdToken();
      set({ user, token, isAuthenticated: true, isLoading: false });
    } else {
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  },
}));
