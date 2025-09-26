"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { 
  Users, 
  FileText, 
  Activity, 
  AlertTriangle,
  TrendingUp,
  Database,
  Clock,
  Shield
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { adminAPI } from "@/lib/api";
import { formatTiming } from "@/lib/utils";
import type { AdminMetrics } from "@/lib/types";

type QError = { message?: string };

export default function AdminPage() {
  const router = useRouter();
  const auth = useAuth();
  
  const isAuthed = auth.isAuthenticated;
  const isAdmin = auth.canAccess("admin");

  // Stabilized redirect effect
  React.useEffect(() => {
    if (!isAuthed) {
      router.push("/login");
    } else if (!isAdmin) {
      router.push("/search");
    }
  }, [isAuthed, isAdmin, router]);

  // Fetch metrics
  const { data: metrics, isLoading, error } = useQuery({
    queryKey: ["admin-metrics"],
    queryFn: adminAPI.getMetrics,
    refetchInterval: 30000, // Refresh every 30 seconds
    enabled: isAuthed && isAdmin,
  });

  if (!isAuthed || !isAdmin) {
    return null; // Will redirect
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Console d'administration</h1>
            <p className="text-muted-foreground">
              Surveillance et gestion de la plateforme
            </p>
          </div>
          
          <Badge variant="secondary" className="flex items-center space-x-1">
            <Shield className="h-3 w-3" />
            <span>Accès administrateur</span>
          </Badge>
        </div>

        {/* Error state */}
        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Erreur lors du chargement des métriques: {(error as QError)?.message ?? "inconnue"}
            </AlertDescription>
          </Alert>
        )}

        {/* Metrics Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Documents"
            value={metrics?.total_documents}
            icon={FileText}
            isLoading={isLoading}
            description="Documents indexés"
          />
          
          <MetricCard
            title="Utilisateurs"
            value={metrics?.total_users}
            icon={Users}
            isLoading={isLoading}
            description="Comptes actifs"
          />
          
          <MetricCard
            title="Requêtes"
            value={metrics?.ask_requests}
            icon={TrendingUp}
            isLoading={isLoading}
            description="Questions posées"
          />
          
          <MetricCard
            title="P95 Latence"
            value={metrics?.ask_p95_ms ? formatTiming(metrics.ask_p95_ms) : undefined}
            icon={Clock}
            isLoading={isLoading}
            description="Temps de réponse"
            color={metrics?.ask_p95_ms && metrics.ask_p95_ms > 5000 ? "text-red-600" : "text-green-600"}
          />
        </div>

        {/* Detailed Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Performance Metrics */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="h-5 w-5" />
                <span>Performance</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {isLoading ? (
                <div className="space-y-2">
                  <div className="h-4 bg-muted rounded animate-pulse" />
                  <div className="h-4 bg-muted rounded animate-pulse w-3/4" />
                  <div className="h-4 bg-muted rounded animate-pulse w-1/2" />
                </div>
              ) : metrics ? (
                <>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Requêtes RAG</span>
                    <span className="font-medium">{metrics.ask_requests}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Indexations</span>
                    <span className="font-medium">{metrics.ingest_requests}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Erreurs</span>
                    <span className={`font-medium ${metrics.errors > 0 ? "text-red-600" : "text-green-600"}`}>
                      {metrics.errors}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Rate limits actifs</span>
                    <span className="font-medium">{metrics.rate_limits_active}</span>
                  </div>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">Données non disponibles</p>
              )}
            </CardContent>
          </Card>

          {/* System Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Database className="h-5 w-5" />
                <span>État du système</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <StatusIndicator
                  label="API Backend"
                  status="healthy"
                  description="Fonctionnel"
                />
                
                <StatusIndicator
                  label="Index FAISS"
                  status={metrics?.total_documents ? "healthy" : "warning"}
                  description={`${metrics?.total_documents || 0} documents`}
                />
                
                <StatusIndicator
                  label="Authentification"
                  status="healthy"
                  description="JWT actif"
                />
                
                <StatusIndicator
                  label="Rate Limiting"
                  status={metrics && metrics.rate_limits_active < 10 ? "healthy" : "warning"}
                  description={`${metrics?.rate_limits_active || 0} limites actives`}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Users Management (Placeholder) */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Users className="h-5 w-5" />
              <span>Gestion des utilisateurs</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center space-y-4 py-8">
              <Users className="mx-auto h-12 w-12 text-muted-foreground" />
              <div>
                <h3 className="text-lg font-medium">Gestion d'utilisateurs</h3>
                <p className="text-muted-foreground">
                  Interface de gestion des comptes utilisateurs à venir
                </p>
              </div>
              <div className="flex justify-center space-x-2">
                <Button variant="outline" disabled>
                  Inviter un utilisateur
                </Button>
                <Button variant="outline" disabled>
                  Gérer les permissions
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Actions rapides</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" disabled>
                Rebuild index
              </Button>
              <Button variant="outline" disabled>
                Nettoyer le cache
              </Button>
              <Button variant="outline" disabled>
                Export des logs
              </Button>
              <Button variant="outline" disabled>
                Sauvegarde
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Ces fonctionnalités seront disponibles dans une version future
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Helper components
interface MetricCardProps {
  title: string;
  value?: number | string;
  icon: React.ComponentType<{ className?: string }>;
  isLoading: boolean;
  description?: string;
  color?: string;
}

function MetricCard({ 
  title, 
  value, 
  icon: Icon, 
  isLoading, 
  description,
  color = "text-foreground"
}: MetricCardProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            {isLoading ? (
              <div className="h-8 w-16 bg-muted rounded animate-pulse mt-1" />
            ) : (
              <div className={`text-2xl font-bold ${color}`}>
                {value ?? "—"}
              </div>
            )}
            {description && (
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            )}
          </div>
          <Icon className="h-8 w-8 text-muted-foreground" />
        </div>
      </CardContent>
    </Card>
  );
}

interface StatusIndicatorProps {
  label: string;
  status: "healthy" | "warning" | "error";
  description?: string;
}

function StatusIndicator({ label, status, description }: StatusIndicatorProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy": return "bg-green-500";
      case "warning": return "bg-yellow-500";
      case "error": return "bg-red-500";
      default: return "bg-gray-500";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "healthy": return "Sain";
      case "warning": return "Attention";
      case "error": return "Erreur";
      default: return "Inconnu";
    }
  };

  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center space-x-3">
        <div className={`h-2 w-2 rounded-full ${getStatusColor(status)}`} />
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="text-right">
        <div className="text-sm text-muted-foreground">
          {getStatusText(status)}
        </div>
        {description && (
          <div className="text-xs text-muted-foreground">{description}</div>
        )}
      </div>
    </div>
  );
}