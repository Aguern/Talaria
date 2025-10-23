"use client";

import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Progress } from '../ui/progress';
import {
  Loader2,
  Clock,
  Play,
  CheckCircle,
  XCircle,
  MessageSquare,
  Pause
} from 'lucide-react';
import type { TaskStatus } from '@/lib/types/recipes';

interface StatusIndicatorProps {
  status: TaskStatus;
  progress?: number;
  currentStep?: string;
  message?: string;
  className?: string;
}

export function StatusIndicator({
  status,
  progress = 0,
  currentStep,
  message,
  className
}: StatusIndicatorProps) {
  const getStatusConfig = (status: TaskStatus) => {
    switch (status) {
      case 'pending':
        return {
          icon: Clock,
          color: 'text-amber-600',
          bgColor: 'bg-amber-50',
          borderColor: 'border-amber-200',
          title: 'En attente',
          description: 'La tâche est en file d\'attente'
        };
      case 'running':
        return {
          icon: Loader2,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          title: 'En cours d\'exécution',
          description: 'La recette est en train de s\'exécuter'
        };
      case 'waiting_for_human_input':
        return {
          icon: MessageSquare,
          color: 'text-purple-600',
          bgColor: 'bg-purple-50',
          borderColor: 'border-purple-200',
          title: 'Interaction requise',
          description: 'La recette attend votre réponse'
        };
      case 'completed':
        return {
          icon: CheckCircle,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          title: 'Terminé',
          description: 'La recette s\'est exécutée avec succès'
        };
      case 'error':
        return {
          icon: XCircle,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          title: 'Erreur',
          description: 'Une erreur s\'est produite lors de l\'exécution'
        };
      default:
        return {
          icon: Pause,
          color: 'text-slate-600',
          bgColor: 'bg-slate-50',
          borderColor: 'border-slate-200',
          title: 'Statut inconnu',
          description: 'Statut de la tâche non déterminé'
        };
    }
  };

  const config = getStatusConfig(status);
  const Icon = config.icon;
  const isAnimated = status === 'running';

  return (
    <Card className={cn(
      "border-2",
      config.bgColor,
      config.borderColor,
      className
    )}>
      <div className="p-6">
        <div className="flex items-center gap-4">
          {/* Icon */}
          <div className={cn(
            "p-3 rounded-full",
            config.bgColor,
            "ring-1",
            config.borderColor
          )}>
            <Icon className={cn(
              "h-6 w-6",
              config.color,
              isAnimated && "animate-spin"
            )} />
          </div>

          {/* Status info */}
          <div className="flex-1">
            <h3 className={cn("font-semibold text-lg", config.color)}>
              {config.title}
            </h3>
            <p className="text-slate-600 text-sm">
              {config.description}
            </p>
          </div>
        </div>

        {/* Progress bar (for running tasks) */}
        {status === 'running' && progress > 0 && (
          <div className="mt-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">Progression</span>
              <span className={config.color}>{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        )}

        {/* Current step */}
        {currentStep && (
          <div className="mt-4 p-3 bg-white/60 rounded-lg border">
            <div className="flex items-center gap-2">
              <Play className="h-4 w-4 text-blue-500" />
              <span className="font-medium text-sm text-slate-900">
                Étape actuelle
              </span>
            </div>
            <p className="text-sm text-slate-700 mt-1">{currentStep}</p>
          </div>
        )}

        {/* Custom message */}
        {message && (
          <div className="mt-4 p-3 bg-white/60 rounded-lg border">
            <p className="text-sm text-slate-700">{message}</p>
          </div>
        )}

        {/* Loading dots for running status */}
        {status === 'running' && !currentStep && (
          <div className="mt-4 flex justify-center">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}