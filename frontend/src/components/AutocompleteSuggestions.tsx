"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Search, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface AutocompleteSuggestionsProps {
  suggestions: string[];
  isLoading?: boolean;
  onSelect: (suggestion: string) => void;
  visible?: boolean;
  className?: string;
}

export function AutocompleteSuggestions({
  suggestions,
  isLoading,
  onSelect,
  visible = false,
  className,
}: AutocompleteSuggestionsProps) {
  if (!visible || (!suggestions.length && !isLoading)) {
    return null;
  }

  return (
    <Card className={cn(
      "absolute z-50 w-full mt-2 p-2 shadow-lg border-slate-200 bg-white",
      className
    )}>
      {isLoading ? (
        <div className="p-3 text-sm text-muted-foreground">
          Recherche de suggestions...
        </div>
      ) : (
        <div className="space-y-1">
          <div className="px-3 py-1.5 text-xs font-medium text-muted-foreground flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            Suggestions
          </div>
          {suggestions.map((suggestion, index) => (
            <Button
              key={index}
              variant="ghost"
              className="w-full justify-start text-left px-3 py-2 h-auto hover:bg-teal-50 hover:text-teal-900"
              onClick={() => onSelect(suggestion)}
            >
              <Search className="w-3.5 h-3.5 mr-2 text-slate-400" />
              <span className="text-sm">{suggestion}</span>
            </Button>
          ))}
        </div>
      )}
    </Card>
  );
}