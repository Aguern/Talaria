"use client";

import React from 'react';
import { MessageItem } from './MessageItem';
import { Message } from '@/lib/types/chat';
import { Loader2 } from 'lucide-react';

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  return (
    <div className="space-y-6">
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}

      {isLoading && (
        <div className="flex items-center gap-3 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm">Assistant réfléchit...</span>
        </div>
      )}

      {messages.length === 0 && !isLoading && (
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-lg mb-2">Commencez une nouvelle conversation</p>
          <p className="text-sm">Posez une question ou activez une recette pour démarrer</p>
        </div>
      )}
    </div>
  );
}