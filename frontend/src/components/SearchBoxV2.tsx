"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Send,
  Loader2,
  Mic,
  Paperclip,
  X,
  FileText,
  Image as ImageIcon,
  File
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SearchBoxV2Props {
  onSubmit: (question: string, attachments?: File[]) => void;
  isLoading?: boolean;
  placeholder?: string;
  className?: string;
  showAttachments?: boolean;
}

export function SearchBoxV2({
  onSubmit,
  isLoading = false,
  placeholder = "Posez votre question...",
  className,
  showAttachments = true,
}: SearchBoxV2Props) {
  const [question, setQuestion] = React.useState("");
  const [attachments, setAttachments] = React.useState<File[]>([]);
  const [isListening, setIsListening] = React.useState(false);
  const [isDragging, setIsDragging] = React.useState(false);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const recognitionRef = React.useRef<any>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if ((question.trim() || attachments.length > 0) && !isLoading) {
      onSubmit(question.trim(), attachments);
      setQuestion("");
      setAttachments([]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Auto-resize textarea
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  };

  React.useEffect(() => {
    adjustTextareaHeight();
  }, [question]);

  // Initialize speech recognition
  React.useEffect(() => {
    if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'fr-FR';

      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setQuestion(prev => prev + (prev ? ' ' : '') + transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const toggleVoiceRecording = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setAttachments(prev => [...prev, ...files]);
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
    if (files.length > 0) {
      setAttachments(prev => [...prev, ...files]);
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

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return ImageIcon;
    } else if (file.type.includes('pdf')) {
      return FileText;
    }
    return File;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  const canSubmit = (question.trim().length > 0 || attachments.length > 0) && !isLoading;

  return (
    <div className={cn("relative", className)}>
      <div
        className={cn(
          "rounded-2xl border-2 bg-white transition-all",
          isDragging ? "border-[#3898FF] bg-[#3898FF]/5" : "border-slate-200",
          "shadow-lg"
        )}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        {/* Attachments preview */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 p-3 border-b border-slate-200">
            {attachments.map((file, index) => {
              const Icon = getFileIcon(file);
              return (
                <div
                  key={index}
                  className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-lg group"
                >
                  <Icon className="h-4 w-4 text-[#3898FF]" />
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-slate-700 truncate max-w-[150px]">
                      {file.name}
                    </span>
                    <span className="text-xs text-slate-500">
                      {formatFileSize(file.size)}
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={() => removeAttachment(index)}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              );
            })}
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-4">
          <div className="flex items-end gap-2">
            {showAttachments && (
              <Button
                type="button"
                size="icon"
                variant="ghost"
                className="h-10 w-10 flex-shrink-0 hover:bg-[#3898FF]/10"
                disabled={isLoading}
                onClick={() => fileInputRef.current?.click()}
              >
                <Paperclip className="h-5 w-5 text-slate-600" />
              </Button>
            )}

            <div className="flex-1">
              <Textarea
                ref={textareaRef}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                disabled={isLoading}
                className="min-h-[44px] max-h-[150px] resize-none text-base border-0 focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 bg-transparent px-0 placeholder:text-slate-400"
                rows={1}
              />
            </div>

            <div className="flex gap-2">
              <Button
                type="button"
                onClick={toggleVoiceRecording}
                disabled={isLoading}
                className={cn(
                  "h-10 w-10 rounded-full p-0 flex items-center justify-center transition-all",
                  isListening
                    ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                )}
              >
                <Mic className="h-4 w-4" />
              </Button>

              <Button
                type="submit"
                disabled={!canSubmit}
                className="h-10 w-10 rounded-full bg-gradient-to-r from-[#3898FF] to-[#8A78F2] hover:opacity-90 text-white p-0 flex items-center justify-center shadow-md transition-all disabled:opacity-50"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </form>

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
  );
}