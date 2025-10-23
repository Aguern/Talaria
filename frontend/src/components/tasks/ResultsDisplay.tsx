"use client";

import React from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Download,
  FileText,
  CheckCircle,
  ExternalLink,
  File,
  Image,
  Archive,
  Code
} from 'lucide-react';
import { recipesAPI } from '@/lib/api/recipes';

interface ResultFile {
  name: string;
  path: string;
  type: string;
  description?: string;
}

interface ResultsDisplayProps {
  taskId: string;
  results: Record<string, any>;
  className?: string;
}

export function ResultsDisplay({ taskId, results, className }: ResultsDisplayProps) {
  const getFileIcon = (type: string, name: string) => {
    const lowerName = name.toLowerCase();

    if (type === 'file_pdf' || lowerName.includes('.pdf')) {
      return FileText;
    } else if (type.includes('image') || /\.(jpg|jpeg|png|gif|svg)$/.test(lowerName)) {
      return Image;
    } else if (type.includes('zip') || type.includes('archive') || /\.(zip|rar|tar|gz)$/.test(lowerName)) {
      return Archive;
    } else if (type === 'json' || lowerName.includes('.json')) {
      return Code;
    }
    return File;
  };

  const getFileTypeLabel = (type: string) => {
    switch (type) {
      case 'file_pdf':
        return 'PDF';
      case 'json':
        return 'JSON';
      case 'csv':
        return 'CSV';
      case 'xlsx':
        return 'Excel';
      default:
        return type.toUpperCase();
    }
  };

  const handleDownload = (outputName: string, fileName?: string) => {
    const downloadUrl = recipesAPI.getDownloadUrl(taskId, outputName);

    // Create a temporary link to trigger download
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = fileName || outputName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handlePreview = (outputName: string) => {
    const previewUrl = recipesAPI.getDownloadUrl(taskId, outputName);
    window.open(previewUrl, '_blank');
  };

  // Separate file outputs from data outputs
  const fileOutputs: Array<{ key: string; value: any; isFile: boolean }> = [];
  const dataOutputs: Array<{ key: string; value: any; isFile: boolean }> = [];

  Object.entries(results).forEach(([key, value]) => {
    const isFilePath = typeof value === 'string' && (
      value.includes('/') ||
      value.includes('\\') ||
      value.endsWith('.pdf') ||
      value.endsWith('.json') ||
      value.endsWith('.csv') ||
      value.endsWith('.xlsx')
    );

    if (isFilePath) {
      fileOutputs.push({ key, value, isFile: true });
    } else {
      dataOutputs.push({ key, value, isFile: false });
    }
  });

  return (
    <div className={className}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <CheckCircle className="h-6 w-6 text-green-600" />
          <h3 className="text-lg font-semibold text-slate-900">
            Résultats de l'exécution
          </h3>
        </div>

        {/* File outputs */}
        {fileOutputs.length > 0 && (
          <Card className="p-6">
            <h4 className="font-medium text-slate-900 mb-4 flex items-center gap-2">
              <Download className="h-5 w-5" />
              Fichiers générés ({fileOutputs.length})
            </h4>

            <div className="space-y-3">
              {fileOutputs.map(({ key, value }) => {
                const fileName = value.split('/').pop() || key;
                const fileExtension = fileName.split('.').pop() || '';
                const Icon = getFileIcon(fileExtension, fileName);

                return (
                  <div
                    key={key}
                    className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-blue-100">
                        <Icon className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{fileName}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="secondary" className="text-xs">
                            {getFileTypeLabel(fileExtension)}
                          </Badge>
                          <span className="text-xs text-slate-500">{key}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {(fileExtension === 'pdf' || fileExtension === 'json') && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handlePreview(key)}
                        >
                          <ExternalLink className="h-4 w-4 mr-1" />
                          Aperçu
                        </Button>
                      )}
                      <Button
                        onClick={() => handleDownload(key, fileName)}
                        size="sm"
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        <Download className="h-4 w-4 mr-1" />
                        Télécharger
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        )}

        {/* Data outputs */}
        {dataOutputs.length > 0 && (
          <Card className="p-6">
            <h4 className="font-medium text-slate-900 mb-4 flex items-center gap-2">
              <Code className="h-5 w-5" />
              Données extraites
            </h4>

            <div className="space-y-4">
              {dataOutputs.map(({ key, value }) => (
                <div key={key} className="p-4 bg-slate-50 rounded-lg border">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="font-medium text-slate-900">{key}</h5>
                    <Badge variant="outline" className="text-xs">
                      {typeof value}
                    </Badge>
                  </div>

                  <div className="text-sm">
                    {typeof value === 'object' ? (
                      <pre className="bg-white p-3 rounded border text-xs overflow-x-auto">
                        {JSON.stringify(value, null, 2)}
                      </pre>
                    ) : (
                      <p className="text-slate-700 bg-white p-3 rounded border">
                        {String(value)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Empty state */}
        {fileOutputs.length === 0 && dataOutputs.length === 0 && (
          <Card className="p-8 text-center">
            <File className="h-12 w-12 text-slate-400 mx-auto mb-4" />
            <h4 className="font-medium text-slate-900 mb-2">
              Aucun résultat à afficher
            </h4>
            <p className="text-slate-600 text-sm">
              La tâche s'est terminée sans générer de fichiers ou de données.
            </p>
          </Card>
        )}

        {/* Summary info */}
        <Card className="p-4 bg-green-50 border-green-200">
          <div className="flex items-center gap-2 text-green-800">
            <CheckCircle className="h-4 w-4" />
            <span className="font-medium text-sm">
              Tâche terminée avec succès
            </span>
          </div>
          <p className="text-green-700 text-sm mt-1">
            Tous les résultats sont disponibles au téléchargement.
          </p>
        </Card>
      </div>
    </div>
  );
}