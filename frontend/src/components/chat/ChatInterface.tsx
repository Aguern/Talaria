"use client";

import React, { useState, useRef, useEffect } from 'react';
import { MessageList } from './MessageList';
import { InputArea } from './InputArea';
import { AttachmentArea } from './AttachmentArea';
import { useChatStore } from '@/lib/stores/chat.store';
import { useMCPStore } from '@/lib/stores/mcp.store';
import { cn } from '@/lib/utils';

interface ChatInterfaceProps {
  conversationId?: string;
  className?: string;
}

export function ChatInterface({ conversationId, className }: ChatInterfaceProps) {
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

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Messages area */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto px-4 py-6"
      >
        <MessageList
          messages={messages}
          isLoading={isLoading}
        />
      </div>

      {/* Attachment preview area */}
      {attachments.length > 0 && (
        <AttachmentArea
          attachments={attachments}
          onRemove={removeAttachment}
          className="px-4 pb-2"
        />
      )}

      {/* Input area */}
      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <InputArea
          onSend={handleSendMessage}
          onFileDrop={handleFileDrop}
          disabled={isLoading}
          placeholder={
            activeRecipes.length > 0
              ? `Message (${activeRecipes.length} recette${activeRecipes.length > 1 ? 's' : ''} active${activeRecipes.length > 1 ? 's' : ''})`
              : "Envoyez un message..."
          }
          className="max-w-3xl mx-auto"
        />
      </div>
    </div>
  );
}