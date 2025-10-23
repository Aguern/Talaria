"use client";

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { useRecipesStore } from '@/lib/stores/recipes.store';
import { recipesAPI } from '@/lib/api/recipes';
import { StatusIndicator } from '@/components/tasks/StatusIndicator';
import { ConversationThread } from '@/components/tasks/ConversationThread';
import { ResultsDisplay } from '@/components/tasks/ResultsDisplay';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  ArrowLeft,
  RefreshCw,
  AlertCircle,
  Home,
  Loader2
} from 'lucide-react';
import type { TaskStatusResponse } from '@/lib/types/recipes';

export default function TaskExecutionPage() {
  const params = useParams();
  const router = useRouter();
  const auth = useAuth();
  const { startTaskPolling, stopTaskPolling, getTaskStatus } = useRecipesStore();

  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmittingResponse, setIsSubmittingResponse] = useState(false);
  const [responseError, setResponseError] = useState<string | null>(null);

  const taskId = params.taskId as string;

  // Redirect if not authenticated
  useEffect(() => {
    if (!auth.isAuthenticated) {
      router.replace('/');
      return;
    }
  }, [auth.isAuthenticated, router]);

  // Start polling when component mounts
  useEffect(() => {
    if (!taskId || !auth.isAuthenticated) return;

    const startPolling = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Check if we already have status in store
        const existingStatus = getTaskStatus(taskId);
        if (existingStatus) {
          setTaskStatus(existingStatus);
          setIsLoading(false);
        }

        // Start polling for updates
        await startTaskPolling(taskId, (status) => {
          setTaskStatus(status);
          setIsLoading(false);
        });

      } catch (error) {
        console.error('Failed to start task polling:', error);
        setError(
          error instanceof Error
            ? error.message
            : 'Erreur lors du chargement de la tâche'
        );
        setIsLoading(false);
      }
    };

    startPolling();

    // Cleanup polling on unmount
    return () => {
      stopTaskPolling(taskId);
    };
  }, [taskId, auth.isAuthenticated, startTaskPolling, stopTaskPolling, getTaskStatus]);

  const handleRefresh = async () => {
    if (!taskId) return;

    setIsLoading(true);
    setError(null);

    try {
      const status = await recipesAPI.getTaskStatus(taskId);
      setTaskStatus(status);
    } catch (error) {
      console.error('Refresh error:', error);
      setError(
        error instanceof Error
          ? error.message
          : 'Erreur lors de l\'actualisation'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitResponse = async (
    response: string | Record<string, any>,
    files?: File[]
  ) => {
    if (!taskId) return;

    setIsSubmittingResponse(true);
    setResponseError(null);

    try {
      console.log('Submitting response:', { response, files: files?.length });

      await recipesAPI.resumeTask(taskId, {
        response,
        files
      });

      // The polling will automatically pick up the status change
      // Reset the conversation state will be handled by new status

    } catch (error) {
      console.error('Error submitting response:', error);
      setResponseError(
        error instanceof Error
          ? error.message
          : 'Erreur lors de l\'envoi de la réponse'
      );
    } finally {
      setIsSubmittingResponse(false);
    }
  };

  const handleGoHome = () => {
    router.push('/');
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
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              onClick={handleGoBack}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Retour
            </Button>
            <div className="h-6 border-l border-slate-300" />
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                Suivi d'exécution
              </h1>
              <p className="text-slate-600 text-sm">
                ID: {taskId}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={isLoading}
              size="sm"
            >
              <RefreshCw className={`h-4 w-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
              Actualiser
            </Button>
            <Button
              variant="outline"
              onClick={handleGoHome}
              size="sm"
            >
              <Home className="h-4 w-4 mr-1" />
              Accueil
            </Button>
          </div>
        </div>

        <div className="max-w-4xl mx-auto">
          {/* Loading state */}
          {isLoading && !taskStatus && (
            <Card className="p-8">
              <div className="text-center space-y-4">
                <Loader2 className="h-8 w-8 animate-spin text-[#3898FF] mx-auto" />
                <p className="text-slate-600">Chargement du statut de la tâche...</p>
              </div>
            </Card>
          )}

          {/* Error state */}
          {error && (
            <Card className="p-6 border-red-200 bg-red-50">
              <div className="flex items-center gap-3 text-red-700">
                <AlertCircle className="h-5 w-5" />
                <div>
                  <h3 className="font-medium">Erreur de chargement</h3>
                  <p className="text-sm text-red-600 mt-1">{error}</p>
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                <Button onClick={handleRefresh} variant="outline" size="sm">
                  Réessayer
                </Button>
                <Button onClick={handleGoHome} variant="outline" size="sm">
                  Retour à l'accueil
                </Button>
              </div>
            </Card>
          )}

          {/* Task status and content */}
          {taskStatus && !error && (
            <div className="space-y-6">
              {/* Recipe info */}
              <Card className="p-4 bg-slate-50 border-slate-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-slate-900">
                      {taskStatus.recipe_id}
                    </h3>
                    <p className="text-sm text-slate-600">
                      Tâche créée le {new Date().toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-slate-500">Statut</div>
                    <div className="font-medium text-slate-900">
                      {taskStatus.status}
                    </div>
                  </div>
                </div>
              </Card>

              {/* Status indicator */}
              <StatusIndicator
                status={taskStatus.status}
                progress={taskStatus.progress}
                currentStep={taskStatus.current_step}
                message={taskStatus.message}
              />

              {/* State-based content */}
              {taskStatus.status === 'waiting_for_human_input' && taskStatus.human_input_request && (
                <ConversationThread
                  messages={taskStatus.conversation_history || []}
                  humanInputRequest={taskStatus.human_input_request}
                  onSubmitResponse={handleSubmitResponse}
                  loading={isSubmittingResponse}
                  error={responseError}
                />
              )}

              {taskStatus.status === 'completed' && taskStatus.result && (
                <ResultsDisplay
                  taskId={taskId}
                  results={taskStatus.result}
                />
              )}

              {taskStatus.status === 'error' && (
                <Card className="p-6 border-red-200 bg-red-50">
                  <div className="flex items-center gap-3 text-red-700">
                    <AlertCircle className="h-5 w-5" />
                    <div>
                      <h3 className="font-medium">Erreur d'exécution</h3>
                      <p className="text-sm text-red-600 mt-1">
                        {taskStatus.error || 'Une erreur s\'est produite lors de l\'exécution'}
                      </p>
                      {taskStatus.error_type && (
                        <p className="text-xs text-red-500 mt-1">
                          Type: {taskStatus.error_type}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="mt-4">
                    <Button onClick={handleGoHome} variant="outline" size="sm">
                      Retour à l'accueil
                    </Button>
                  </div>
                </Card>
              )}

              {/* Help section for waiting states */}
              {(taskStatus.status === 'pending' || taskStatus.status === 'running') && (
                <Card className="p-4 bg-blue-50 border-blue-200">
                  <div className="text-center">
                    <p className="text-blue-800 text-sm">
                      💡 Cette page se met à jour automatiquement toutes les 2 secondes.
                      Vous pouvez fermer cet onglet et revenir plus tard.
                    </p>
                  </div>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}