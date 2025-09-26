"use client";

import React from "react";
import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

type APIError = { status?: number; name?: string };

function isAPIError(e: unknown): e is APIError {
  return typeof e === "object" && e !== null && ("status" in e || "name" in e);
}

interface QueryProviderProps {
  children: ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  // Create a client
  const [queryClient] = React.useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // With SSR, we usually want to set some default staleTime
            // above 0 to avoid refetching immediately on the client
            staleTime: 60 * 1000, // 1 minute
            retry: (failureCount, error: unknown) => {
              if (isAPIError(error) && typeof error.status === "number") {
                if (error.status === 408 || error.status === 429) return failureCount < 2;
                if (error.status >= 400 && error.status < 500) return false;
              }
              return failureCount < 3;
            },
            retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
          },
          mutations: {
            retry: (failureCount, error: unknown) => {
              if (isAPIError(error) && error.name === "NetworkError") return failureCount < 2;
              return false;
            },
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}