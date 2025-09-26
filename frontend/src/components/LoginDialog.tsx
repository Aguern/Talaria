"use client";

import React from "react";
import { useForm } from "react-hook-form";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, AlertCircle } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { authAPI, handleAPIError } from "@/lib/api";
import { useSessionStore } from "@/lib/stores";
import { isValidEmail } from "@/lib/utils";
import type { LoginRequest } from "@/lib/types";

interface LoginDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

interface FormData {
  email: string;
  password: string;
}

export function LoginDialog({ 
  open, 
  onOpenChange, 
  onSuccess 
}: LoginDialogProps) {
  const sessionStore = useSessionStore();
  
  // Login mutation
  const loginMutation = useMutation({
    mutationFn: (credentials: LoginRequest) => authAPI.login(credentials),
    onSuccess: async (response) => {
      console.log("Login response:", response);
      
      // Save directly to sessionStorage first
      if (typeof window !== 'undefined') {
        sessionStorage.setItem('mvp_btp_session', JSON.stringify({
          token: response.token,
          clientId: response.user.client_id
        }));
      }
      
      // Set session data in store
      sessionStore.setSession({
        token: response.token,
        clientId: response.user.client_id,
        role: response.user.role,
        userInfo: response.user,
      });
      
      console.log("Login successful, token saved:", response.token);
      console.log("SessionStorage saved:", sessionStorage.getItem('mvp_btp_session'));
      onSuccess?.();
    },
    onError: handleAPIError,
  });
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setError,
  } = useForm<FormData>();

  const onSubmit = async (data: FormData) => {
    try {
      await loginMutation.mutateAsync(data);
      reset();
      onOpenChange(false);
    } catch (err: any) {
      // Error is already handled by mutation, but we can add form-specific errors
      if (err?.status === 401) {
        setError("email", { message: "Email ou mot de passe incorrect" });
        setError("password", { message: "Email ou mot de passe incorrect" });
      }
    }
  };

  // Reset form when dialog closes
  React.useEffect(() => {
    if (!open) {
      reset();
    }
  }, [open, reset]);

  // Focus management
  const emailRef = React.useRef<HTMLInputElement>(null);
  React.useEffect(() => {
    if (open && emailRef.current) {
      const timer = setTimeout(() => {
        emailRef.current?.focus();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px] bg-white dark:bg-slate-800 border-0 shadow-2xl" data-testid="login-dialog">
        <DialogHeader className="text-center space-y-4 pb-6">
          {/* Logo */}
          <div className="mx-auto w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <div>
            <DialogTitle className="text-2xl font-semibold text-slate-900 dark:text-white">
              Connexion
            </DialogTitle>
            <DialogDescription className="text-slate-600 dark:text-slate-400 mt-2">
              Accédez à votre espace documentaire sécurisé
            </DialogDescription>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" data-testid="login-form">
          <React.Fragment>
            {loginMutation.error ? (
              <Alert variant="destructive" data-testid="error-message">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  {(loginMutation.error as any)?.message || "Une erreur s'est produite lors de la connexion"}
                </AlertDescription>
              </Alert>
            ) : null}
          </React.Fragment>

          {/* Email field */}
          <div className="space-y-2">
            <Label htmlFor="email" className="text-slate-700 dark:text-slate-300 font-medium">
              Adresse email
            </Label>
            <Input
              id="email"
              type="email"
              placeholder="admin@acme.com"
              disabled={loginMutation.isPending}
              data-testid="email-input"
              className="h-11 bg-slate-50 dark:bg-slate-700 border-slate-200 dark:border-slate-600 focus:border-blue-500 focus:ring-blue-500/20"
              {...register("email", {
                required: "L'email est requis",
                validate: (value) => 
                  isValidEmail(value) || "Email invalide",
              })}
              aria-invalid={errors.email ? "true" : "false"}
              aria-describedby={errors.email ? "email-error" : undefined}
            />
            {errors.email && (
              <p 
                id="email-error" 
                className="text-sm text-red-600 dark:text-red-400"
                role="alert"
              >
                {errors.email.message}
              </p>
            )}
          </div>

          {/* Password field */}
          <div className="space-y-2">
            <Label htmlFor="password" className="text-slate-700 dark:text-slate-300 font-medium">
              Mot de passe
            </Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              disabled={loginMutation.isPending}
              data-testid="password-input"
              className="h-11 bg-slate-50 dark:bg-slate-700 border-slate-200 dark:border-slate-600 focus:border-blue-500 focus:ring-blue-500/20"
              {...register("password", {
                required: "Le mot de passe est requis",
                minLength: {
                  value: 3,
                  message: "Le mot de passe doit faire au moins 3 caractères",
                },
              })}
              aria-invalid={errors.password ? "true" : "false"}
              aria-describedby={errors.password ? "password-error" : undefined}
            />
            {errors.password && (
              <p 
                id="password-error" 
                className="text-sm text-red-600 dark:text-red-400"
                role="alert"
              >
                {errors.password.message}
              </p>
            )}
          </div>

          {/* Demo credentials hint - only in dev */}
          {process.env.NODE_ENV === "development" && (
            <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4 border border-slate-200 dark:border-slate-600">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                Comptes de test :
              </h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">ACME :</span>
                  <code className="text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 px-2 py-1 rounded">
                    admin@acme.com
                  </code>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">BTP Demo :</span>
                  <code className="text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 px-2 py-1 rounded">
                    demo@mvp-btp.fr
                  </code>
                </div>
                <div className="pt-1 border-t border-slate-200 dark:border-slate-600">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-600 dark:text-slate-400">Mot de passe :</span>
                    <code className="text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30 px-2 py-1 rounded">
                      admin123 / demo123
                    </code>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex space-x-3 pt-6">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loginMutation.isPending}
              data-testid="cancel-button"
              className="flex-1 h-11 border-slate-200 dark:border-slate-600 text-slate-700 dark:text-slate-300"
            >
              Annuler
            </Button>
            <Button 
              type="submit" 
              disabled={loginMutation.isPending}
              className="flex-1 h-11 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white border-0 shadow-lg"
              data-testid="login-button"
            >
              {loginMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Connexion...
                </>
              ) : (
                "Se connecter"
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// Hook for easy dialog management
export function useLoginDialog() {
  const [open, setOpen] = React.useState(false);

  const openDialog = () => setOpen(true);
  const closeDialog = () => setOpen(false);

  return {
    open,
    openDialog,
    closeDialog,
    setOpen,
  };
}