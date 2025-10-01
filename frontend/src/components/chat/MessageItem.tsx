"use client";

import React from 'react';
import { Message, ToolCall } from '@/lib/types/chat';
import { ToolCallCard } from './ToolCallCard';
import { cn } from '@/lib/utils';
import { User, Bot, FileText, Download } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Button } from '@/components/ui/button';

interface MessageItemProps {
  message: Message;
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  const renderContent = () => {
    if (typeof message.content === 'string') {
      if (isUser) {
        return <p className="whitespace-pre-wrap">{message.content}</p>;
      }

      // For assistant messages, render markdown
      return (
        <div className="prose prose-sm max-w-none dark:prose-invert">
          <ReactMarkdown
            components={{
            // Custom rendering for code blocks
            code({ node, inline, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '');
              const lang = match ? match[1] : '';

              if (!inline && lang) {
                return (
                  <div className="relative">
                    <pre className={cn("bg-muted rounded-md p-3 overflow-x-auto", className)}>
                      <code {...props}>{children}</code>
                    </pre>
                    <span className="absolute top-2 right-2 text-xs text-muted-foreground">
                      {lang}
                    </span>
                  </div>
                );
              }

              return (
                <code className="bg-muted px-1 py-0.5 rounded text-sm" {...props}>
                  {children}
                </code>
              );
            },
            // Custom rendering for links
            a({ children, href, ...props }) {
              return (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                  {...props}
                >
                  {children}
                </a>
              );
            }
          }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      );
    }

    // Handle structured content (tool calls, attachments, etc.)
    return message.content;
  };

  const renderToolCalls = () => {
    if (!message.toolCalls || message.toolCalls.length === 0) return null;

    return (
      <div className="mt-3 space-y-2">
        {message.toolCalls.map((toolCall, index) => (
          <ToolCallCard key={toolCall.id || index} toolCall={toolCall} />
        ))}
      </div>
    );
  };

  const renderAttachments = () => {
    if (!message.attachments || message.attachments.length === 0) return null;

    return (
      <div className="mt-3 flex flex-wrap gap-2">
        {message.attachments.map((attachment, index) => (
          <div
            key={index}
            className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-md text-sm"
          >
            <FileText className="h-4 w-4" />
            <span className="max-w-[200px] truncate">{attachment.name}</span>
            {attachment.url && (
              <Button
                variant="ghost"
                size="sm"
                className="h-auto p-0.5"
                asChild
              >
                <a href={attachment.url} download={attachment.name}>
                  <Download className="h-3 w-3" />
                </a>
              </Button>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div
      className={cn(
        "flex gap-4",
        isUser && "flex-row-reverse"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser ? "bg-primary text-primary-foreground" : "bg-muted"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4" />
        ) : (
          <Bot className="h-4 w-4" />
        )}
      </div>

      {/* Message content */}
      <div className={cn("flex-1 space-y-2", isUser && "flex flex-col items-end")}>
        <div
          className={cn(
            "rounded-lg px-4 py-2",
            isUser
              ? "bg-primary text-primary-foreground max-w-[80%]"
              : "bg-muted max-w-full"
          )}
        >
          {renderContent()}
          {renderAttachments()}
        </div>

        {/* Tool calls (only for assistant messages) */}
        {isAssistant && renderToolCalls()}

        {/* Timestamp */}
        <div className="text-xs text-muted-foreground px-1">
          {new Date(message.timestamp).toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </div>
    </div>
  );
}