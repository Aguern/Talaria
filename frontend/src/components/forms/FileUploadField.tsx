"use client";

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  Upload,
  File,
  X,
  FileText,
  Image,
  FileArchive,
  AlertCircle
} from 'lucide-react';

interface FileUploadFieldProps {
  name: string;
  label: string;
  description?: string;
  multiple?: boolean;
  required?: boolean;
  accept?: string;
  maxSize?: number; // in bytes
  value: File[];
  onChange: (files: File[]) => void;
  error?: string;
}

export function FileUploadField({
  name,
  label,
  description,
  multiple = false,
  required = false,
  accept = "*/*",
  maxSize = 10 * 1024 * 1024, // 10MB default
  value,
  onChange,
  error
}: FileUploadFieldProps) {
  const [dragActive, setDragActive] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    if (rejectedFiles.length > 0) {
      console.warn('Some files were rejected:', rejectedFiles);
    }

    if (multiple) {
      onChange([...value, ...acceptedFiles]);
    } else {
      onChange(acceptedFiles);
    }
  }, [value, onChange, multiple]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: accept === "*/*" ? undefined : { [accept]: [] },
    multiple,
    maxSize,
    onDragEnter: () => setDragActive(true),
    onDragLeave: () => setDragActive(false)
  });

  const removeFile = (index: number) => {
    const newFiles = value.filter((_, i) => i !== index);
    onChange(newFiles);
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return Image;
    } else if (file.type.includes('pdf') || file.type.includes('document')) {
      return FileText;
    } else if (file.type.includes('zip') || file.type.includes('archive')) {
      return FileArchive;
    }
    return File;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-3">
      {/* Label and description */}
      <div>
        <label className="block text-sm font-medium text-slate-900 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        {description && (
          <p className="text-sm text-slate-600">{description}</p>
        )}
      </div>

      {/* Upload zone */}
      <Card
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed cursor-pointer transition-all duration-200",
          "hover:border-blue-400 hover:bg-blue-50/50",
          isDragActive || dragActive
            ? "border-blue-500 bg-blue-50"
            : "border-slate-300",
          error ? "border-red-400 bg-red-50" : "",
          "relative overflow-hidden"
        )}
      >
        <input {...getInputProps()} />
        <div className="p-8 text-center">
          <Upload className={cn(
            "h-10 w-10 mx-auto mb-4 transition-colors",
            isDragActive || dragActive ? "text-blue-500" : "text-slate-400"
          )} />

          <div className="space-y-2">
            <p className="text-lg font-medium text-slate-900">
              {isDragActive || dragActive
                ? "Déposez vos fichiers ici"
                : "Glissez-déposez vos fichiers"
              }
            </p>
            <p className="text-sm text-slate-600">
              ou{" "}
              <span className="text-blue-600 font-medium hover:text-blue-700">
                cliquez pour parcourir
              </span>
            </p>
            <div className="text-xs text-slate-500 space-y-1">
              {multiple && <p>Plusieurs fichiers acceptés</p>}
              <p>Taille max: {formatFileSize(maxSize)}</p>
              {accept !== "*/*" && <p>Types: {accept}</p>}
            </div>
          </div>
        </div>
      </Card>

      {/* Error message */}
      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {/* File list */}
      {value.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-slate-900">
            Fichiers sélectionnés ({value.length})
          </h4>
          <div className="space-y-2">
            {value.map((file, index) => {
              const Icon = getFileIcon(file);
              return (
                <div
                  key={`${file.name}-${index}`}
                  className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border"
                >
                  <Icon className="h-5 w-5 text-slate-600 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(index)}
                    className="flex-shrink-0 h-8 w-8 p-0 text-slate-400 hover:text-red-500"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}