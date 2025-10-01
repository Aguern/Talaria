"use client";

import React, { useState } from 'react';
import { ToolCall } from '@/lib/types/chat';
import { cn } from '@/lib/utils';
import {
  ChevronDown,
  ChevronRight,
  Zap,
  CheckCircle,
  XCircle,
  Loader2,
  FileText,
  Database,
  Send
} from 'lucide-react';

interface ToolCallCardProps {
  toolCall: ToolCall;
  className?: string;
}

export function ToolCallCard({ toolCall, className }: ToolCallCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getIcon = () => {
    // Icon based on tool category or name
    if (toolCall.name.includes('extract')) return FileText;
    if (toolCall.name.includes('generate')) return Send;
    if (toolCall.name.includes('complete')) return Database;
    return Zap;
  };

  const getStatusIcon = () => {
    switch (toolCall.status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Zap className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const Icon = getIcon();

  const formatArguments = (args: any) => {
    try {
      return JSON.stringify(args, null, 2);
    } catch {
      return String(args);
    }
  };

  const formatResult = (result: any) => {
    if (typeof result === 'string') return result;

    try {
      return JSON.stringify(result, null, 2);
    } catch {
      return String(result);
    }
  };

  return (
    <div
      className={cn(
        "border rounded-lg overflow-hidden bg-card",
        toolCall.status === 'error' && "border-red-500/50",
        className
      )}
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <Icon className="h-4 w-4 text-muted-foreground" />
          <div className="text-left">
            <div className="font-medium text-sm">{toolCall.displayName || toolCall.name}</div>
            {toolCall.description && (
              <div className="text-xs text-muted-foreground">{toolCall.description}</div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {getStatusIcon()}
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="px-4 pb-3 space-y-3 border-t">
          {/* Arguments */}
          {toolCall.arguments && (
            <div className="space-y-1">
              <div className="text-xs font-medium text-muted-foreground">Paramètres :</div>
              <pre className="text-xs bg-muted rounded p-2 overflow-x-auto">
                {formatArguments(toolCall.arguments)}
              </pre>
            </div>
          )}

          {/* Result */}
          {toolCall.result && (
            <div className="space-y-1">
              <div className="text-xs font-medium text-muted-foreground">
                {toolCall.status === 'error' ? 'Erreur :' : 'Résultat :'}
              </div>
              <pre
                className={cn(
                  "text-xs rounded p-2 overflow-x-auto",
                  toolCall.status === 'error' ? "bg-red-500/10" : "bg-muted"
                )}
              >
                {formatResult(toolCall.result)}
              </pre>
            </div>
          )}

          {/* Duration */}
          {toolCall.duration && (
            <div className="text-xs text-muted-foreground">
              Durée : {toolCall.duration}ms
            </div>
          )}
        </div>
      )}
    </div>
  );
}