"use client";

import React from "react";
import type { ReactNode } from "react";
export default function MainLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="relative flex min-h-screen flex-col">
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
}

