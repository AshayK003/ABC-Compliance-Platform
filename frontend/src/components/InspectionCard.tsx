export interface InspectionCardProps {
  readonly centreName: string;
  readonly scheduledAt: string;
  readonly status: 'Scheduled' | 'Completed' | 'Overdue';
}

export function InspectionCard({ centreName, scheduledAt, status }: InspectionCardProps) {
  const statusConfig = {
    Scheduled: { bg: 'bg-secondary-container/50', text: 'text-secondary', label: 'Scheduled', border: '' },
    Completed: { bg: 'bg-primary-container/20', text: 'text-primary', label: 'Completed', border: 'border-primary/30' },
    Overdue: { bg: 'bg-error-container/20', text: 'text-error', label: 'Overdue', border: 'border-error/30' },
  };

  const config = statusConfig[status];

  return (
    <div className={`bg-surface-container border border-outline-variant/50 p-3 rounded flex justify-between items-center ${config.border}`}>
      <div>
        <p className="font-label-bold text-label-bold text-on-surface">{centreName}</p>
        <p className="font-label-md text-label-md text-on-surface-variant mt-1">
          {scheduledAt ? new Date(scheduledAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'TBD'}
        </p>
      </div>
      <span className={`px-2 py-1 rounded ${config.bg} ${config.text} text-label-md ${config.border}`}>
        {config.label}
      </span>
    </div>
  );
}