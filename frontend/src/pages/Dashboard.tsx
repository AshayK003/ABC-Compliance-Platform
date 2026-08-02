import { useState, useEffect } from 'react';
import { StatCard } from '../components/StatCard';
import { InspectionCard } from '../components/InspectionCard';
import { ChartPlaceholder } from '../components/ChartPlaceholder';
import { api } from '../services/api';

type CentreSummary = {
  id: string;
  name: string;
  code: string;
  district: string;
  state: string;
  capacity: number;
  status: 'active' | 'inactive' | 'suspended';
  complianceScore: number;
  surgeriesThisMonth: number;
};

type AlertItem = {
  centre: string;
  district: string;
  issue: string;
  status: 'Critical' | 'Warning' | 'Resolved';
};

export function Dashboard() {
  const [centres, setCentres] = useState<CentreSummary[]>([]);
  const [upcomingInspections, setUpcomingInspections] = useState<Array<{
    centreName: string;
    scheduledAt: string;
    status: 'Scheduled' | 'Completed' | 'Overdue';
  }>>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [totalDisbursed, setTotalDisbursed] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [centreData, inspectionData, complaintData, surgeryData, allocationData] = await Promise.all([
        api.getCentres({ limit: 100 }),
        api.getInspections(),
        api.getComplaints().catch(() => [] as never[]),
        api.getSurgeries().catch(() => [] as never[]),
        api.getAllocations().catch(() => [] as never[]),
      ]);

      const totalDisbursed = (allocationData as Array<{ amount: number }>)
        .reduce((sum, a) => sum + (a.amount ?? 0), 0);
      setTotalDisbursed(totalDisbursed);

      const centreMap = new Map(centreData.map(c => [c.id, c]));

      const monthStart = new Date();
      monthStart.setDate(1);
      monthStart.setHours(0, 0, 0, 0);

      const surgeryCounts = new Map<string, number>();
      for (const s of surgeryData as Array<{ centre_id: string; timestamp?: string }>) {
        const ts = s.timestamp ? new Date(s.timestamp) : null;
        if (ts && ts >= monthStart) {
          surgeryCounts.set(s.centre_id, (surgeryCounts.get(s.centre_id) ?? 0) + 1);
        }
      }

      const completedInspections = new Set(
        (inspectionData as Array<{ centre_id: string; status: string }>)
          .filter(i => i.status === 'completed')
          .map(i => i.centre_id),
      );

      const summaries: CentreSummary[] = centreData.map(c => ({
        id: c.id,
        name: c.name,
        code: c.code,
        district: c.district,
        state: c.state,
        capacity: c.capacity ?? 0,
        status: c.status,
        complianceScore: completedInspections.has(c.id) ? 100 : 0,
        surgeriesThisMonth: surgeryCounts.get(c.id) ?? 0,
      }));

      setCentres(summaries);
      setUpcomingInspections(
        inspectionData
          .filter(i => i.status === 'scheduled')
          .slice(0, 5)
          .map(i => ({
            centreName: centreMap.get(i.centre_id)?.name ?? i.centre_id,
            scheduledAt: i.scheduled_at ?? 'Not scheduled',
            status: 'Scheduled' as const,
          })),
      );
      setAlerts(
        (complaintData as Array<{ centre_id: string; description: string; status: string }>)
          .filter(c => c.status === 'open' || c.status === 'in_progress')
          .slice(0, 5)
          .map(c => ({
            centre: centreMap.get(c.centre_id)?.name ?? c.centre_id,
            district: centreMap.get(c.centre_id)?.district ?? '—',
            issue: c.description,
            status: c.status === 'open' ? 'Critical' as const : 'Warning' as const,
          })),
      );
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  function getAlertStatusColor(status: AlertItem['status']): string {
  if (status === 'Critical') return 'bg-error';
  if (status === 'Warning') return 'bg-yellow-500';
  return 'bg-primary';
}

function getAlertStatusTextColor(status: AlertItem['status']): string {
  if (status === 'Critical') return 'text-error';
  if (status === 'Warning') return 'text-yellow-500';
  return 'text-primary';
}

if (loading) {
  return (
    <div className="flex h-screen items-center justify-center bg-background">
      <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
    </div>
  );
}

const topCentres = centres
    .filter(c => c.status === 'active')
    .sort((a, b) => b.surgeriesThisMonth - a.surgeriesThisMonth)
    .slice(0, 10);

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* TopAppBar */}
      <header className="flex justify-between items-center h-16 px-gutter bg-surface-container dark:bg-surface-container border-b border-outline-variant dark:border-outline-variant z-10 shrink-0">
        <div className="flex items-center gap-4">
          <h2 className="text-headline-sm font-headline-sm font-black text-on-surface dark:text-on-surface">AWBI ABC Compliance</h2>
        </div>
        <div className="flex items-center gap-4 text-on-surface-variant">
          <button type="button" className="hover:text-primary dark:hover:text-primary transition-opacity duration-150 p-2 rounded-full hover:bg-surface-variant">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <button type="button" className="hover:text-primary dark:hover:text-primary transition-opacity duration-150 p-2 rounded-full hover:bg-surface-variant">
            <span className="material-symbols-outlined">settings</span>
          </button>
          <div className="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center cursor-pointer">
            <span className="material-symbols-outlined text-on-primary-container icon-fill text-lg">person</span>
          </div>
        </div>
      </header>

      {/* Canvas */}
      <main className="flex-1 overflow-y-auto p-container-padding bg-background">
        <div className="max-w-7xl mx-auto flex flex-col gap-container-padding">
          {/* Stat Cards */}
          <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-gutter">
            <StatCard
              label="Total ABC Centres"
              value={String(centres.length)}
              trend="+3%"
              trendColor="primary"
            />
            <StatCard
              label="Surgeries This Month"
              value={String(centres.reduce((sum, c) => sum + c.surgeriesThisMonth, 0))}
              trend="+12%"
              trendColor="primary"
            />
            <StatCard
              label="Compliance >90%"
              value={`${centres.filter(c => c.complianceScore >= 90).length}/${centres.length}`}
              trend="-2%"
              trendColor="error"
            />
            <StatCard
              label="Funds Disbursed"
              value={totalDisbursed >= 1_0000_0000
                ? `₹${(totalDisbursed / 1_0000_0000).toFixed(1)} Cr`
                : `₹${(totalDisbursed / 100000).toFixed(1)} L`}
              trend="On Track"
              trendColor="primary"
            />
          </section>

          {/* Middle Section: Chart + Upcoming Inspections */}
          <section className="grid grid-cols-1 lg:grid-cols-3 gap-gutter">
            {/* Left: Chart Area */}
            <div className="lg:col-span-2 bg-surface-container-high border border-outline-variant rounded-lg p-6 flex flex-col">
              <h3 className="font-headline-sm text-headline-sm mb-4">Surgeries per Centre — Last 30 Days</h3>
              <ChartPlaceholder height="300px">
                <div className="flex-1 bg-surface-container-lowest border border-outline-variant/50 rounded flex items-end p-4 gap-2 min-h-[300px] w-full">
                  {topCentres.map((centre) => {
                    const maxSurgeries = Math.max(...topCentres.map(c => c.surgeriesThisMonth));
                    const heightPct = Math.max(10, (centre.surgeriesThisMonth / maxSurgeries) * 90);
                    return (
                      <div
                        key={centre.id}
                        className="flex-1 bg-primary/20 hover:bg-primary/40 transition-colors rounded-t border-t border-primary relative group chart-bar"
                        style={{ '--target-h': `${heightPct}%` } as React.CSSProperties}
                      >
                        <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 bg-surface-variant text-on-surface text-label-md px-2 py-1 rounded pointer-events-none">
                          {centre.surgeriesThisMonth}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ChartPlaceholder>
              <div className="flex justify-between mt-2 text-label-md text-on-surface-variant">
                <span>Top Performing Centres</span>
                <span>Scale: 0 - {Math.max(...topCentres.map(c => c.surgeriesThisMonth))}</span>
              </div>
            </div>

            {/* Right: Upcoming Inspections */}
            <div className="bg-surface-container-high border border-outline-variant rounded-lg p-6 flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-headline-sm text-headline-sm">Upcoming Surprise Inspections</h3>
                <button type="button" className="text-primary hover:text-primary-fixed transition-colors">
                  <span className="material-symbols-outlined">arrow_forward</span>
                </button>
              </div>
              <div className="flex flex-col gap-3">
                {upcomingInspections.map((inspection) => (
                                  <InspectionCard
                                    key={inspection.centreName + inspection.scheduledAt}
                    centreName={inspection.centreName}
                    scheduledAt={inspection.scheduledAt}
                    status={inspection.status}
                  />
                ))}
              </div>
            </div>
          </section>

          {/* Bottom Section: Alerts Table */}
          <section className="bg-surface-container-high border border-outline-variant rounded-lg overflow-hidden">
            <div className="p-6 border-b border-outline-variant">
              <h3 className="font-headline-sm text-headline-sm">Recent Compliance Alerts</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-container border-b border-outline-variant text-on-surface-variant font-label-bold text-label-bold uppercase tracking-wider">
                    <th className="p-table-cell-padding">Centre</th>
                    <th className="p-table-cell-padding">District</th>
                    <th className="p-table-cell-padding">Issue Description</th>
                    <th className="p-table-cell-padding">Status</th>
                  </tr>
                </thead>
                <tbody className="text-body-md">
                  {alerts.map((alert) => (
                    <tr key={alert.centre + alert.district + alert.issue} className="border-b border-outline-variant/50 hover:bg-surface-variant/30 transition-colors">
                      <td className="p-table-cell-padding font-medium text-on-surface">{alert.centre}</td>
                      <td className="p-table-cell-padding text-on-surface-variant">{alert.district}</td>
                      <td className="p-table-cell-padding text-on-surface-variant">{alert.issue}</td>
                      <td className="p-table-cell-padding">
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${getAlertStatusColor(alert.status)}`}></div>
                          <span className={getAlertStatusTextColor(alert.status)}>
                            {alert.status}
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}