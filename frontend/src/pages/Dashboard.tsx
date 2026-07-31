import { useState, useEffect } from 'react';
import { StatCard } from '../components/StatCard';
import { InspectionCard } from '../components/InspectionCard';
import { ChartPlaceholder } from '../components/ChartPlaceholder';

interface CentreSummary {
  id: string;
  name: string;
  code: string;
  district: string;
  state: string;
  capacity: number;
  status: 'active' | 'inactive' | 'suspended';
  complianceScore: number;
  surgeriesThisMonth: number;
}

interface AlertItem {
  centre: string;
  district: string;
  issue: string;
  status: 'Critical' | 'Warning' | 'Resolved';
}

export function Dashboard() {
  const [centres, setCentres] = useState<CentreSummary[]>([]);
  const [upcomingInspections, setUpcomingInspections] = useState<Array<{
    centreName: string;
    scheduledAt: string;
    status: 'Scheduled' | 'Completed' | 'Overdue';
  }>>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      // In a real app, these would be API calls
      // For now, using mock data that matches the HTML designs
      setCentres([
        { id: '1', name: 'Metro North ABC Hub', code: 'MNAH-001', district: 'North District', state: 'State', capacity: 450, status: 'active', complianceScore: 92, surgeriesThisMonth: 245 },
        { id: '2', name: 'Southside Animal Welfare', code: 'SAW-002', district: 'South District', state: 'State', capacity: 200, status: 'active', complianceScore: 78, surgeriesThisMonth: 180 },
        { id: '3', name: 'East Valley ABC Clinic', code: 'EVAC-003', district: 'East District', state: 'State', capacity: 150, status: 'inactive', complianceScore: 45, surgeriesThisMonth: 0 },
        { id: '4', name: 'West End Veterinary Trust', code: 'WEVT-004', district: 'West District', state: 'State', capacity: 500, status: 'active', complianceScore: 98, surgeriesThisMonth: 320 },
      ]);

      setUpcomingInspections([
        { centreName: 'Apex Care Centre', scheduledAt: '2023-10-24', status: 'Scheduled' },
        { centreName: 'Metro Paws ABC', scheduledAt: '2023-10-22', status: 'Completed' },
        { centreName: 'City Ward 4 Clinic', scheduledAt: '2023-10-15', status: 'Overdue' },
        { centreName: 'North District Hub', scheduledAt: '2023-11-02', status: 'Scheduled' },
      ]);

      setAlerts([
        { centre: 'Southside ABC', district: 'District 2', issue: 'Post-op care protocol violation reported.', status: 'Critical' },
        { centre: 'East Valley Shelter', district: 'District 5', issue: 'Delayed monthly surgery reporting.', status: 'Warning' },
        { centre: 'Central Gov ABC', district: 'District 1', issue: 'Minor infrastructure gap identified during inspection.', status: 'Resolved' },
      ]);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

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
          <button className="hover:text-primary dark:hover:text-primary transition-opacity duration-150 p-2 rounded-full hover:bg-surface-variant">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <button className="hover:text-primary dark:hover:text-primary transition-opacity duration-150 p-2 rounded-full hover:bg-surface-variant">
            <span className="material-symbols-outlined">settings</span>
          </button>
          <div className="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center cursor-pointer">
            <img alt="User Avatar" className="w-full h-full object-cover rounded-full" src="" />
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
              value="₹12.5 Cr"
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
                  {topCentres.map((centre) => (
                    <div
                      key={centre.id}
                      className="flex-1 bg-primary/20 hover:bg-primary/40 transition-colors rounded-t border-t border-primary relative group"
                      style={{ height: `${Math.max(10, (centre.surgeriesThisMonth / Math.max(...topCentres.map(c => c.surgeriesThisMonth))) * 90)}%` }}
                    >
                      <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 bg-surface-variant text-on-surface text-label-md px-2 py-1 rounded pointer-events-none">
                        {centre.surgeriesThisMonth}
                      </div>
                    </div>
                  ))}
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
                <button className="text-primary hover:text-primary-fixed transition-colors">
                  <span className="material-symbols-outlined">arrow_forward</span>
                </button>
              </div>
              <div className="flex flex-col gap-3">
                {upcomingInspections.map((inspection, index) => (
                  <InspectionCard
                    key={index}
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
                  {alerts.map((alert, index) => (
                    <tr key={index} className="border-b border-outline-variant/50 hover:bg-surface-variant/30 transition-colors">
                      <td className="p-table-cell-padding font-medium text-on-surface">{alert.centre}</td>
                      <td className="p-table-cell-padding text-on-surface-variant">{alert.district}</td>
                      <td className="p-table-cell-padding text-on-surface-variant">{alert.issue}</td>
                      <td className="p-table-cell-padding">
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${alert.status === 'Critical' ? 'bg-error' : alert.status === 'Warning' ? 'bg-yellow-500' : 'bg-primary'}`}></div>
                          <span className={alert.status === 'Critical' ? 'text-error' : alert.status === 'Warning' ? 'text-yellow-500' : 'text-primary'}>
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