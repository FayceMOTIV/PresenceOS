// PresenceOS Mobile — Brand & Auth Contexts
// Extracted from App.tsx to break the require cycle:
//   App → TabNavigator → Screens → App

import React from "react";
import { Brand } from "@/types";

export interface AuthContextType {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, workspaceName?: string) => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
}

export const AuthContext = React.createContext<AuthContextType | null>(null);

export const BrandContext = React.createContext<{
  activeBrand: Brand | null;
  brands: Brand[];
  switchBrand: (id: string) => void;
  isLoading: boolean;
} | null>(null);
