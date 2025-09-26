"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SearchBox } from "@/components/SearchBox";
import { InteractiveAnswer } from "@/components/InteractiveAnswer";
import { SuggestedQuestions } from "@/components/SuggestedQuestions";
import {
  AlertCircle,
  ThumbsUp,
  ThumbsDown,
  Clock,
  Building2,
  Plus,
  PanelLeftClose,
  PanelLeftOpen,
  MessageSquare,
  LogOut
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useAsk, useFeedback } from "@/hooks/useAsk";
import { useStreamingAsk } from "@/hooks/useStreamingAsk";
import { useFilters, useHistory } from "@/lib/stores";
import { getFallbackSchema } from "@/lib/filters-presets";
import { toast } from "sonner";

export default function SearchPage() {
  const router = useRouter();
  const auth = useAuth();
  const { schema, setSchema } = useFilters();
  const { recent } = useHistory();
  // const { ask, isLoading, data: response, error: askError, streamingText, isStreaming } = useAsk();
  const { askStream, isStreaming, streamingText, status, response, error: askError, conversationId, reset } = useStreamingAsk();
  const { sendFeedback } = useFeedback();
  const isLoading = isStreaming;
  const scrollContainerRef = React.useRef<HTMLDivElement>(null);
  const [currentQuestion, setCurrentQuestion] = React.useState<string>("");
  const [sidebarExpanded, setSidebarExpanded] = React.useState<boolean>(true);

  // Initialize filters if not set
  React.useEffect(() => {
    if (schema.length === 0 && auth.vertical) {
      const fallbackSchema = getFallbackSchema(auth.vertical);
      setSchema(fallbackSchema);
    }
  }, [schema.length, auth.vertical, setSchema]);

  // Auto-scroll during streaming
  React.useEffect(() => {
    if (isStreaming && scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [streamingText, isStreaming]);

  // Si l'utilisateur n'est pas connecté, on le redirige vers la page de connexion.
  React.useEffect(() => {
    if (!auth.isAuthenticated) {
      router.replace("/");
    }
  }, [auth.isAuthenticated, router]);

  const handleSearch = async (question: string) => {
    if (!auth.isAuthenticated) {
      toast.error("Veuillez vous connecter pour effectuer une recherche");
      router.push("/");
      return;
    }

    try {
      setCurrentQuestion(question);
      await askStream(question, conversationId || undefined);
    } catch (error) {
      // Error is handled by useStreamingAsk hook
      console.error("Search error:", error);
    }
  };

  const startNewConversation = () => {
    setCurrentQuestion("");
    reset(); // Reset streaming state
    // Note: Pas besoin de recharger la page avec le vrai streaming
  };

  const toggleSidebar = () => {
    setSidebarExpanded(!sidebarExpanded);
  };

  const handleFeedback = (rating: "up" | "down", reason?: string) => {
    if (!response) return;
    
    // Find the question from recent history (latest item)
    const latestSearch = recent[0];
    if (latestSearch) {
      sendFeedback(latestSearch.question, response.answer, rating, reason);
      toast.success("Merci pour votre retour !");
    }
  };


  // Sample suggestions based on vertical
  const getSuggestions = () => {
    switch (auth.vertical) {
      case "btp":
        return [
          "Quelles sont les normes de sécurité pour travaux en hauteur ?",
          "Procédures de bétonnage selon DTU 21 ?",
          "Liste des équipements de protection individuelle requis ?",
          "Modalités de réception des travaux de voirie ?",
        ];
      case "notaires":
        return [
          "Procédure de rédaction d'un acte de vente ?",
          "Documents requis pour une succession ?",
          "Calcul des droits de mutation ?",
          "Formalités hypothécaires obligatoires ?",
        ];
      case "compta":
        return [
          "Comptabilisation des immobilisations ?",
          "Déclaration TVA mensuelle ?",
          "Clôture des comptes annuels ?",
          "Calcul des provisions pour congés payés ?",
        ];
      default:
        return [
          "Comment puis-je vous aider ?",
          "Recherchez dans vos documents...",
        ];
    }
  };

  if (!auth.isAuthenticated) {
    // Affiche un loader ou rien pendant la redirection.
    return <div className="flex h-screen w-full items-center justify-center">Chargement...</div>;
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar gauche - Expansible/Réduite */}
      <div
        className={`border-r bg-background flex flex-col transition-all duration-300 ${
          sidebarExpanded ? 'w-80' : 'w-16'
        }`}
      >
        {/* Header sidebar */}
        <div className="p-3 border-b">
          {sidebarExpanded ? (
            // Version étendue
            <div>
              <div className="flex items-center justify-between mb-4">
                <Button
                  onClick={startNewConversation}
                  className="flex-1 mr-2 bg-teal-600 hover:bg-teal-700 text-white font-medium"
                  size="sm"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Nouvelle conversation
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleSidebar}
                  className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-2"
                >
                  <PanelLeftClose className="w-4 h-4" />
                </Button>
              </div>

              {/* Tenant badge */}
              <div className="flex items-center justify-between">
                {auth.currentTenant && (
                  <Badge variant="outline" className="text-xs border-teal-200 text-teal-700 bg-teal-50">
                    {auth.currentTenant}
                  </Badge>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => auth.logout()}
                  className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 text-xs"
                >
                  Déconnexion
                </Button>
              </div>
            </div>
          ) : (
            // Version réduite - icônes simples
            <div className="space-y-3">
              <div className="flex flex-col items-center space-y-2">
                <Button
                  variant="ghost"
                  onClick={toggleSidebar}
                  className="w-10 h-10 p-0 text-slate-400 hover:text-slate-600 hover:bg-slate-100"
                  title="Ouvrir la barre latérale"
                >
                  <PanelLeftOpen className="w-5 h-5" />
                </Button>

                <Button
                  onClick={startNewConversation}
                  className="w-10 h-10 p-0 bg-teal-600 hover:bg-teal-700 text-white"
                  title="Nouvelle conversation"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Historique */}
        <div className="flex-1 overflow-auto">
          {sidebarExpanded ? (
            // Version étendue - historique complet
            recent.length > 0 ? (
              <div className="p-3">
                <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3 px-1">
                  Historique récent
                </h3>
                <div className="space-y-1">
                  {recent.slice(0, 20).map((item, index) => (
                    <div
                      key={index}
                      className="p-3 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors group border border-transparent hover:border-slate-200"
                      onClick={() => handleSearch(item.question)}
                    >
                      <p className="text-sm text-slate-700 leading-snug line-clamp-2">
                        {item.question}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(item.timestamp).toLocaleDateString('fr-FR', {
                          day: 'numeric',
                          month: 'short'
                        })}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center p-6">
                <Clock className="w-12 h-12 text-muted-foreground/30 mb-4" />
                <p className="text-sm text-muted-foreground mb-2">Aucun historique</p>
                <p className="text-xs text-muted-foreground/70">
                  Vos conversations apparaîtront ici
                </p>
              </div>
            )
          ) : (
            // Version réduite - Icône bulle pour ouvrir l'historique
            recent.length > 0 && (
              <div className="p-2 flex justify-center">
                <Button
                  variant="ghost"
                  onClick={toggleSidebar}
                  className="w-10 h-10 p-0 text-slate-400 hover:text-slate-600 hover:bg-slate-100"
                  title="Voir l'historique des conversations"
                >
                  <MessageSquare className="w-5 h-5" />
                </Button>
              </div>
            )
          )}
        </div>

        {/* Footer sidebar */}
        <div className={`border-t ${sidebarExpanded ? 'p-4 bg-slate-50/50' : 'p-2'}`}>
          {sidebarExpanded ? (
            <div className="text-xs text-muted-foreground text-center">
              propulsé par <span className="font-medium text-teal-600">nouvelle-rive.com</span>
            </div>
          ) : (
            <div className="flex justify-center">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => auth.logout()}
                className="w-10 h-10 p-0 text-slate-400 hover:text-red-600 hover:bg-red-50"
                title="Déconnexion"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Zone principale */}
      <div className="flex-1 flex flex-col">
        {/* Zone de conversation */}
        <div ref={scrollContainerRef} className="flex-1 overflow-auto">
          {!response && !isLoading && !askError && !isStreaming ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-2xl px-4">
                <h2 className="text-2xl font-semibold text-foreground mb-4">
                  Que puis-je vous aider à rechercher ?
                </h2>
                <p className="text-muted-foreground mb-8">
                  Posez une question et je vous fournirai des réponses basées sur vos documents avec des sources précises.
                </p>
                
                {/* Suggestions */}
                <div className="grid gap-2 max-w-lg mx-auto">
                  {getSuggestions().slice(0, 3).map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSearch(suggestion)}
                      className="p-3 text-sm text-left rounded-lg border hover:bg-muted/50 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 space-y-8">
              {/* Message utilisateur et réponse IA style chat */}
              <div className="max-w-4xl mx-auto space-y-6">
                {/* Question utilisateur */}
                {currentQuestion && (
                  <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
                    <div className="flex items-start space-x-4">
                      <div className="w-8 h-8 rounded-full bg-teal-100 flex items-center justify-center flex-shrink-0">
                        <span className="text-sm font-medium text-teal-700">
                          {auth.user?.email?.charAt(0).toUpperCase() || "U"}
                        </span>
                      </div>
                      <div className="flex-1">
                        <p className="text-slate-800 font-medium leading-relaxed">{currentQuestion}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Réponse IA */}
                <div className="bg-slate-50 rounded-2xl p-6 border border-slate-100">
                  {isLoading && !streamingText ? (
                    <div className="space-y-3">
                      <div className="animate-pulse">
                        <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                        <div className="h-4 bg-muted rounded w-1/2 mb-2"></div>
                        <div className="h-4 bg-muted rounded w-2/3"></div>
                      </div>
                      <p className="text-sm text-teal-600 font-medium">{status || "Initialisation..."}</p>
                    </div>
                  ) : isStreaming || streamingText ? (
                    <div className="max-w-4xl mx-auto space-y-4">
                      {/* Texte en cours de streaming */}
                      <div className="prose prose-sm max-w-none">
                        <div className="whitespace-pre-wrap text-slate-700 leading-relaxed">
                          {streamingText}
                          <span className="animate-pulse text-teal-600">|</span>
                        </div>
                      </div>

                      {/* Citations si disponibles pendant le streaming */}
                      {response?.citations && response.citations.length > 0 && (
                        <div>
                          <InteractiveAnswer answer={streamingText} citations={response.citations} />
                        </div>
                      )}

                      {/* Actions si response disponible */}
                      {response && (
                        <div className="pt-4 border-t border-slate-200">
                          <div className="flex items-center space-x-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleFeedback("up")}
                              className="text-slate-400 hover:text-teal-600 hover:bg-teal-50"
                            >
                              <ThumbsUp className="w-4 h-4" />
                            </Button>

                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleFeedback("down")}
                              className="text-slate-400 hover:text-red-600 hover:bg-red-50"
                            >
                              <ThumbsDown className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      )}

                      {/* Questions suggérées si disponibles pendant le streaming */}
                      {response?.suggested_questions && response.suggested_questions.length > 0 && (
                        <div className="pt-4 mt-4 border-t border-slate-200">
                          <SuggestedQuestions
                            questions={response.suggested_questions}
                            onSelect={handleSearch}
                            isLoading={isLoading}
                          />
                        </div>
                      )}
                    </div>
                  ) : response ? (
                    <div className="max-w-4xl mx-auto space-y-4">
                      {/* Badge d'enrichissement BDNB */}
                      {response.enriched_with && (
                        <div className="flex items-center space-x-2 mb-4">
                          <Building2 className="w-4 h-4 text-emerald-600" />
                          <Badge variant="outline" className="border-emerald-200 text-emerald-700 bg-emerald-50">
                            ✨ Enrichi avec {response.enriched_with}
                          </Badge>
                        </div>
                      )}

                      {/* Réponse avec citations intégrées */}
                      <InteractiveAnswer answer={response.answer} citations={response.citations} />

                      {/* Actions */}
                      <div className="pt-4 border-t border-slate-200">
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleFeedback("up")}
                            className="text-slate-400 hover:text-teal-600 hover:bg-teal-50"
                          >
                            <ThumbsUp className="w-4 h-4" />
                          </Button>

                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleFeedback("down")}
                            className="text-slate-400 hover:text-red-600 hover:bg-red-50"
                          >
                            <ThumbsDown className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>

                      {/* Questions suggérées */}
                      {response.suggested_questions && response.suggested_questions.length > 0 && (
                        <div className="pt-4 mt-4 border-t border-slate-200">
                          <SuggestedQuestions
                            questions={response.suggested_questions}
                            onSelect={handleSearch}
                            isLoading={isLoading}
                          />
                        </div>
                      )}
                    </div>
                  ) : askError ? (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        {(askError as any)?.message || "Une erreur s'est produite lors de la recherche"}
                      </AlertDescription>
                    </Alert>
                  ) : null}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Zone de saisie fixe en bas */}
        <div className="bg-background">
          <div className="max-w-4xl mx-auto p-4">
            <SearchBox
              onSubmit={handleSearch}
              isLoading={isLoading}
              placeholder="Posez votre question..."
            />
          </div>
        </div>
      </div>
    </div>
  );
}