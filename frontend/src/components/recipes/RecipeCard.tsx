"use client";

import React from 'react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  FileText,
  MessageSquare,
  ArrowRight,
  Layers,
  Zap,
  Shield,
  Database
} from 'lucide-react';
import type { RecipeManifest } from '@/lib/types/recipes';

interface RecipeCardProps {
  recipe: RecipeManifest;
  className?: string;
}

export function RecipeCard({ recipe, className }: RecipeCardProps) {
  const router = useRouter();

  const getCategoryIcon = (category?: string) => {
    switch (category) {
      case 'fiscal':
        return FileText;
      case 'legal':
        return Shield;
      case 'analysis':
        return Database;
      default:
        return Layers;
    }
  };

  const getCategoryColor = (category?: string) => {
    switch (category) {
      case 'fiscal':
        return 'from-blue-500 to-cyan-500';
      case 'legal':
        return 'from-purple-500 to-indigo-500';
      case 'analysis':
        return 'from-green-500 to-emerald-500';
      default:
        return 'from-slate-500 to-gray-500';
    }
  };

  const isConversational = recipe.interaction_mode === 'conversational';
  const Icon = getCategoryIcon(recipe.category);

  const handleClick = () => {
    router.push(`/recipes/${recipe.id}`);
  };

  return (
    <Card
      className={cn(
        "relative overflow-hidden cursor-pointer transition-all duration-300",
        "hover:shadow-xl hover:shadow-blue-500/10 hover:-translate-y-1",
        "border-slate-200 hover:border-slate-300 bg-white/80 backdrop-blur",
        "group",
        className
      )}
      onClick={handleClick}
    >
      {/* Background gradient overlay */}
      <div className={cn(
        "absolute inset-0 opacity-0 group-hover:opacity-5 transition-opacity",
        "bg-gradient-to-br",
        getCategoryColor(recipe.category)
      )} />

      <div className="relative p-6 space-y-4">
        {/* Header with icon and badges */}
        <div className="flex items-start justify-between">
          <div className={cn(
            "inline-flex p-3 rounded-xl shadow-lg",
            "bg-gradient-to-br",
            getCategoryColor(recipe.category)
          )}>
            <Icon className="h-6 w-6 text-white" />
          </div>

          <div className="flex flex-col gap-2">
            {recipe.category && (
              <Badge variant="secondary" className="text-xs">
                {recipe.category}
              </Badge>
            )}
            {isConversational && (
              <Badge className="text-xs bg-gradient-to-r from-amber-500 to-orange-500 text-white border-0">
                <MessageSquare className="h-3 w-3 mr-1" />
                Conversationnel
              </Badge>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="space-y-3">
          <h3 className="font-semibold text-lg text-slate-900 group-hover:text-slate-700 transition-colors">
            {recipe.name}
          </h3>

          <p className="text-sm text-slate-600 line-clamp-3 leading-relaxed">
            {recipe.description}
          </p>

          {/* Metadata */}
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <Layers className="h-3 w-3" />
              {recipe.inputs?.length || 0} inputs
            </span>
            <span className="flex items-center gap-1">
              <Zap className="h-3 w-3" />
              {recipe.outputs?.length || 0} outputs
            </span>
            {recipe.version && (
              <span>v{recipe.version}</span>
            )}
          </div>

          {/* Tags */}
          {recipe.tags && recipe.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {recipe.tags.slice(0, 3).map((tag) => (
                <Badge
                  key={tag}
                  variant="outline"
                  className="text-xs px-2 py-0.5 bg-slate-50 text-slate-600 border-slate-200"
                >
                  {tag}
                </Badge>
              ))}
              {recipe.tags.length > 3 && (
                <Badge
                  variant="outline"
                  className="text-xs px-2 py-0.5 bg-slate-50 text-slate-600 border-slate-200"
                >
                  +{recipe.tags.length - 3}
                </Badge>
              )}
            </div>
          )}
        </div>

        {/* Call to action */}
        <div className="pt-2">
          <Button
            variant="ghost"
            className="w-full justify-between group-hover:bg-slate-100 transition-colors"
            size="sm"
          >
            <span className="font-medium">Lancer la recette</span>
            <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
          </Button>
        </div>
      </div>
    </Card>
  );
}