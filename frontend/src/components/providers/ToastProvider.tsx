"use client";

import React from "react";
import type { ReactNode } from "react";
import { Toaster } from "@/components/ui/sonner";

interface ToastProviderProps {
  children: ReactNode;
}

export function ToastProvider({ children }: ToastProviderProps) {
  return (
    <>
      {children}
      <Toaster 
        position="bottom-right"
        expand={false}
        richColors
        closeButton
        toastOptions={{
          style: {
            background: "hsl(var(--background))",
            color: "hsl(var(--foreground))",
            border: "1px solid hsl(var(--border))",
          },
        }}
      />
    </>
  );
}