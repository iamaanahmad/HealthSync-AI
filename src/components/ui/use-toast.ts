// Simple toast hook for notifications
import { useState, useCallback } from 'react';

interface Toast {
  id: string;
  title: string;
  description?: string;
  variant?: 'default' | 'destructive';
}

let toastCount = 0;

export function toast({ title, description, variant = 'default' }: Omit<Toast, 'id'>) {
  // Simple console log for now - in a real app this would show a toast notification
  console.log(`Toast: ${title}${description ? ` - ${description}` : ''}`);
  
  // Mock toast behavior
  if (typeof window !== 'undefined') {
    const toastElement = document.createElement('div');
    toastElement.className = `fixed top-4 right-4 bg-white border rounded-lg shadow-lg p-4 z-50 max-w-sm ${
      variant === 'destructive' ? 'border-red-200 bg-red-50' : 'border-gray-200'
    }`;
    toastElement.innerHTML = `
      <div class="font-medium">${title}</div>
      ${description ? `<div class="text-sm text-gray-600 mt-1">${description}</div>` : ''}
    `;
    
    document.body.appendChild(toastElement);
    
    setTimeout(() => {
      if (document.body.contains(toastElement)) {
        document.body.removeChild(toastElement);
      }
    }, 3000);
  }
}

export function useToast() {
  return { toast };
}