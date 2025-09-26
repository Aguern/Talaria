// Fichier: frontend/src/components/InteractiveAnswer.tsx
"use client";

import React from "react";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { Citation } from "@/lib/types";
import { ExternalLink, FileText } from "lucide-react";
import { Button } from "./ui/button";

interface InteractiveAnswerProps {
  answer: string;
  citations: Citation[];
}

export function InteractiveAnswer({ answer, citations }: InteractiveAnswerProps) {
  // Fonction pour parser la réponse et insérer les popovers
  const renderAnswerWithCitations = () => {
    // Sépare le texte par les marqueurs de citation (ex: [1], [2])
    const parts = answer.split(/(\[\d+\])/g);

    return parts.map((part, index) => {
      // Vérifie si la partie est un marqueur de citation
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        const citationIndex = parseInt(match[1], 10) - 1;
        const citation = citations[citationIndex];

        if (citation) {
          return (
            <HoverCard key={index} openDelay={100} closeDelay={100}>
              <HoverCardTrigger asChild>
                <span className="inline-block align-super text-xs font-bold text-teal-600 bg-teal-50 rounded-full px-1.5 py-0.5 mx-0.5 cursor-pointer hover:bg-teal-100 transition-colors border border-teal-200">
                  {match[1]}
                </span>
              </HoverCardTrigger>
              <HoverCardContent className="w-96 shadow-xl border-slate-200 bg-white" side="top" align="center">
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <div className="flex-shrink-0 h-6 w-6 rounded-md bg-teal-100 text-teal-700 flex items-center justify-center text-xs font-bold">
                      {match[1]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-slate-900 truncate">
                        {citation.source || `Document ${citation.doc_id}`}
                      </p>
                      {citation.doc_type && (
                        <p className="text-xs text-slate-500">
                          {citation.doc_type}
                        </p>
                      )}
                    </div>
                    <FileText className="w-4 h-4 text-slate-400" />
                  </div>

                  {citation.excerpt && (
                    <div className="bg-slate-50 border-l-3 border-l-teal-500 p-3 rounded-r-lg">
                      <p className="text-sm text-slate-700 leading-relaxed italic">
                        "{citation.excerpt.length > 250 ? citation.excerpt.substring(0, 250) + '...' : citation.excerpt}"
                      </p>
                    </div>
                  )}

                  {citation.source && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full text-xs"
                      asChild
                    >
                      <a
                        href={`https://bofip.impots.gouv.fr/bofip/${citation.source}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <ExternalLink className="mr-2 h-3 w-3" />
                        Consulter sur BOFIP
                      </a>
                    </Button>
                  )}
                </div>
              </HoverCardContent>
            </HoverCard>
          );
        }
      }
      // Si ce n'est pas un marqueur, on affiche juste le texte
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div className="prose prose-sm max-w-none">
      <div className="whitespace-pre-wrap text-slate-700 leading-relaxed">
        {renderAnswerWithCitations()}
      </div>
    </div>
  );
}