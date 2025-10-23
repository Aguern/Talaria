"use client";

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { useRecipesStore } from '@/lib/stores/recipes.store';
import { recipesAPI } from '@/lib/api/recipes';
import { DynamicForm } from '@/components/forms/DynamicForm';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, ArrowLeft, AlertCircle, FileText, MessageSquare } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function RecipeLaunchPage() {
  const params = useParams();
  const router = useRouter();
  const auth = useAuth();
  const { currentRecipe, isLoadingRecipe, recipeError, loadRecipe, clearCurrentRecipe } = useRecipesStore();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const recipeId = params.recipeId as string;

  // Redirect if not authenticated
  useEffect(() => {
    if (!auth.isAuthenticated) {
      router.replace('/');
      return;
    }
  }, [auth.isAuthenticated, router]);

  // Load recipe on mount
  useEffect(() => {
    if (recipeId) {
      loadRecipe(recipeId);
    }

    return () => {
      clearCurrentRecipe();
    };
  }, [recipeId, loadRecipe, clearCurrentRecipe]);

  const handleSubmit = async (formData: FormData) => {
    if (!currentRecipe) return;

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Extract request data from FormData
      const requestDataString = formData.get('request') as string;
      const requestData = JSON.parse(requestDataString);

      // Extract files
      const files = formData.getAll('files') as File[];

      console.log('Submitting recipe:', {
        recipeId: currentRecipe.id,
        requestData,
        filesCount: files.length
      });

      const response = await recipesAPI.runRecipe(currentRecipe.id, requestData, files);

      console.log('Recipe execution started:', response);

      // Redirect to task monitoring page
      router.push(`/tasks/${response.task_id}`);

    } catch (error) {
      console.error('Recipe submission error:', error);
      setSubmitError(
        error instanceof Error
          ? error.message
          : 'Erreur lors du lancement de la recette'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoBack = () => {
    router.back();
  };

  // Show loading while checking auth
  if (!auth.isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header with back button */}
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="ghost"
            onClick={handleGoBack}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Retour
          </Button>
          <div className="h-6 border-l border-slate-300" />
          <h1 className="text-2xl font-bold text-slate-900">
            Lancement de recette
          </h1>
        </div>

        <div className="max-w-2xl mx-auto">
          {/* Loading state */}
          {isLoadingRecipe && (
            <Card className="p-8">
              <div className="text-center space-y-4">
                <Loader2 className="h-8 w-8 animate-spin text-[#3898FF] mx-auto" />
                <p className="text-slate-600">Chargement de la recette...</p>
              </div>
            </Card>
          )}

          {/* Error state */}
          {recipeError && (
            <Card className="p-6 border-red-200 bg-red-50">
              <div className="flex items-center gap-3 text-red-700">
                <AlertCircle className="h-5 w-5" />
                <div>
                  <h3 className="font-medium">Erreur de chargement</h3>
                  <p className="text-sm text-red-600 mt-1">{recipeError}</p>
                </div>
              </div>
              <div className="mt-4">
                <Button onClick={handleGoBack} variant="outline" size="sm">
                  Retour au catalogue
                </Button>
              </div>
            </Card>
          )}

          {/* Recipe info and form */}
          {currentRecipe && !isLoadingRecipe && (
            <div className="space-y-6">
              {/* Recipe info card */}
              <Card className="p-6">
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500">
                    <FileText className="h-6 w-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h2 className="text-xl font-semibold text-slate-900">
                        {currentRecipe.name}
                      </h2>
                      {currentRecipe.interaction_mode === 'conversational' && (
                        <Badge className="bg-gradient-to-r from-amber-500 to-orange-500 text-white border-0">
                          <MessageSquare className="h-3 w-3 mr-1" />
                          Conversationnel
                        </Badge>
                      )}
                    </div>
                    <p className="text-slate-600 mb-3">{currentRecipe.description}</p>

                    {currentRecipe.category && (
                      <Badge variant="secondary" className="text-xs">
                        {currentRecipe.category}
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Interaction mode info */}
                {currentRecipe.interaction_mode === 'conversational' && (
                  <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                    <div className="flex items-center gap-2 text-amber-800">
                      <MessageSquare className="h-4 w-4" />
                      <span className="font-medium">Mode conversationnel</span>
                    </div>
                    <p className="text-sm text-amber-700 mt-1">
                      Cette recette peut demander des clarifications pendant son exécution.
                      Vous serez notifié si une interaction est nécessaire.
                    </p>
                  </div>
                )}
              </Card>

              {/* Dynamic form */}
              <DynamicForm
                recipe={currentRecipe}
                onSubmit={handleSubmit}
                loading={isSubmitting}
                error={submitError}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}