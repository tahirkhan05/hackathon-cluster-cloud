import { type ClassValue, clsx } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatCLSTR(amount: number): string {
  return `${amount.toLocaleString()} CLSTR`;
}

export function formatDuration(hours: number): string {
  if (hours < 1) {
    return `${Math.round(hours * 60)} minutes`;
  }
  if (hours < 24) {
    return `${hours.toFixed(1)} hours`;
  }
  const days = Math.floor(hours / 24);
  const remainingHours = Math.round(hours % 24);
  return remainingHours > 0
    ? `${days} day${days > 1 ? 's' : ''} ${remainingHours}h`
    : `${days} day${days > 1 ? 's' : ''}`;
}

export function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  });
}

export function getStatusColor(status: string): string {
  const statusMap: Record<string, string> = {
    SUBMITTED: 'bg-blue-100 text-blue-700',
    ANALYZING: 'bg-purple-100 text-purple-700',
    SCHEDULING: 'bg-yellow-100 text-yellow-700',
    ALLOCATED: 'bg-cyan-100 text-cyan-700',
    RUNNING: 'bg-green-100 text-green-700',
    COMPLETED: 'bg-gray-100 text-gray-700',
    FAILED: 'bg-red-100 text-red-700',
    CANCELLED: 'bg-gray-100 text-gray-500',
    RECOVERING: 'bg-orange-100 text-orange-700',
    
    PENDING: 'bg-gray-100 text-gray-600',
    ASSIGNED: 'bg-blue-100 text-blue-600',
    RETRYING: 'bg-orange-100 text-orange-600',
    
    HEALTHY: 'bg-green-100 text-green-700',
    UNHEALTHY: 'bg-red-100 text-red-700',
    OFFLINE: 'bg-gray-100 text-gray-500',
    
    DETECTED: 'bg-red-100 text-red-700',
    RECOVERING: 'bg-yellow-100 text-yellow-700',
    RESOLVED: 'bg-green-100 text-green-700',
  };

  return statusMap[status] || 'bg-gray-100 text-gray-600';
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(1)} MB`;
  return `${(bytes / 1073741824).toFixed(1)} GB`;
}

export function calculateProgress(completed: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((completed / total) * 100);
}
