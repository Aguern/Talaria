"use client";

import { useAuth } from "@/hooks/useAuth";
import { useRecipesStore } from "@/lib/stores/recipes.store";
import React, { useEffect } from "react";
import { AuthForm } from "@/components/auth/AuthForm";
import { RecipeCard } from "@/components/recipes/RecipeCard";
import { Card } from "@/components/ui/card";
import { Wind, Loader2, AlertCircle } from "lucide-react";

export default function HomePage() {
  const auth = useAuth();
  const { recipes, isLoadingRecipes, recipesError, loadRecipes } = useRecipesStore();

  // Load recipes when user becomes authenticated
  useEffect(() => {
    if (auth.isAuthenticated) {
      loadRecipes();
    }
  }, [auth.isAuthenticated, loadRecipes]);

  // Si l'utilisateur n'est pas connecté, on affiche le formulaire d'authentification.
  if (!auth.isAuthenticated) {
    return <AuthForm />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-[#3898FF] to-[#8A78F2] shadow-2xl mb-6">
            <Wind className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-slate-900 mb-4">
            Catalogue de{" "}
            <span className="bg-gradient-to-r from-[#3898FF] to-[#8A78F2] bg-clip-text text-transparent">
              Recettes
            </span>
          </h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Choisissez parmi nos recettes d'automatisation intelligente pour vos tâches métier
          </p>
        </div>

        {/* Loading state */}
        {isLoadingRecipes && (
          <div className="flex items-center justify-center py-16">
            <div className="text-center space-y-4">
              <Loader2 className="h-8 w-8 animate-spin text-[#3898FF] mx-auto" />
              <p className="text-slate-600">Chargement des recettes...</p>
            </div>
          </div>
        )}

        {/* Error state */}
        {recipesError && (
          <div className="max-w-md mx-auto">
            <Card className="p-6 border-red-200 bg-red-50">
              <div className="flex items-center gap-3 text-red-700">
                <AlertCircle className="h-5 w-5" />
                <div>
                  <h3 className="font-medium">Erreur de chargement</h3>
                  <p className="text-sm text-red-600 mt-1">{recipesError}</p>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Recipes grid */}
        {!isLoadingRecipes && !recipesError && (
          <>
            {recipes.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
                {recipes.map((recipe) => (
                  <RecipeCard key={recipe.id} recipe={recipe} />
                ))}
              </div>
            ) : (
              <div className="text-center py-16">
                <div className="max-w-md mx-auto">
                  <Card className="p-8 border-slate-200">
                    <Wind className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-slate-900 mb-2">
                      Aucune recette disponible
                    </h3>
                    <p className="text-slate-600">
                      Les recettes d'automatisation seront bientôt disponibles.
                    </p>
                  </Card>
                </div>
              </div>
            )}
          </>
        )}

        {/* Footer info */}
        <div className="text-center mt-16 pt-8 border-t border-slate-200">
          <p className="text-sm text-slate-500">
            Chaque recette est un workflow intelligent qui s'adapte à vos besoins
          </p>
        </div>
      </div>
    </div>
  );
}