"use client";

import React, { useState, useRef, useEffect } from 'react';
import { MessageList } from './MessageList';
import { InputAreaV2 } from './InputAreaV2';
import { useChatStore } from '@/lib/stores/chat.store';
import { useMCPStore } from '@/lib/stores/mcp.store';
import { cn } from '@/lib/utils';
import { Layers, ArrowRight } from 'lucide-react';

interface ChatInterfaceV2Props {
  conversationId?: string;
  className?: string;
}

export function ChatInterfaceV2({ conversationId, className }: ChatInterfaceV2Props) {
  const [attachments, setAttachments] = useState<File[]>([]);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const {
    messages,
    isLoading,
    sendMessage,
    activeConversation
  } = useChatStore();

  const { activeRecipes } = useMCPStore();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim() && attachments.length === 0) return;

    await sendMessage({
      content,
      attachments,
      activeRecipes,
      conversationId: conversationId || activeConversation
    });

    // Clear attachments after sending
    setAttachments([]);
  };

  const handleFileDrop = (files: File[]) => {
    setAttachments(prev => [...prev, ...files]);
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const hasMessages = messages.length > 0;

  return (
    <div className={cn("flex flex-col h-full bg-[#FFFFFF]", className)}>
      {/* Messages area */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto"
      >
        <div className="max-w-4xl mx-auto">
          {!hasMessages ? (
            // Welcome screen
            <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
              <div className="mb-8">
                <h1 className="text-4xl font-bold text-center text-[#1D2B48] mb-2">
                  Bienvenue sur Talaria
                </h1>
                <p className="text-lg text-[#1D2B48]/70 text-center max-w-md">
                  Votre assistant intelligent pour les démarches administratives et fiscales
                </p>
              </div>

              {activeRecipes.length > 0 ? (
                <div className="flex items-center gap-2 mb-6 px-4 py-2 rounded-full bg-gradient-to-r from-[#8A78F2] to-[#F178B6]">
                  <Layers className="h-5 w-5 text-white" />
                  <span className="text-sm font-medium text-white">
                    {activeRecipes.length} recette{activeRecipes.length > 1 ? 's' : ''} active{activeRecipes.length > 1 ? 's' : ''}
                  </span>
                </div>
              ) : (
                <p className="text-sm text-[#1D2B48]/60 text-center max-w-md mb-8">
                  Activez une recette dans la barre latérale pour débloquer des fonctionnalités spécifiques
                </p>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4 w-full max-w-lg">
                <button
                  onClick={() => handleSendMessage("J'ai besoin d'aide avec le formulaire 3916")}
                  className="text-left p-4 rounded-xl border border-[#3898FF]/20 hover:bg-[#3898FF]/5 hover:border-[#3898FF]/40 transition-all group"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-medium text-sm text-[#1D2B48] mb-1">Formulaire 3916</div>
                      <div className="text-xs text-[#1D2B48]/60">
                        Déclarer un compte bancaire étranger
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-[#3898FF] opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </button>

                <button
                  onClick={() => handleSendMessage("Comment remplir ma déclaration d'impôts ?")}
                  className="text-left p-4 rounded-xl border border-[#3898FF]/20 hover:bg-[#3898FF]/5 hover:border-[#3898FF]/40 transition-all group"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-medium text-sm text-[#1D2B48] mb-1">Déclaration IR</div>
                      <div className="text-xs text-[#1D2B48]/60">
                        Aide pour votre déclaration de revenus
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-[#3898FF] opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </button>

                <button
                  onClick={() => handleSendMessage("Quelles sont les dernières actualités fiscales ?")}
                  className="text-left p-4 rounded-xl border border-[#3898FF]/20 hover:bg-[#3898FF]/5 hover:border-[#3898FF]/40 transition-all group"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-medium text-sm text-[#1D2B48] mb-1">Actualités BOFIP</div>
                      <div className="text-xs text-[#1D2B48]/60">
                        Dernières mises à jour fiscales
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-[#3898FF] opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </button>

                <button
                  onClick={() => handleSendMessage("J'ai une question sur mes obligations fiscales")}
                  className="text-left p-4 rounded-xl border border-[#3898FF]/20 hover:bg-[#3898FF]/5 hover:border-[#3898FF]/40 transition-all group"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-medium text-sm text-[#1D2B48] mb-1">Conseil fiscal</div>
                      <div className="text-xs text-[#1D2B48]/60">
                        Posez vos questions fiscales
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-[#3898FF] opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </button>
              </div>
            </div>
          ) : (
            // Messages list
            <div className="px-4 py-6">
              <MessageList
                messages={messages}
                isLoading={isLoading}
              />
            </div>
          )}
        </div>
      </div>

      {/* Input area */}
      <div className="border-t border-[#F3F5F9] bg-white">
        <div className="max-w-4xl mx-auto p-4">
          <InputAreaV2
            onSend={handleSendMessage}
            onFileDrop={handleFileDrop}
            attachments={attachments}
            onRemoveAttachment={removeAttachment}
            disabled={isLoading}
            isLoading={isLoading}
            activeRecipes={activeRecipes}
            placeholder={
              activeRecipes.length > 0
                ? "Posez votre question..."
                : "Posez votre question ou activez une recette..."
            }
          />
        </div>
      </div>
    </div>
  );
}