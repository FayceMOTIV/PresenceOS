// PresenceOS Mobile — Brand & Auth Contexts
// Extracted from App.tsx to break the require cycle:
//   App → TabNavigator → Screens → App

import React from "react";
import { Brand } from "@/types";

export const AuthContext = React.createContext<any>(null);

export const BrandContext = React.createContext<{
  activeBrand: Brand | null;
  brands: Brand[];
  switchBrand: (id: string) => void;
  isLoading: boolean;
} | null>(null);
