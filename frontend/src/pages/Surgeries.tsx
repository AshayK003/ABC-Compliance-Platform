import { useState, useEffect } from 'react';
import { DataTable } from '../components/DataTable';
import { StatCard } from '../components/StatCard';
import { 
  type SurgeryRecord, 
  type SurgerySummary,
  MOCK_SURGERY_SUMMARY,
  MOCK_SURGERIES
} from '../mocks';

export function Surgeries() {
  const [records, setRecords] = useState<SurgeryRecord[]>([]);
  const [summary, setSummary] = useState<SurgerySummary>(MOCK_SURGERY_SUMMARY);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setSummary(MOCK_SURGERY_SUMMARY);
      setRecords(MOCK_SURGERIES);
    } catch (error) {
      console.error('Failed to load surgeries:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <header className="md:hidden flex justify-between items-center h-16 px-gutter w-full sticky top-0 z-40 border-b border-outline-variant bg-surface-container">
        <div className="flex items-center gap-4">
          <span className="material-symbols-outlined text-primary cursor-pointer" data-icon="menu">menu</span>
          <span className="font-headline-md text-headline-md font-bold text-primary">ABC Digital Compliance</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="material-symbols-outlined text-on-surface-variant cursor-pointer">notifications</span>
          <span className="material-symbols-outlined text-on-surface-variant cursor-pointer">settings</span>
        </div>
      </header>

      <main className="flex-1 flex flex-col min-w-0 p-container-padding space-y-6">
        {/* Header & Controls */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="font-display-lg text-display-lg text-on-background">Surgery Audit Log</h1>
            <p className="font-body-md text-body-md text-on-surface-variant mt-1">Detailed view of animal surgeries performed across compliant centres.</p>
          </div>
          <div className="flex items-center gap-2 bg-surface-container-high border border-outline-variant rounded p-2">
            <span className="material-symbols-outlined text-on-surface-variant" data-icon="calendar_month">calendar_month</span>
            <span className="font-label-bold text-label-bold text-on-surface">Oct 01, 2023 - Oct 31, 2023</span>
            <span className="material-symbols-outlined text-on-surface-variant cursor-pointer ml-2" data-icon="arrow_drop_down">arrow_drop_down</span>
          </div>
        </div>

        {/* Summary Section (Bento Grid) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-element-gap">
          <StatCard label="Total Surgeries" value={summary.total.toLocaleString()} trend="+12%" trendColor="primary" />
          <StatCard label="Pre-op" value={summary.preOp.toLocaleString()} trend="Active" trendColor="primary" />
          <StatCard label="Post-op / Recovering" value={summary.postOp.toLocaleString()} trend="Cleared" trendColor="secondary" />
          <StatCard label="Complications" value={summary.complications.toLocaleString()} trend="Flagged" trendColor="error" />
        </div>

        {/* Detailed List/Table */}
        <div className="bg-surface-container-high border border-outline-variant rounded overflow-hidden flex-1 flex flex-col">
          <div className="p-4 border-b border-outline-variant flex justify-between items-center bg-surface-container">
            <h2 className="font-headline-sm text-headline-sm text-on-surface">Surgery Records</h2>
            <div className="flex gap-2">
              <button className="bg-surface-container-highest border border-outline-variant text-on-surface px-3 py-1 rounded font-label-bold text-label-bold flex items-center gap-2 hover:bg-surface-variant transition-colors">
                <span className="material-symbols-outlined text-sm" data-icon="filter_list">filter_list</span> Filter
              </button>
              <button className="bg-surface-container-highest border border-outline-variant text-on-surface px-3 py-1 rounded font-label-bold text-label-bold flex items-center gap-2 hover:bg-surface-variant transition-colors">
                <span className="material-symbols-outlined text-sm" data-icon="download">download</span> Export
              </button>
            </div>
          </div>
          <div className="overflow-x-auto flex-1">
            <DataTable
              data={records}
              columns={[
                { key: 'date', header: 'Date' },
                { key: 'centreName', header: 'Centre Name', render: (r: SurgeryRecord) => <span>{r.centreName} ({r.centreCode})</span> },
                { key: 'animalId', header: 'Animal ID', render: (r: SurgeryRecord) => <span className="font-code-sm text-code-sm text-tertiary">{r.animalId}</span> },
                { key: 'procedureType', header: 'Procedure Type' },
                {
                  key: 'outcome',
                  header: 'Outcome',
                  render: (r: SurgeryRecord) => (
                    <span className={`inline-flex items-center px-2 py-1 rounded ${
                      r.outcome === 'Recovered' ? 'bg-primary/10 text-primary font-label-bold text-label-bold' :
                      r.outcome === 'In Observation' ? 'bg-secondary-container text-on-secondary-container font-label-bold text-label-bold' :
                      'bg-error-container text-on-error-container font-label-bold text-label-bold'
                    }`}>
                      {r.outcome}
                    </span>
                  ),
                },
                { key: 'actions', header: 'Actions', align: 'right', render: () => <button className="text-on-surface-variant hover:text-primary"><span className="material-symbols-outlined text-[20px]" data-icon="more_vert">more_vert</span></button> },
              ]}
            />
          </div>
          <div className="p-4 border-t border-outline-variant flex justify-between items-center bg-surface-container text-on-surface-variant font-label-md text-label-md">
            <span>Showing 1-6 of 1,248 records</span>
            <div className="flex items-center gap-2">
              <button className="material-symbols-outlined hover:text-on-surface cursor-pointer" data-icon="chevron_left">chevron_left</button>
              <span className="text-on-surface">1</span>
              <span>/</span>
              <span>312</span>
              <button className="material-symbols-outlined hover:text-on-surface cursor-pointer" data-icon="chevron_right">chevron_right</button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}