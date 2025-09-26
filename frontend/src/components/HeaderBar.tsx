"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoginDialog, useLoginDialog } from "@/components/LoginDialog";
import { LogIn } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useSessionStore } from "@/lib/stores";
import { cn } from "@/lib/utils";

interface HeaderBarProps {
  className?: string;
}

export function HeaderBar({ className }: HeaderBarProps) {
  const router = useRouter();
  const auth = useAuth();
  const loginDialog = useLoginDialog();


  return (
    <header className={cn(
      "sticky top-0 z-50 w-full border-b border-primary/10 glass backdrop-blur-xl shadow-lg",
      className
    )}>
      <div className="container flex h-16 items-center px-6 justify-between">
        {/* Titre centré */}
        <div className="flex-1 flex justify-center">
          <h1 className="text-xl font-bold text-foreground">Nouvelle-rive</h1>
        </div>

        {/* Informations utilisateur à droite */}
        <div className="flex items-center space-x-3">
          {auth.isAuthenticated ? (
            <>
              {/* Espace/Tenant */}
              {auth.currentTenant && (
                <Badge variant="outline" className="text-xs">
                  {auth.currentTenant}
                </Badge>
              )}

              {/* Déconnexion */}
              <Button
                variant="ghost"
                size="sm"
                onClick={auth.logout}
                className="text-muted-foreground hover:text-foreground"
              >
                Déconnexion
              </Button>
            </>
          ) : (
            <Button
              variant="default"
              size="sm"
              onClick={loginDialog.openDialog}
            >
              Connexion
            </Button>
          )}
        </div>
      </div>

      {/* Login Dialog */}
      <LoginDialog
        open={loginDialog.open}
        onOpenChange={loginDialog.setOpen}
        onSuccess={() => {
          // Redirect to search page after successful login using Next.js router
          router.push("/search");
        }}
      />

      {/* Auto-open login dialog when needed */}
      {auth.needsLogin && !loginDialog.open && (
        <AutoLoginPrompt onOpenLogin={loginDialog.openDialog} />
      )}
    </header>
  );
}

// Component to auto-open login dialog when auth is needed
function AutoLoginPrompt({ onOpenLogin }: { onOpenLogin: () => void }) {
  const { setNeedsLogin } = useAuth();

  React.useEffect(() => {
    const timer = setTimeout(() => {
      onOpenLogin();
      setNeedsLogin(false);
    }, 100);

    return () => clearTimeout(timer);
  }, [onOpenLogin, setNeedsLogin]);

  return null;
}