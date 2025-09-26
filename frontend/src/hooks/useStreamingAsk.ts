import React from "react";
import { flushSync } from "react-dom";
import { sessionStorage } from "@/lib/api";
import { useHistory } from "@/lib/stores";
import type { AskRequest, AskResponse, Citation } from "@/lib/types";

interface StreamingState {
  isStreaming: boolean;
  streamingText: string;
  status: string;
  response: AskResponse | null;
  error: string | null;
  conversationId: string | null;
}

export function useStreamingAsk() {
  const { addItem } = useHistory();
  const [state, setState] = React.useState<StreamingState>({
    isStreaming: false,
    streamingText: "",
    status: "",
    response: null,
    error: null,
    conversationId: null,
  });

  const askStream = React.useCallback(async (question: string, conversationId?: string) => {
    if (!question.trim()) {
      throw new Error("La question ne peut pas être vide");
    }

    // Reset state
    setState({
      isStreaming: true,
      streamingText: "",
      status: "Connexion...",
      response: null,
      error: null,
      conversationId: conversationId || null,
    });

    try {
      const session = sessionStorage.get();
      if (!session?.token) {
        throw new Error("Non authentifié");
      }

      // Préparer la requête
      const request: AskRequest = {
        question,
        conversation_id: conversationId,
      };

      let finalCitations: Citation[] = [];
      let finalSuggestedQuestions: string[] = [];
      let finalConversationId = conversationId || "";
      let accumulatedText = "";

      // Utiliser le proxy Next.js avec les headers anti-buffering
      const response = await fetch("/packs/bofip/ask-stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.token}`,
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("Pas de stream disponible");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          // Décoder le chunk et l'ajouter au buffer
          const chunk = decoder.decode(value, { stream: true });
          console.log('Received chunk:', JSON.stringify(chunk)); // Debug log
          buffer += chunk;

          // Traiter toutes les lignes complètes du buffer
          let newlineIndex;
          while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
            const line = buffer.slice(0, newlineIndex).trim();
            buffer = buffer.slice(newlineIndex + 1);

            console.log('Processing line:', line); // Debug log

            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.substring(6));
                console.log('Parsed SSE data:', data); // Debug log

                switch (data.type) {
                  case "status":
                    console.log('Status update:', data.message); // Debug log
                    flushSync(() => {
                      setState((prev) => ({
                        ...prev,
                        status: data.message,
                        conversationId: data.conversation_id || prev.conversationId,
                      }));
                    });
                    break;

                  case "token":
                    console.log('Token received:', data.content); // Debug log
                    accumulatedText += data.content;
                    flushSync(() => {
                      setState((prev) => ({
                        ...prev,
                        streamingText: accumulatedText,
                        conversationId: data.conversation_id || prev.conversationId,
                      }));
                    });
                    break;

                  case "citations":
                    finalCitations = data.citations || [];
                    // Créer l'objet response avec les citations pour affichage immédiat
                    flushSync(() => {
                      setState((prev) => ({
                        ...prev,
                        response: {
                          answer: accumulatedText,
                          citations: finalCitations,
                          suggested_questions: finalSuggestedQuestions,
                          conversation_id: finalConversationId
                        }
                      }));
                    });
                    break;

                  case "suggested_questions":
                    finalSuggestedQuestions = data.questions || [];
                    // Créer l'objet response avec les questions suggérées pour affichage immédiat
                    flushSync(() => {
                      setState((prev) => ({
                        ...prev,
                        response: {
                          answer: accumulatedText,
                          citations: finalCitations,
                          suggested_questions: finalSuggestedQuestions,
                          conversation_id: finalConversationId
                        }
                      }));
                    });
                    break;

                  case "done":
                    finalConversationId = data.conversation_id;

                    // Créer la réponse finale
                    const finalResponse: AskResponse = {
                      answer: accumulatedText,
                      citations: finalCitations,
                      suggested_questions: finalSuggestedQuestions,
                      conversation_id: finalConversationId,
                    };

                    // Ajouter à l'historique
                    addItem({
                      question,
                      answer: accumulatedText,
                      citations: finalCitations,
                      filters: {},
                      timing_ms: undefined,
                    });

                    setState((prev) => ({
                      ...prev,
                      isStreaming: false,
                      status: "",
                      response: finalResponse,
                      conversationId: finalConversationId,
                    }));
                    return; // Sortir de la boucle

                  case "error":
                    setState((prev) => ({
                      ...prev,
                      isStreaming: false,
                      error: data.message,
                      status: "",
                    }));
                    return; // Sortir de la boucle
                }
              } catch (e) {
                console.error("Erreur parsing SSE:", e, line);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

    } catch (error) {
      setState((prev) => ({
        ...prev,
        isStreaming: false,
        error: error instanceof Error ? error.message : "Erreur inconnue",
        status: "",
      }));
    }
  }, [addItem]);

  const reset = React.useCallback(() => {
    setState({
      isStreaming: false,
      streamingText: "",
      status: "",
      response: null,
      error: null,
      conversationId: null,
    });
  }, []);

  return {
    askStream,
    isStreaming: state.isStreaming,
    streamingText: state.streamingText,
    status: state.status,
    response: state.response,
    error: state.error,
    conversationId: state.conversationId,
    reset,
  };
}