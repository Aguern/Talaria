"use client";

import React, { useState } from 'react';
import { ChatInterfaceV3 } from '@/components/chat/ChatInterfaceV3';
import { ConversationList } from '@/components/sidebar/ConversationList';
import { RecipeList } from '@/components/sidebar/RecipeList';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useMCPStore } from '@/lib/stores/mcp.store';
import {
  PanelLeftClose,
  PanelLeftOpen,
  LogOut,
  Settings,
  MessageSquare,
  Layers,
  User,
  Plus
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function ChatPage() {
  const router = useRouter();
  const auth = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<'conversations' | 'recipes'>('conversations');
  const { activeRecipes } = useMCPStore();

  React.useEffect(() => {
    if (!auth.isAuthenticated) {
      router.replace('/');
    }
  }, [auth.isAuthenticated, router]);

  const handleLogout = () => {
    auth.logout();
    router.push('/');
  };

  const startNewConversation = () => {
    // TODO: Implement new conversation logic
    window.location.reload();
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      {/* Background Elements for modern look */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 via-transparent to-purple-50/50 pointer-events-none"></div>
      <div className="absolute top-20 left-1/4 w-72 h-72 bg-blue-100/30 rounded-full blur-3xl opacity-60 pointer-events-none"></div>
      <div className="absolute bottom-20 right-1/3 w-96 h-96 bg-purple-100/30 rounded-full blur-3xl opacity-60 pointer-events-none"></div>

      {/* Sidebar */}
      <div
        className={cn(
          "relative z-10 border-r bg-white/80 backdrop-blur-xl flex flex-col transition-all duration-300 shadow-lg",
          sidebarOpen ? 'w-80' : 'w-16'
        )}
      >
        {/* Header */}
        <div className="p-3 border-b bg-white/90">
          {sidebarOpen ? (
            <div>
              <div className="flex items-center justify-between mb-4">
                <Button
                  onClick={startNewConversation}
                  className="flex-1 mr-2 bg-gradient-to-r from-[#3898FF] to-[#8A78F2] hover:opacity-90 text-white font-medium shadow-md transition-all"
                  size="sm"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Nouvelle conversation
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSidebarOpen(false)}
                  className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-2"
                >
                  <PanelLeftClose className="w-4 h-4" />
                </Button>
              </div>

              {/* Brand */}
              <div className="flex items-center justify-between px-2">
                <div className="flex items-center gap-2">
                  <div className="text-xl font-bold bg-gradient-to-r from-[#3898FF] to-[#8A78F2] bg-clip-text text-transparent">
                    Talaria
                  </div>
                  {activeRecipes.length > 0 && (
                    <Badge className="bg-gradient-to-r from-[#8A78F2] to-[#F178B6] text-white border-0 text-xs shadow-sm">
                      {activeRecipes.length}
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          ) : (
            // Version réduite
            <div className="space-y-3">
              <div className="flex flex-col items-center space-y-2">
                <Button
                  variant="ghost"
                  onClick={() => setSidebarOpen(true)}
                  className="w-10 h-10 p-0 text-slate-400 hover:text-slate-600 hover:bg-slate-100"
                  title="Ouvrir la barre latérale"
                >
                  <PanelLeftOpen className="w-5 h-5" />
                </Button>

                <Button
                  onClick={startNewConversation}
                  className="w-10 h-10 p-0 bg-gradient-to-r from-[#3898FF] to-[#8A78F2] hover:opacity-90 text-white shadow-md"
                  title="Nouvelle conversation"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Tabs */}
        {sidebarOpen && (
          <div className="flex border-b bg-white/90">
            <button
              onClick={() => setActiveTab('conversations')}
              className={cn(
                "flex-1 flex items-center justify-center gap-2 px-3 py-2.5 text-sm font-medium transition-all",
                activeTab === 'conversations'
                  ? "border-b-2 border-[#3898FF] text-[#3898FF] bg-[#3898FF]/5"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              )}
            >
              <MessageSquare className="h-4 w-4" />
              <span>Conversations</span>
            </button>
            <button
              onClick={() => setActiveTab('recipes')}
              className={cn(
                "flex-1 flex items-center justify-center gap-2 px-3 py-2.5 text-sm font-medium transition-all",
                activeTab === 'recipes'
                  ? "border-b-2 border-[#3898FF] text-[#3898FF] bg-[#3898FF]/5"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              )}
            >
              <Layers className="h-4 w-4" />
              <span>Recettes</span>
              {activeRecipes.length > 0 && (
                <span className="ml-1 px-2 py-0.5 text-xs font-medium rounded-full bg-gradient-to-r from-[#8A78F2] to-[#F178B6] text-white">
                  {activeRecipes.length}
                </span>
              )}
            </button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {sidebarOpen && (
            activeTab === 'conversations' ? (
              <ConversationList />
            ) : (
              <RecipeList />
            )
          )}
        </div>

        {/* Footer */}
        <div className={cn("border-t bg-white/90", sidebarOpen ? "p-3" : "p-2")}>
          {sidebarOpen ? (
            <div>
              <div className="flex items-center justify-between px-2 mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#3898FF] to-[#8A78F2] flex items-center justify-center">
                    <User className="h-4 w-4 text-white" />
                  </div>
                  <div className="text-sm">
                    <div className="font-medium text-slate-900">{auth.user?.name || 'Utilisateur'}</div>
                    <div className="text-xs text-slate-500">{auth.user?.email}</div>
                  </div>
                </div>
              </div>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="flex-1 justify-start text-slate-600 hover:bg-slate-100"
                  onClick={() => router.push('/settings')}
                >
                  <Settings className="h-4 w-4 mr-2" />
                  Paramètres
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-slate-600 hover:bg-red-50 hover:text-red-600"
                  onClick={handleLogout}
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex justify-center">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="w-10 h-10 p-0 text-slate-400 hover:text-red-600 hover:bg-red-50"
                title="Déconnexion"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col relative z-10">
        {/* Chat interface */}
        <ChatInterfaceV3 className="flex-1" />
      </div>
    </div>
  );
}