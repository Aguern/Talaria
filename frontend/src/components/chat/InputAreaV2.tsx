"use client";

import React, { useState, useRef, KeyboardEvent } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Paperclip,
  Send,
  X,
  FileText,
  Image as ImageIcon,
  Loader2,
  Layers
} from 'lucide-react';

interface InputAreaV2Props {
  onSend: (message: string) => void;
  onFileDrop?: (files: File[]) => void;
  attachments?: File[];
  onRemoveAttachment?: (index: number) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
  activeRecipes?: string[];
  isLoading?: boolean;
}

export function InputAreaV2({
  onSend,
  onFileDrop,
  attachments = [],
  onRemoveAttachment,
  disabled,
  placeholder = "Posez votre question...",
  className,
  activeRecipes = [],
  isLoading = false
}: InputAreaV2Props) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleSubmit = () => {
    if ((input.trim() || attachments.length > 0) && !disabled) {
      onSend(input.trim());
      setInput('');

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0 && onFileDrop) {
      onFileDrop(files);
    }
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0 && onFileDrop) {
      onFileDrop(files);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return ImageIcon;
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
    <div className={cn("relative", className)}>
      {/* Active recipes indicator */}
      {activeRecipes.length > 0 && (
        <div className="mb-3 flex items-center gap-2">
          <Layers className="h-4 w-4 text-[#3898FF]" />
          <span className="text-sm text-[#1D2B48]/70">Recettes actives :</span>
          {activeRecipes.map(recipe => (
            <Badge
              key={recipe}
              variant="secondary"
              className="text-xs bg-gradient-to-r from-[#8A78F2] to-[#F178B6] text-white border-0"
            >
              {recipe}
            </Badge>
          ))}
        </div>
      )}

      {/* Main input area */}
      <div
        className={cn(
          "relative rounded-2xl border-2 bg-white transition-all",
          isDragging ? "border-[#3898FF] bg-[#3898FF]/5" : "border-[#F3F5F9]",
          disabled && "opacity-50"
        )}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        {/* Attachments preview */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 p-3 border-b border-[#F3F5F9]">
            {attachments.map((file, index) => {
              const Icon = getFileIcon(file);
              return (
                <div
                  key={index}
                  className="flex items-center gap-2 px-3 py-1.5 bg-[#F3F5F9] rounded-lg group"
                >
                  <Icon className="h-4 w-4 text-[#1D2B48]/60" />
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-[#1D2B48] truncate max-w-[150px]">
                      {file.name}
                    </span>
                    <span className="text-xs text-[#1D2B48]/60">
                      {formatFileSize(file.size)}
                    </span>
                  </div>
                  {onRemoveAttachment && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={() => onRemoveAttachment(index)}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Input row */}
        <div className="flex items-end gap-2 p-3">
          <Button
            type="button"
            size="icon"
            variant="ghost"
            className="h-9 w-9 flex-shrink-0 hover:bg-[#3898FF]/10"
            disabled={disabled}
            onClick={() => fileInputRef.current?.click()}
          >
            <Paperclip className="h-4 w-4 text-[#1D2B48]/70" />
          </Button>

          <Textarea
            ref={textareaRef}
            value={input}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            className="min-h-[40px] max-h-[150px] resize-none border-0 bg-transparent px-0 py-2 text-[#1D2B48] placeholder:text-[#1D2B48]/40 focus-visible:ring-0 focus-visible:ring-offset-0"
            rows={1}
          />

          <Button
            onClick={handleSubmit}
            disabled={disabled || isLoading || (!input.trim() && attachments.length === 0)}
            size="icon"
            className="h-9 w-9 flex-shrink-0 rounded-lg bg-[#3898FF] hover:bg-[#3898FF]/90"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin text-white" />
            ) : (
              <Send className="h-4 w-4 text-white" />
            )}
          </Button>

          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleFileSelect}
            accept=".pdf,.txt,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
          />
        </div>

        {/* Drag overlay */}
        {isDragging && (
          <div className="absolute inset-0 flex items-center justify-center rounded-2xl bg-[#3898FF]/10 pointer-events-none">
            <div className="flex flex-col items-center gap-2">
              <Paperclip className="h-8 w-8 text-[#3898FF]" />
              <span className="text-sm font-medium text-[#3898FF]">
                Déposez vos fichiers ici
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Helper text */}
      <div className="mt-2 text-xs text-[#1D2B48]/40 text-center">
        Entrée pour envoyer • Maj+Entrée pour nouvelle ligne • Glissez-déposez des fichiers
      </div>
    </div>
  );
}