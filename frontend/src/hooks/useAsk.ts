import React from "react";
import { useMutation } from "@tanstack/react-query";
import { searchAPI, handleAPIError, apiFetch, sessionStorage } from "@/lib/api";
import { useHistory, useFilters } from "@/lib/stores";
import type { AskRequest, AskResponse } from "@/lib/types";

export function useAsk() {
  const { addItem } = useHistory();
  const { activeFilters } = useFilters();
  const [streamingText, setStreamingText] = React.useState("");
  const [isStreaming, setIsStreaming] = React.useState(false);
  const [finalResponse, setFinalResponse] = React.useState<AskResponse | null>(null);

  const askMutation = useMutation({
    mutationFn: async (question: string): Promise<AskResponse> => {
      const request: AskRequest = {
        question,
        ...activeFilters,
      };
      
      return searchAPI.ask(request);
    },
    onSuccess: (response, question) => {
      // Add to history
      addItem({
        question,
        answer: response.answer,
        citations: response.citations,
        filters: activeFilters,
        timing_ms: response.timing_ms,
      });
    },
    onError: handleAPIError,
  });

  const askWithStreaming = async (question: string) => {
    if (!question.trim()) {
      throw new Error("La question ne peut pas être vide");
    }

    setStreamingText("");
    setIsStreaming(true);
    setFinalResponse(null);
    
    try {
      const request: AskRequest = {
        question,
        ...activeFilters,
      };
      
      // Simulate streaming by calling regular API then displaying text progressively
      const response = await searchAPI.ask(request);
      
      // Stream the response text
      const text = response.answer;
      let currentText = "";
      
      for (let i = 0; i <= text.length; i++) {
        currentText = text.slice(0, i);
        setStreamingText(currentText);
        
        // Adjust speed: faster for spaces, slower for other chars
        const delay = text[i] === ' ' ? 5 : Math.random() * 8 + 3;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
      
      setIsStreaming(false);
      setFinalResponse(response);
      
      // Add to history
      addItem({
        question,
        answer: response.answer,
        citations: response.citations,
        filters: activeFilters,
        timing_ms: response.timing_ms,
      });
      
      return response;
    } catch (error) {
      setIsStreaming(false);
      setStreamingText("");
      throw error;
    }
  };

  const ask = (question: string) => {
    if (!question.trim()) {
      throw new Error("La question ne peut pas être vide");
    }
    return askMutation.mutateAsync(question);
  };

  return {
    ask: askWithStreaming,
    isLoading: askMutation.isPending || isStreaming,
    error: askMutation.error,
    data: finalResponse || askMutation.data,
    reset: () => {
      askMutation.reset();
      setStreamingText("");
      setIsStreaming(false);
      setFinalResponse(null);
    },
    streamingText,
    isStreaming,
  };
}

export function useFeedback() {
  const feedbackMutation = useMutation({
    mutationFn: searchAPI.feedback,
    onError: (error) => {
      // Feedback errors are non-critical, just log them
      console.warn("Feedback error:", error);
    },
  });

  const sendFeedback = (
    question: string,
    answer: string,
    rating: "up" | "down",
    reason?: string
  ) => {
    feedbackMutation.mutate({
      question,
      answer,
      rating,
      reason,
    });
  };

  return {
    sendFeedback,
    isLoading: feedbackMutation.isPending,
    error: feedbackMutation.error,
  };
}