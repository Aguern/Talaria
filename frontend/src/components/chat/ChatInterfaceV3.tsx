"use client";

import React, { useState, useRef, useEffect } from 'react';
import { MessageList } from './MessageList';
import { SearchBoxV2 } from '@/components/SearchBoxV2';
import { useChatStore } from '@/lib/stores/chat.store';
import { useMCPStore } from '@/lib/stores/mcp.store';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Layers, Wind, ArrowRight, MessageSquarePlus, FileText, Zap } from 'lucide-react';

interface ChatInterfaceV3Props {
  conversationId?: string;
  className?: string;
}

export function ChatInterfaceV3({ conversationId, className }: ChatInterfaceV3Props) {
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

  const handleSendMessage = async (content: string, attachments?: File[]) => {
    if (!content.trim() && (!attachments || attachments.length === 0)) return;

    await sendMessage({
      content,
      attachments: attachments || [],
      activeRecipes,
      conversationId: conversationId || activeConversation
    });
  };

  const hasMessages = messages.length > 0;

  const quickActions = [
    {
      icon: FileText,
      title: "Formulaire 3916",
      description: "Déclarer un compte bancaire étranger",
      action: "J'ai besoin d'aide avec le formulaire 3916",
      gradient: "from-blue-500 to-cyan-500"
    },
    {
      icon: Zap,
      title: "Actualités fiscales",
      description: "Dernières mises à jour BOFIP",
      action: "Quelles sont les dernières actualités fiscales ?",
      gradient: "from-amber-500 to-orange-500"
    },
    {
      icon: MessageSquarePlus,
      title: "Assistance générale",
      description: "Posez vos questions administratives",
      action: "J'ai une question sur mes obligations fiscales",
      gradient: "from-purple-500 to-pink-500"
    }
  ];

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Messages area */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto"
      >
        {!hasMessages ? (
          // Welcome screen with modern design
          <div className="flex flex-col items-center justify-center min-h-[80vh] px-4">
            <div className="max-w-4xl w-full space-y-8">
              {/* Welcome Header */}
              <div className="text-center space-y-4">
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-[#3898FF] to-[#8A78F2] shadow-2xl mb-4">
                  <Wind className="h-10 w-10 text-white" />
                </div>
                <h1 className="text-5xl font-bold text-slate-900">
                  Bienvenue sur{" "}
                  <span className="bg-gradient-to-r from-[#3898FF] to-[#8A78F2] bg-clip-text text-transparent">
                    Talaria
                  </span>
                </h1>
                <p className="text-xl text-slate-600 max-w-2xl mx-auto">
                  Orchestrez des workflows intelligents avec des recettes d'automatisation sur mesure
                </p>
              </div>

              {/* Active Recipes Badge */}
              {activeRecipes.length > 0 && (
                <div className="flex justify-center">
                  <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-[#8A78F2]/10 to-[#F178B6]/10 border border-[#8A78F2]/20">
                    <Layers className="h-5 w-5 text-[#8A78F2]" />
                    <span className="text-sm font-medium text-slate-700">
                      {activeRecipes.length} recette{activeRecipes.length > 1 ? 's' : ''} active{activeRecipes.length > 1 ? 's' : ''}
                    </span>
                    <div className="flex gap-1">
                      {activeRecipes.map(recipe => (
                        <Badge
                          key={recipe}
                          className="text-xs bg-gradient-to-r from-[#8A78F2] to-[#F178B6] text-white border-0"
                        >
                          {recipe}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Quick Actions */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                {quickActions.map((action, index) => {
                  const Icon = action.icon;
                  return (
                    <Card
                      key={index}
                      className="p-6 cursor-pointer hover:shadow-xl transition-all duration-300 border-slate-200 hover:border-slate-300 bg-white/80 backdrop-blur group"
                      onClick={() => handleSendMessage(action.action, [])}
                    >
                      <div className="space-y-3">
                        <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${action.gradient} shadow-lg`}>
                          <Icon className="h-6 w-6 text-white" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-900 mb-1">{action.title}</h3>
                          <p className="text-sm text-slate-600">{action.description}</p>
                        </div>
                        <div className="flex items-center text-[#3898FF] opacity-0 group-hover:opacity-100 transition-opacity">
                          <span className="text-sm font-medium">Commencer</span>
                          <ArrowRight className="h-4 w-4 ml-1" />
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </div>

              {/* Capabilities */}
              <div className="text-center space-y-3 mt-12">
                <p className="text-sm text-slate-500">
                  Posez-moi une question ou choisissez une action ci-dessus pour commencer
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {['Analyse de documents', 'Remplissage de formulaires', 'Conseils personnalisés', 'Veille réglementaire'].map((capability) => (
                    <Badge
                      key={capability}
                      variant="secondary"
                      className="text-xs px-3 py-1 bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
                    >
                      {capability}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          // Messages list with modern styling
          <div className="max-w-4xl mx-auto px-4 py-6">
            <MessageList
              messages={messages}
              isLoading={isLoading}
            />
          </div>
        )}
      </div>

      {/* Input area with SearchBox */}
      <div className="border-t bg-white/90 backdrop-blur-sm shadow-lg">
        <div className="max-w-4xl mx-auto p-4">
          {/* Active recipes indicator */}
          {activeRecipes.length > 0 && (
            <div className="mb-3 flex items-center gap-2 text-sm">
              <Layers className="h-4 w-4 text-[#8A78F2]" />
              <span className="text-slate-600">Recettes actives :</span>
              <div className="flex gap-1">
                {activeRecipes.map(recipe => (
                  <Badge
                    key={recipe}
                    variant="secondary"
                    className="text-xs bg-gradient-to-r from-[#8A78F2] to-[#F178B6] text-white border-0"
                  >
                    {recipe}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <SearchBoxV2
            onSubmit={handleSendMessage}
            isLoading={isLoading}
            placeholder={
              activeRecipes.length > 0
                ? "Posez votre question..."
                : "Posez votre question ou activez une recette..."
            }
            showAttachments={true}
          />
        </div>
      </div>
    </div>
  );
}