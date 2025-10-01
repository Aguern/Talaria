"use client";

import React from 'react';
import { useMCPStore } from '@/lib/stores/mcp.store';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import {
  FileText,
  Database,
  Shield,
  Zap,
  Circle,
  CheckCircle,
  XCircle,
  Loader2
} from 'lucide-react';

interface RecipeListProps {
  className?: string;
}

export function RecipeList({ className }: RecipeListProps) {
  const {
    availableRecipes,
    activeRecipes,
    toggleRecipe
  } = useMCPStore();

  const getIcon = (category: string) => {
    switch (category) {
      case 'fiscal':
        return FileText;
      case 'legal':
        return Shield;
      case 'analysis':
        return Database;
      default:
        return Zap;
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="h-3 w-3 text-green-500" />;
      case 'connecting':
        return <Loader2 className="h-3 w-3 animate-spin text-blue-500" />;
      case 'error':
        return <XCircle className="h-3 w-3 text-red-500" />;
      default:
        return <Circle className="h-3 w-3 text-muted-foreground" />;
    }
  };

  return (
    <div className={cn("space-y-2", className)}>
      <div className="px-3 py-2">
        <h3 className="text-sm font-medium text-muted-foreground mb-3">
          Recettes disponibles
        </h3>

        <div className="space-y-2">
          {availableRecipes.map((recipe) => {
            const Icon = getIcon(recipe.category);
            const isActive = activeRecipes.includes(recipe.id);

            return (
              <div
                key={recipe.id}
                className={cn(
                  "p-3 rounded-lg border transition-colors",
                  isActive ? "bg-primary/5 border-primary/20" : "hover:bg-muted/50"
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium text-sm">{recipe.name}</span>
                      {getStatusIcon(recipe.status)}
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">
                      {recipe.description}
                    </p>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>{recipe.tools?.length || 0} outils</span>
                      <Badge variant="outline" className="text-xs">
                        {recipe.category}
                      </Badge>
                    </div>
                  </div>

                  <Switch
                    checked={isActive}
                    onCheckedChange={async () => {
                      try {
                        await toggleRecipe(recipe.id);
                      } catch (error) {
                        console.error('Error toggling recipe:', error);
                      }
                    }}
                    disabled={!recipe.available}
                  />
                </div>

                {/* Show tools when active */}
                {isActive && recipe.tools && recipe.tools.length > 0 && (
                  <div className="mt-3 pt-3 border-t">
                    <div className="space-y-1">
                      {recipe.tools.map((tool, index) => (
                        <div
                          key={index}
                          className="flex items-center gap-2 text-xs text-muted-foreground"
                        >
                          <span className="w-1.5 h-1.5 bg-primary rounded-full" />
                          {tool.description || tool.name || 'Outil'}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {availableRecipes.length === 0 && (
          <div className="text-center py-8 text-muted-foreground text-sm">
            Aucune recette disponible
          </div>
        )}
      </div>
    </div>
  );
}