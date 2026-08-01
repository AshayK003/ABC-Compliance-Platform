import { useState, useEffect } from 'react';
import { DataTable } from '../components/DataTable';
import { CentreFormModal } from '../components/CentreFormModal';
import type { Centre } from '../types';
import { api } from '../services/api';

export function Centres() {
  const [centres, setCentres] = useState<Centre[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [districtFilter, setDistrictFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    loadCentres();
  }, []);

  const loadCentres = async () => {
    try {
      const data = await api.getCentres();
      setCentres(data);
    } catch (error) {
      console.error('Failed to load centres:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCentre = async (data: { name: string; code: string; district: string; state: string; capacity?: number }) => {
    try {
      await api.createCentre(data);
      setModalOpen(false);
      await loadCentres();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create centre';
      alert(message);
    }
  };

  const filteredCentres = centres.filter(centre => {
    const matchesSearch = centre.name.toLowerCase().includes(search.toLowerCase()) ||
      centre.code.toLowerCase().includes(search.toLowerCase()) ||
      centre.district.toLowerCase().includes(search.toLowerCase());
    const matchesDistrict = !districtFilter || centre.district === districtFilter;
    const matchesStatus = !statusFilter || centre.status === statusFilter;
    return matchesSearch && matchesDistrict && matchesStatus;
  });

  const districts = [...new Set(centres.map(c => c.district))].sort((a, b) => a.localeCompare(b));
  const statuses = ['active', 'inactive', 'suspended'];

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* Page Header */}
      <header className="bg-surface-container dark:bg-surface-container w-full sticky top-0 z-40 border-b border-outline-variant flex justify-between items-center h-16 px-gutter shrink-0">
        <h1 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Registered Centres Directory</h1>
        <button onClick={() => setModalOpen(true)} className="bg-primary hover:bg-primary-container text-on-primary font-label-bold text-label-bold px-4 py-2.5 rounded transition-colors flex items-center justify-center gap-2 w-full lg:w-auto shrink-0 shadow-sm">
          <span className="material-symbols-outlined text-[18px]">add</span>
          Add New Centre
        </button>
      </header>

      {/* Filters */}
      <div className="flex-1 overflow-y-auto p-container-padding">
        <div className="bg-surface-container rounded-lg border border-outline-variant p-4 mb-6 flex flex-col md:flex-row gap-4 items-end">
          <div className="w-full md:w-1/3">
            <label className="block font-label-md text-label-md text-on-surface-variant mb-1">Search Facility</label>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">search</span>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-background border border-outline-variant rounded pl-10 pr-3 py-2 text-on-surface font-body-sm text-body-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-outline"
                placeholder="Centre name, ID, or location..."
              />
            </div>
          </div>
          <div className="w-full md:w-1/4">
            <label className="block font-label-md text-label-md text-on-surface-variant mb-1">District</label>
            <div className="relative">
              <select
                value={districtFilter}
                onChange={(e) => setDistrictFilter(e.target.value)}
                className="w-full bg-background border border-outline-variant rounded pl-3 pr-8 py-2 text-on-surface font-body-sm text-body-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none appearance-none cursor-pointer"
              >
                <option value="">All Districts</option>
                {districts.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
              <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none text-[18px]">arrow_drop_down</span>
            </div>
          </div>
          <div className="w-full md:w-1/4">
            <label className="block font-label-md text-label-md text-on-surface-variant mb-1">Operating Status</label>
            <div className="relative">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full bg-background border border-outline-variant rounded pl-3 pr-8 py-2 text-on-surface font-body-sm text-body-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none appearance-none cursor-pointer"
              >
                <option value="">All Statuses</option>
                {statuses.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none text-[18px]">arrow_drop_down</span>
            </div>
          </div>
          <button className="w-full md:w-auto bg-surface-container-high border border-outline-variant hover:border-outline text-on-surface font-label-bold text-label-bold px-4 py-2 rounded transition-colors flex items-center justify-center gap-2 h-[38px]">
            <span className="material-symbols-outlined text-[18px]">filter_list</span>
            More Filters
          </button>
        </div>

        {/* Table */}
        <div className="bg-surface-container rounded-lg border border-outline-variant overflow-hidden flex flex-col">
          <div className="overflow-x-auto">
            <DataTable
              data={filteredCentres}
              columns={[
                { key: 'code', header: 'ID', align: 'center', render: (c: Centre) => <span className="font-code-sm text-outline">{c.code}</span> },
                {
                  key: 'name',
                  header: 'Centre Name',
                  render: (c: Centre) => (
                    <div>
                      <div className="font-medium text-on-surface">{c.name}</div>
                      <div className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">Gov Operated • Type A</div>
                    </div>
                  ),
                },
                { key: 'district', header: 'Location / District', render: (c: Centre) => `${c.district}, ${c.state}` },
                { key: 'capacity', header: 'Capacity (Monthly)', align: 'right', render: (c: Centre) => <span className="font-code-sm">{c.capacity}</span> },
                {
                  key: 'status',
                  header: 'Status',
                  align: 'center',
                  render: (c: Centre) => (
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold tracking-wide uppercase ${c.status === 'active' ? 'bg-primary-container/10 text-primary border border-primary/20' : c.status === 'inactive' ? 'bg-error/10 text-error border border-error/20' : 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20'}`}>
                      {c.status}
                    </span>
                  ),
                },
                {
                  key: 'complianceScore',
                  header: 'Compliance Score',
                  align: 'center',
                  render: (c: Centre) => (
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-16 h-1.5 bg-surface-container rounded-full overflow-hidden">
                        <div className="h-full bg-primary w-[92%] rounded-full"></div>
                      </div>
                      <span className="font-code-sm text-primary">{c.complianceScore}/100</span>
                    </div>
                  ),
                },
                {
                  key: 'actions',
                  header: 'Actions',
                  align: 'right',
                  render: () => (
                    <button className="text-on-surface-variant hover:text-primary p-1 rounded transition-colors">
                      <span className="material-symbols-outlined text-[20px]">visibility</span>
                    </button>
                  ),
                },
              ]}
            />
          </div>

          {/* Pagination */}
          <div className="bg-surface-container-highest border-t border-outline-variant px-4 py-3 flex items-center justify-between">
            <div className="font-body-sm text-body-sm text-on-surface-variant">Showing <span className="font-medium text-on-surface">1</span> to <span className="font-medium text-on-surface">{filteredCentres.length}</span> of <span className="font-medium text-on-surface">{centres.length}</span> entries</div>
            <div className="flex items-center gap-1">
              <button className="p-1 rounded text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                <span className="material-symbols-outlined text-[20px]">chevron_left</span>
              </button>
              <button className="w-8 h-8 rounded bg-primary/20 text-primary font-label-md text-label-md flex items-center justify-center border border-primary/30">1</button>
              <button className="w-8 h-8 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface font-label-md text-label-md flex items-center justify-center transition-colors">2</button>
              <button className="w-8 h-8 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface font-label-md text-label-md flex items-center justify-center transition-colors">3</button>
              <span className="w-8 h-8 flex items-center justify-center text-on-surface-variant">...</span>
              <button className="w-8 h-8 rounded hover:bg-surface-container text-on-surface-variant hover:text-on-surface font-label-md text-label-md flex items-center justify-center transition-colors">12</button>
              <button className="p-1 rounded text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors">
                <span className="material-symbols-outlined text-[20px]">chevron_right</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {modalOpen && (
        <CentreFormModal
          centre={null}
          onClose={() => setModalOpen(false)}
          onSubmit={handleCreateCentre}
        />
      )}
    </div>
  );
}