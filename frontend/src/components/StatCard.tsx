export interface StatCardProps {
  label: string;
  value: string;
  trend?: string;
  trendColor?: 'primary' | 'error' | 'secondary' | 'tertiary';
}

function getTrendIcon(trend: string): string {
  if (trend.startsWith('+')) return 'trending_up';
  if (trend.startsWith('-')) return 'trending_down';
  return 'trending_flat';
}

export function StatCard({ label, value, trend, trendColor = 'primary' }: StatCardProps) {
  return (
    <div className="bg-surface-container-high border border-outline-variant rounded-lg p-4 flex flex-col justify-between">
      <span className="font-label-bold text-label-bold text-on-surface-variant uppercase tracking-wider">{label}</span>
      <div className="mt-4 flex items-baseline justify-between gap-2">
        <span className="font-display-lg text-display-lg text-on-surface">{value}</span>
        {trend && (
          <span className={`font-label-bold text-label-bold text-${trendColor} flex items-center`}>
            <span className="material-symbols-outlined text-sm">{getTrendIcon(trend)}</span>
            {trend}
          </span>
        )}
      </div>
    </div>
  );
}