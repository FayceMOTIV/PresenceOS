// PresenceOS Mobile — Auth Hook

import { useState, useEffect, useCallback } from "react";
import * as SecureStore from "expo-secure-store";
import { authApi } from "@/lib/api";
import { User } from "@/types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = await SecureStore.getItemAsync("auth_token");
      if (token) {
        setIsAuthenticated(true);
        // TODO: fetch user profile
      }
    } catch {
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  const login = useCallback(async (email: string, password: string) => {
    const res = await authApi.login(email, password);
    const { token, user: userData } = res.data;
    await SecureStore.setItemAsync("auth_token", token.access_token);
    await SecureStore.setItemAsync("refresh_token", token.refresh_token);
    setUser(userData);
    setIsAuthenticated(true);
  }, []);

  const logout = useCallback(async () => {
    await SecureStore.deleteItemAsync("auth_token");
    await SecureStore.deleteItemAsync("brand_id");
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  return { user, isLoading, isAuthenticated, login, logout };
}
