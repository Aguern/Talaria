"use client";

import React from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { X, FileText, Image } from 'lucide-react';

interface AttachmentAreaProps {
  attachments: File[];
  onRemove: (index: number) => void;
  className?: string;
}

export function AttachmentArea({ attachments, onRemove, className }: AttachmentAreaProps) {
  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return Image;
    }
    return FileText;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  return (
    <div className={cn("border-t pt-3", className)}>
      <div className="flex flex-wrap gap-2">
        {attachments.map((file, index) => {
          const Icon = getFileIcon(file);

          return (
            <div
              key={index}
              className="flex items-center gap-2 px-3 py-2 bg-muted rounded-md group"
            >
              <Icon className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <div className="min-w-0">
                <div className="text-sm font-medium truncate max-w-[150px]">
                  {file.name}
                </div>
                <div className="text-xs text-muted-foreground">
                  {formatFileSize(file.size)}
                </div>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => onRemove(index)}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          );
        })}
      </div>
    </div>
  );
}