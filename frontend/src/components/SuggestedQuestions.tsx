"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface SuggestedQuestionsProps {
  questions: string[];
  onSelect: (question: string) => void;
  isLoading?: boolean;
  className?: string;
}

export function SuggestedQuestions({
  questions,
  onSelect,
  isLoading = false,
  className,
}: SuggestedQuestionsProps) {
  if (!questions || questions.length === 0) {
    return null;
  }

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Sparkles className="w-4 h-4 text-teal-600" />
        <span className="font-medium">Questions suggérées</span>
      </div>

      <div className="grid gap-2">
        {questions.map((question, index) => (
          <Button
            key={index}
            variant="outline"
            disabled={isLoading}
            onClick={() => onSelect(question)}
            className="group h-auto p-4 justify-between text-left hover:bg-teal-50 hover:border-teal-300 transition-all"
          >
            <span className="flex-1 text-sm text-slate-700 group-hover:text-slate-900">
              {question}
            </span>
            <ArrowRight className="w-4 h-4 ml-3 text-slate-400 group-hover:text-teal-600 group-hover:translate-x-1 transition-all" />
          </Button>
        ))}
      </div>
    </div>
  );
}