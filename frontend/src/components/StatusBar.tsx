"use client";

import React from "react";
import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { cn, formatTiming, getConfidenceColor, getConfidenceLabel } from "@/lib/utils";

interface StatusBarProps {
  className?: string;
  children?: ReactNode;
}

export function StatusBar({ className, children }: StatusBarProps) {
  return (
    <div
      className={cn(
        "border-t bg-muted/50 px-4 py-2 text-sm text-muted-foreground",
        className
      )}
      aria-live="polite"
      aria-label="Barre de statut"
      data-testid="status-bar"
    >
      {children}
    </div>
  );
}

interface StatusMessageProps {
  message: string;
  timing?: number;
  confidence?: number;
  type?: "info" | "success" | "warning" | "error";
}

export function StatusMessage({
  message,
  timing,
  confidence,
  type = "info",
}: StatusMessageProps) {
  const baseStyles = {
    info: "text-muted-foreground",
    success: "text-green-600",
    warning: "text-yellow-600",
    error: "text-red-600",
  };

  return (
    <div className="flex items-center gap-2">
      <span className={baseStyles[type]}>{message}</span>
      
      {timing && (
        <Badge variant="outline" className="text-xs" data-testid="search-timing">
          {formatTiming(timing)}
        </Badge>
      )}
      
      {confidence !== undefined && (
        <Badge 
          variant="outline" 
          className={cn("text-xs", getConfidenceColor(confidence))}
          data-testid="confidence-badge"
        >
          Confiance: {getConfidenceLabel(confidence)}
        </Badge>
      )}
    </div>
  );
}

interface ConnectionStatusProps {
  isConnected: boolean;
  clientId?: string;
  userName?: string;
}

export function ConnectionStatus({ 
  isConnected, 
  clientId, 
  userName 
}: ConnectionStatusProps) {
  if (!isConnected) {
    return (
      <div className="flex items-center gap-2">
        <div className="h-2 w-2 rounded-full bg-red-500" />
        <span className="text-red-600">Hors ligne</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2" data-testid="connection-status">
      <div className="h-2 w-2 rounded-full bg-green-500" />
      <span className="text-green-600">Connecté</span>
      {clientId && (
        <>
          <span className="text-muted-foreground">•</span>
          <span data-testid="current-tenant">Espace : {clientId}</span>
        </>
      )}
      {userName && (
        <>
          <span className="text-muted-foreground">•</span>
          <span data-testid="current-user">{userName}</span>
        </>
      )}
    </div>
  );
}