"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Building2, LogIn, UserPlus, Loader2, Eye, EyeOff, AlertCircle } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";

export function AuthForm() {
  const [isLoginView, setIsLoginView] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tenantName, setTenantName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const auth = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      if (isLoginView) {
        await auth.login({ email, password });
        toast.success("Connexion réussie !");
        router.push("/search");
      } else {
        await auth.register({ email, password, tenant_name: tenantName || undefined });
        toast.success("Compte créé avec succès !");
        // Basculer automatiquement vers la vue de connexion après inscription
        setIsLoginView(true);
        // Garder l'email pour faciliter la connexion
        setPassword("");
        setTenantName("");
      }
    } catch (error: any) {
      setError(error.message || "Une erreur s'est produite.");
    } finally {
      setIsLoading(false);
    }
  };

  const switchView = () => {
    setIsLoginView(!isLoginView);
    // Réinitialiser le formulaire lors du changement de vue
    setPassword("");
    setError(null);
    if (isLoginView) {
      setTenantName("");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 via-transparent to-purple-50/50 dark:from-blue-950/20 dark:to-purple-950/20"></div>
      <div className="absolute top-20 left-1/4 w-72 h-72 bg-blue-100/30 dark:bg-blue-800/20 rounded-full blur-3xl opacity-60"></div>
      <div className="absolute bottom-20 right-1/3 w-96 h-96 bg-purple-100/30 dark:bg-purple-800/20 rounded-full blur-3xl opacity-60"></div>
      
      <div className="relative z-10 container mx-auto px-6 py-24">
        <div className="flex items-center justify-center min-h-screen">
          <div className="max-w-md w-full">
            {/* Logo & Title */}
            <div className="text-center mb-8">
              <div className="mx-auto w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-6">
                <Building2 className="h-8 w-8 text-white" />
              </div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                Rive BOFIP
              </h1>
              <p className="text-slate-600 dark:text-slate-400 text-lg">
                Assistant intelligent pour la doctrine fiscale
              </p>
            </div>

            {/* Auth Card */}
            <Card className="shadow-xl border-0 bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl">
              <CardHeader className="space-y-1 text-center">
                <CardTitle className="text-2xl font-semibold">
                  {isLoginView ? "Connexion" : "Inscription"}
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  {isLoginView
                    ? "Accédez à votre espace documentaire sécurisé"
                    : "Créez votre compte pour commencer"}
                </p>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  {error && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  )}
                  
                  {!isLoginView && (
                    <div className="space-y-2">
                      <Label htmlFor="tenantName" className="text-slate-700 dark:text-slate-300 font-medium">
                        Nom de votre organisation (optionnel)
                      </Label>
                      <Input
                        id="tenantName"
                        type="text"
                        value={tenantName}
                        onChange={(e) => setTenantName(e.target.value)}
                        placeholder="Ex: Cabinet Dupont"
                        className="h-11 bg-slate-50 dark:bg-slate-700 border-slate-200 dark:border-slate-600 focus:border-blue-500 focus:ring-blue-500/20"
                        disabled={isLoading}
                      />
                    </div>
                  )}
                  
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-slate-700 dark:text-slate-300 font-medium">
                      Adresse email
                    </Label>
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="vous@exemple.com"
                      required
                      className="h-11 bg-slate-50 dark:bg-slate-700 border-slate-200 dark:border-slate-600 focus:border-blue-500 focus:ring-blue-500/20"
                      disabled={isLoading}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="password" className="text-slate-700 dark:text-slate-300 font-medium">
                      Mot de passe
                    </Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        required
                        className="h-11 bg-slate-50 dark:bg-slate-700 border-slate-200 dark:border-slate-600 focus:border-blue-500 focus:ring-blue-500/20 pr-10"
                        disabled={isLoading}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 p-1"
                        tabIndex={-1}
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                  
                  <Button 
                    type="submit" 
                    className="w-full h-11 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white border-0 shadow-lg"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        {isLoginView ? "Connexion..." : "Inscription..."}
                      </>
                    ) : isLoginView ? (
                      <>
                        <LogIn className="mr-2 h-5 w-5" />
                        Se connecter
                      </>
                    ) : (
                      <>
                        <UserPlus className="mr-2 h-5 w-5" />
                        Créer mon compte
                      </>
                    )}
                  </Button>
                </form>

                {/* Demo Credentials - only shown on login view */}
                {isLoginView && process.env.NODE_ENV === "development" && (
                  <div className="mt-6 p-4 rounded-lg bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600">
                    <h3 className="text-sm font-medium mb-3 text-slate-700 dark:text-slate-300">
                      Compte de test disponible :
                    </h3>
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-600 dark:text-slate-400">Email :</span>
                        <code className="text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 px-2 py-1 rounded">
                          demo@bofip.fr
                        </code>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-600 dark:text-slate-400">Mot de passe :</span>
                        <code className="text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30 px-2 py-1 rounded">
                          demo123
                        </code>
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-600 text-center">
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {isLoginView ? "Pas encore de compte ?" : "Déjà inscrit ?"}
                  </p>
                  <Button
                    type="button"
                    variant="link"
                    onClick={switchView}
                    className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
                  >
                    {isLoginView ? "Créer un compte" : "Se connecter"}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Features */}
            <div className="mt-8 text-center space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="p-3 rounded-lg bg-white/50 dark:bg-slate-800/50 backdrop-blur">
                  <div className="font-medium text-slate-700 dark:text-slate-300">Multi-tenant</div>
                  <div className="text-slate-500 dark:text-slate-400">Isolation sécurisée</div>
                </div>
                <div className="p-3 rounded-lg bg-white/50 dark:bg-slate-800/50 backdrop-blur">
                  <div className="font-medium text-slate-700 dark:text-slate-300">Recherche avancée</div>
                  <div className="text-slate-500 dark:text-slate-400">Doctrine fiscale</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}