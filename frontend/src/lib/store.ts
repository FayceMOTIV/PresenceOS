import { create } from "zustand";
import type { User, Workspace, Brand } from "@/types";

interface AuthState {
  user: User | null;
  workspaces: Workspace[];
  activeWorkspaceId: string | null;
  brands: Brand[];
  activeBrandId: string | null;
  isAuthenticated: boolean;

  setUser: (user: User | null) => void;
  setWorkspaces: (workspaces: Workspace[]) => void;
  setActiveWorkspaceId: (id: string | null) => void;
  setBrands: (brands: Brand[]) => void;
  setActiveBrandId: (id: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  workspaces: [],
  activeWorkspaceId: null,
  brands: [],
  activeBrandId: null,
  isAuthenticated: false,

  setUser: (user) => set({ user, isAuthenticated: !!user }),
  setWorkspaces: (workspaces) => set({ workspaces }),
  setActiveWorkspaceId: (id) => {
    if (id) localStorage.setItem("workspace_id", id);
    set({ activeWorkspaceId: id });
  },
  setBrands: (brands) => set({ brands }),
  setActiveBrandId: (id) => {
    if (id) localStorage.setItem("brand_id", id);
    else localStorage.removeItem("brand_id");
    set({ activeBrandId: id });
  },
  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("workspace_id");
    localStorage.removeItem("brand_id");
    set({
      user: null,
      workspaces: [],
      activeWorkspaceId: null,
      brands: [],
      activeBrandId: null,
      isAuthenticated: false,
    });
    window.location.href = "/auth/login";
  },
}));
