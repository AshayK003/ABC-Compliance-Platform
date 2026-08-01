import { useState, useEffect } from 'react';
import { api } from '../services/api';

type InspectionRecord = {
  id: string;
  centreName: string;
  centreCode: string;
  inspectorName: string;
  priority: string;
  type: string;
  scheduledAt: string;
};

export function Inspections() {
  const [records, setRecords] = useState<InspectionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedInspection, setSelectedInspection] = useState<InspectionRecord | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [inspectionData, centreData] = await Promise.all([
        api.getInspections(),
        api.getCentres().catch(() => [] as never[]),
      ]);
      const centreMap = new Map((centreData as Array<{ id: string; name: string; code: string }>).map(c => [c.id, c]));
      setRecords((inspectionData as Array<{
        id: string; centre_id: string; inspector_id: string; scheduled_at?: string; status: string;
      }>).map(i => ({
        id: i.id,
        centreName: centreMap.get(i.centre_id)?.name ?? i.centre_id,
        centreCode: centreMap.get(i.centre_id)?.code ?? '—',
        inspectorName: i.inspector_id,
        priority: i.status === 'overdue' ? 'OVERDUE' : i.status === 'completed' ? 'DONE' : 'SCHEDULED',
        type: 'Compliance Inspection',
        scheduledAt: i.scheduled_at ?? '',
      })));
    } catch (error) {
      console.error('Failed to load inspections:', error);
    } finally {
      setLoading(false);
    }
  };

  const todayRecords = records.filter(r => new Date(r.scheduledAt).toDateString() === new Date().toDateString());
  const tomorrowRecords = records.filter(r => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return new Date(r.scheduledAt).toDateString() === tomorrow.toDateString();
  });

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* TopAppBar */}
      <header className="bg-surface-container dark:bg-surface-container text-primary dark:text-primary font-body-md text-body-md border-b border-outline-variant dark:border-outline-variant flex justify-between items-center h-16 px-gutter shrink-0 z-10 w-full">
        <div className="flex items-center">
          <span className="text-headline-sm font-headline-sm font-black text-on-surface dark:text-on-surface tracking-tight">AWBI ABC Compliance</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 bg-surface-container-highest px-2 py-1 rounded border border-outline-variant" title="System synced 2 mins ago">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
            <span className="text-[11px] font-label-md text-on-surface-variant">Online & Synced</span>
          </div>
          <div className="flex items-center gap-2 border-l border-outline-variant pl-4 ml-2">
            <button className="p-2 text-on-surface-variant hover:text-primary transition-colors rounded hover:bg-surface-container-highest">
              <span className="material-symbols-outlined">notifications</span>
            </button>
            <button className="p-2 text-on-surface-variant hover:text-primary transition-colors rounded hover:bg-surface-container-highest">
              <span className="material-symbols-outlined">settings</span>
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-auto p-container-padding">
        <div className="flex justify-between items-end mb-6">
          <div>
            <h2 className="font-headline-md text-headline-md text-on-surface mb-1">Inspection Schedule</h2>
            <p className="font-body-sm text-body-sm text-on-surface-variant">Manage and execute compliance inspections for ABC centres.</p>
          </div>
          <div className="flex gap-2">
            <button className="px-4 py-2 border border-outline-variant rounded font-label-md text-label-md hover:bg-surface-container-highest transition-colors flex items-center gap-2">
              <span className="material-symbols-outlined text-[18px]">filter_list</span> Filter
            </button>
            <button className="px-4 py-2 border border-outline-variant rounded font-label-md text-label-md hover:bg-surface-container-highest transition-colors flex items-center gap-2">
              <span className="material-symbols-outlined text-[18px]">calendar_month</span> Month View
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100%-80px)] min-h-[600px]">
          {/* Left: Calendar / Schedule List */}
          <div className="lg:col-span-8 bg-surface-container rounded-lg border border-outline-variant flex flex-col overflow-hidden">
            <div className="p-4 border-b border-outline-variant bg-surface-container-high flex justify-between items-center">
              <h3 className="font-label-bold text-label-bold uppercase text-on-surface-variant tracking-wider">{new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</h3>
              <div className="flex gap-1">
                <button className="p-1 rounded hover:bg-secondary-container text-on-surface-variant"><span className="material-symbols-outlined text-[18px]">chevron_left</span></button>
                <button className="p-1 rounded hover:bg-secondary-container text-on-surface-variant"><span className="material-symbols-outlined text-[18px]">chevron_right</span></button>
              </div>
            </div>
            <div className="flex-1 overflow-auto p-4 space-y-3">
              {todayRecords.length > 0 && (
                <>
                  <div className="text-[11px] font-bold text-primary tracking-wider uppercase mb-2 mt-2">Today</div>
                  {todayRecords.map((record) => (
                    <div key={record.id} className="group relative bg-surface-container-highest border border-primary rounded p-3 flex gap-4 cursor-pointer hover:bg-secondary-container transition-colors" onClick={() => setSelectedInspection(record)}>
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-l"></div>
                      <div className="w-16 shrink-0 flex flex-col items-center justify-center border-r border-outline-variant pr-4">
                        <span className="font-label-bold text-on-surface">09:00</span>
                        <span className="text-[10px] text-on-surface-variant">AM</span>
                      </div>
                      <div className="flex-1 min-w-0 flex flex-col justify-center">
                        <div className="flex justify-between items-start mb-1">
                          <h4 className="font-label-bold text-on-surface truncate">{record.centreName}</h4>
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-error/10 text-error border border-error/20 whitespace-nowrap">{record.priority}</span>
                        </div>
                        <p className="text-[11px] text-on-surface-variant truncate">{record.type}</p>
                      </div>
                      <div className="shrink-0 flex items-center">
                        <span className="material-symbols-outlined text-primary group-hover:translate-x-1 transition-transform">arrow_forward</span>
                      </div>
                    </div>
                  ))}
                </>
              )}

              {tomorrowRecords.length > 0 && (
                <>
                  <div className="text-[11px] font-bold text-on-surface-variant tracking-wider uppercase mb-2 mt-6">Tomorrow</div>
                  {tomorrowRecords.map((record) => (
                    <div key={record.id} className="bg-surface-container border border-outline-variant rounded p-3 flex gap-4 cursor-pointer hover:bg-surface-container-highest transition-colors" onClick={() => setSelectedInspection(record)}>
                      <div className="w-16 shrink-0 flex flex-col items-center justify-center border-r border-outline-variant pr-4 opacity-70">
                        <span className="font-label-bold text-on-surface">10:00</span>
                        <span className="text-[10px] text-on-surface-variant">AM</span>
                      </div>
                      <div className="flex-1 min-w-0 flex flex-col justify-center opacity-70">
                        <div className="flex justify-between items-start mb-1">
                          <h4 className="font-label-bold text-on-surface truncate">{record.centreName}</h4>
                        </div>
                        <p className="text-[11px] text-on-surface-variant truncate">{record.type}</p>
                      </div>
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>

          {/* Right: Inspection Detail Card */}
          <div className="lg:col-span-4 flex flex-col gap-4">
            <div className="bg-surface-container rounded-lg border border-outline-variant flex flex-col flex-1 relative overflow-hidden">
              <div className="h-1 w-full bg-gradient-to-r from-primary to-surface-tint"></div>
              <div className="p-5 flex-1 flex flex-col">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <div className="text-[10px] text-on-surface-variant uppercase tracking-wider mb-1">Selected Inspection</div>
                    <h3 className="font-headline-sm text-headline-sm text-on-surface">
                      {selectedInspection?.centreName || 'Select an inspection'}
                    </h3>
                  </div>
                  <span className="px-2 py-1 bg-surface-container-highest rounded border border-outline-variant text-[10px] font-mono text-on-surface-variant">
                    ID: {selectedInspection?.id || '—'}
                  </span>
                </div>
                <div className="space-y-4 flex-1">
                  <div>
                    <div className="text-[11px] text-on-surface-variant mb-1">Address</div>
                    <div className="font-body-sm text-body-sm text-on-surface flex items-start gap-2">
                      <span className="material-symbols-outlined text-[16px] text-primary shrink-0 mt-0.5">location_on</span>
                      <span>{selectedInspection?.centreCode || '42 Industrial Estate Road, Sector 5<br/>North District, 110042'}</span>
                    </div>
                  </div>
                  <div className="h-px w-full bg-outline-variant/50"></div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-[11px] text-on-surface-variant mb-1">Scheduled Date</div>
                      <div className="font-body-sm text-body-sm text-on-surface">
                        {selectedInspection?.scheduledAt ? new Date(selectedInspection.scheduledAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) + ' • ' + new Date(selectedInspection.scheduledAt).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) : 'Oct 24, 2024 • 09:00 AM'}
                      </div>
                    </div>
                    <div>
                      <div className="text-[11px] text-on-surface-variant mb-1">Assigned Officer</div>
                      <div className="font-body-sm text-body-sm text-on-surface">{selectedInspection?.inspectorName || 'Inspector Dan'}</div>
                    </div>
                  </div>
                  <div className="h-px w-full bg-outline-variant/50"></div>
                  <div>
                    <div className="text-[11px] text-on-surface-variant mb-2">Pre-Inspection Context</div>
                    <div className="bg-surface-container-lowest border border-outline-variant rounded p-3 grid grid-cols-2 gap-2">
                      <div>
                        <div className="text-[10px] text-on-surface-variant uppercase">Last Surgeries</div>
                        <div className="font-headline-sm text-primary">142 <span className="text-[10px] text-on-surface-variant font-normal">/mo</span></div>
                      </div>
                      <div>
                        <div className="text-[10px] text-on-surface-variant uppercase">Previous Rating</div>
                        <div className="font-label-bold text-yellow-500 flex items-center gap-1 mt-1">
                          <span className="material-symbols-outlined text-[14px]">warning</span> Needs Imp.
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="mt-6 pt-4 border-t border-outline-variant">
                  <button className="w-full py-3 bg-yellow-500 hover:bg-yellow-600 text-white font-label-bold rounded transition-colors flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(249,115,22,0.2)]">
                    <span className="material-symbols-outlined icon-fill">play_circle</span> START INSPECTION
                  </button>
                  <p className="text-[10px] text-center text-on-surface-variant mt-2">Entering inspection mode will lock device location.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}