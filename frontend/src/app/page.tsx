"use client";

import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import React, { useEffect } from "react";
import { AuthForm } from "@/components/auth/AuthForm";

export default function HomePage() {
  const auth = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Si l'utilisateur est déjà connecté, on le redirige vers le chat.
    if (auth.isAuthenticated) {
      router.replace("/chat");
    }
  }, [auth.isAuthenticated, router]);

  // Si l'utilisateur n'est pas connecté, on affiche le formulaire d'authentification.
  if (!auth.isAuthenticated) {
    return <AuthForm />;
  }
  
  // Pendant la redirection, on n'affiche rien.
  return null;
}