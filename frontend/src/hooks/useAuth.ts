import React from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { authAPI, handleAPIError } from "@/lib/api";
import { useAuth as useAuthStore } from "@/lib/stores";
import type { LoginRequest, RegisterRequest } from "@/lib/types";

export function useAuth() {
  const auth = useAuthStore();

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: (credentials: LoginRequest) => authAPI.login(credentials),
    onSuccess: async (response) => {
      // Set initial session data
      auth.setSession({
        token: response.token,
        clientId: response.user.client_id,
        role: response.user.role,
      });

      // Fetch additional user info
      try {
        const userInfo = await authAPI.getMe();
        auth.setSession({
          token: response.token,
          clientId: response.user.client_id,
          role: response.user.role,
          vertical: userInfo.vertical,
          userInfo,
        });
      } catch (error) {
        console.warn("Failed to fetch user info:", error);
      }
    },
    onError: handleAPIError,
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: (data: RegisterRequest) => authAPI.register(data),
    onError: handleAPIError,
  });

  // User info query (only when authenticated)
  const userInfoQuery = useQuery({
    queryKey: ["userInfo"],
    queryFn: authAPI.getMe,
    enabled: auth.isAuthenticated,
    staleTime: 60 * 1000, // 1 minute
    retry: (failureCount, error: any) => {
      // Don't retry on auth errors
      if (error?.status === 401) return false;
      return failureCount < 3;
    },
  });

  // Update store when user info changes
  React.useEffect(() => {
    if (userInfoQuery.data && auth.isAuthenticated) {
      auth.setSession({
        token: auth.token || "", // Keep existing token, not the email!
        clientId: auth.currentTenant || "",
        role: auth.role || "user",
        vertical: userInfoQuery.data.vertical,
        userInfo: userInfoQuery.data,
      });
    }
  }, [userInfoQuery.data, auth.isAuthenticated, auth.token, auth.currentTenant, auth.role]);

  const login = (credentials: LoginRequest) => {
    return loginMutation.mutateAsync(credentials);
  };

  const register = (data: RegisterRequest) => {
    return registerMutation.mutateAsync(data);
  };

  const logout = () => {
    authAPI.logout();
    auth.logout();
  };

  return {
    // State
    isAuthenticated: auth.isAuthenticated,
    user: auth.user,
    tenants: auth.tenants,
    currentTenant: auth.currentTenant,
    token: auth.token,
    role: auth.role,
    vertical: auth.vertical,
    needsLogin: auth.needsLogin,

    // Actions
    login,
    register,
    logout,
    setNeedsLogin: auth.setNeedsLogin,

    // Loading states
    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
    isLoadingUserInfo: userInfoQuery.isLoading,

    // Errors
    loginError: loginMutation.error,
    registerError: registerMutation.error,
    userInfoError: userInfoQuery.error,

    // Utilities
    canAccess: (requiredRole?: "admin" | "user") => {
      if (!auth.isAuthenticated) return false;
      if (!requiredRole) return true;
      if (requiredRole === "admin") return auth.role === "admin";
      return auth.role === "admin" || auth.role === "user";
    },
  };
}

export function useLogin() {
  const { login, isLoggingIn, loginError } = useAuth();
  return { login, isLoading: isLoggingIn, error: loginError };
}

export function useRegister() {
  const { register, isRegistering, registerError } = useAuth();
  return { register, isLoading: isRegistering, error: registerError };
}