import { cn } from '@/lib/utils';

interface ProgressBarProps {
  value: number;
  max?: number;
  className?: string;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function ProgressBar({
  value,
  max = 100,
  className,
  showLabel = false,
  size = 'md',
}: ProgressBarProps) {
  const percentage = Math.min((value / max) * 100, 100);

  const sizes = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  return (
    <div className={cn('w-full', className)}>
      <div className="flex items-center gap-2">
        <div
          className={cn(
            'flex-1 bg-gray-200 rounded-full overflow-hidden',
            sizes[size]
          )}
        >
          <div
            className="bg-primary-600 h-full transition-all duration-500 ease-out"
            style={{ width: `${percentage}%` }}
          />
        </div>
        {showLabel && (
          <span className="text-sm font-medium text-gray-700 min-w-[3rem] text-right">
            {Math.round(percentage)}%
          </span>
        )}
      </div>
    </div>
  );
}
