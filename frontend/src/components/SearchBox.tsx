"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Send, Loader2, Mic } from "lucide-react";
import { cn, isShortcut } from "@/lib/utils";
import { useSuggestions } from "@/hooks/useSuggestions";
import { AutocompleteSuggestions } from "@/components/AutocompleteSuggestions";

interface SearchBoxProps {
  onSubmit: (question: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  className?: string;
}

export function SearchBox({
  onSubmit,
  isLoading = false,
  placeholder = "Posez votre question sur vos documents...",
  className,
}: SearchBoxProps) {
  const [question, setQuestion] = React.useState("");
  const [isListening, setIsListening] = React.useState(false);
  const [showSuggestions, setShowSuggestions] = React.useState(false);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const recognitionRef = React.useRef<SpeechRecognition | null>(null);

  // Hook pour récupérer les suggestions intelligentes
  const { data: suggestions = [], isLoading: suggestionsLoading } = useSuggestions(question, showSuggestions);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim() && !isLoading) {
      onSubmit(question.trim());
      setQuestion("");
      setShowSuggestions(false);
    }
  };

  const handleSuggestionSelect = (suggestion: string) => {
    setQuestion(suggestion);
    setShowSuggestions(false);
    onSubmit(suggestion);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Submit on Enter (simple or with modifiers)
    if (e.key === "Enter") {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  };

  React.useEffect(() => {
    adjustTextareaHeight();
  }, [question]);

  // Initialize speech recognition
  React.useEffect(() => {
    if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'fr-FR';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setQuestion(prev => prev + (prev ? ' ' : '') + transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const toggleVoiceRecording = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const canSubmit = question.trim().length > 0 && !isLoading;

  return (
    <div className="relative">
      <Card className={cn("glass border-primary/10 backdrop-blur-xl shadow-2xl", className)} data-testid="search-box">
        <form onSubmit={handleSubmit} className="p-4">
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <Textarea
                ref={textareaRef}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)} // Délai pour permettre le clic sur les suggestions
                placeholder={placeholder}
                disabled={isLoading}
                className="min-h-[60px] max-h-[200px] resize-none text-base border-slate-200 focus:border-teal-400 focus:ring-2 focus:ring-teal-100 bg-background/50 backdrop-blur-sm outline-none transition-colors"
                aria-label="Question à poser"
                data-testid="search-input"
              />
            </div>
            <div className="flex gap-2">
              <Button
                type="button"
                onClick={toggleVoiceRecording}
                disabled={isLoading}
                className={`shrink-0 h-10 w-10 rounded-full p-0 flex items-center justify-center disabled:opacity-50 ${
                  isListening
                    ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
                    : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
                }`}
                data-testid="voice-button"
              >
                <Mic className="h-4 w-4" />
              </Button>
              <Button
                type="submit"
                disabled={!canSubmit}
                className="shrink-0 h-10 w-10 rounded-full bg-teal-600 hover:bg-teal-700 text-white p-0 flex items-center justify-center disabled:opacity-50"
                data-testid="search-button"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </form>
      </Card>

      {/* Autocomplétion intelligente */}
      <AutocompleteSuggestions
        suggestions={suggestions}
        isLoading={suggestionsLoading}
        onSelect={handleSuggestionSelect}
        visible={showSuggestions && question.length >= 2}
      />
    </div>
  );
}

// Quick suggestions component
interface SearchSuggestionsProps {
  suggestions: string[];
  onSelect: (suggestion: string) => void;
  className?: string;
}

export function SearchSuggestions({
  suggestions,
  onSelect,
  className,
}: SearchSuggestionsProps) {
  if (suggestions.length === 0) {
    return null;
  }

  return (
    <div className={cn("space-y-2", className)} data-testid="search-suggestions">
      <h3 className="text-sm font-medium text-muted-foreground">
        Suggestions de recherche :
      </h3>
      <div className="grid gap-2 sm:grid-cols-2">
        {suggestions.map((suggestion, index) => (
          <Button
            key={index}
            variant="outline"
            size="sm"
            onClick={() => onSelect(suggestion)}
            className="h-auto p-3 text-left justify-start whitespace-normal"
            data-testid={`suggestion-${index}`}
          >
            {suggestion}
          </Button>
        ))}
      </div>
    </div>
  );
}

// Recent searches component
interface RecentSearchesProps {
  searches: Array<{ question: string; timestamp: string }>;
  onSelect: (question: string) => void;
  onClear: () => void;
  className?: string;
}

export function RecentSearches({
  searches,
  onSelect,
  onClear,
  className,
}: RecentSearchesProps) {
  if (searches.length === 0) {
    return null;
  }

  return (
    <div className={cn("space-y-2", className)} data-testid="recent-searches">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted-foreground">
          Recherches récentes :
        </h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClear}
          className="h-6 px-2 text-xs"
          data-testid="clear-recent-searches"
        >
          Effacer
        </Button>
      </div>
      
      <div className="space-y-1">
        {searches.slice(0, 5).map((search, index) => (
          <Button
            key={index}
            variant="ghost"
            size="sm"
            onClick={() => onSelect(search.question)}
            className="h-auto p-2 text-left justify-start whitespace-normal w-full"
            data-testid={`recent-search-${index}`}
          >
            <div className="truncate text-sm">{search.question}</div>
          </Button>
        ))}
      </div>
    </div>
  );
}