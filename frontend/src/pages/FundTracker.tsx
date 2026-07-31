import { useState, useEffect } from 'react';
import { DataTable } from '../components/DataTable';
import { StatCard } from '../components/StatCard';
import { ChartPlaceholder } from '../components/ChartPlaceholder';

export function FundTracker() {
  const [activeTab, setActiveTab] = useState<'grants' | 'allocations' | 'expenses'>('grants');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(false);
  }, []);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount).replace('₹', '₹');
  };

  const tabs = [
    { id: 'grants', label: 'Grants', icon: 'account_balance' },
    { id: 'allocations', label: 'Allocations', icon: 'call_split' },
    { id: 'expenses', label: 'Expenses', icon: 'receipt_long' },
  ];

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-background">
      {/* TopAppBar */}
      <header className="flex justify-between items-center h-16 px-gutter bg-surface-container dark:bg-surface-container border-b border-outline-variant dark:border-outline-variant sticky top-0 z-40 shrink-0">
        <div className="flex items-center gap-4">
          <div className="md:hidden font-headline-md text-headline-md font-bold text-primary dark:text-primary">ABC Digital Compliance</div>
        </div>
        <div className="flex-1 max-w-md mx-4 hidden sm:block">
          <div className="relative">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">search</span>
            <input className="w-full bg-surface-container-highest border border-outline-variant rounded px-10 py-1.5 text-body-md font-body-md text-on-surface focus:outline-none focus:border-primary transition-colors" placeholder="Search funds, entities..." type="text" />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-2 rounded text-on-surface-variant hover:bg-surface-container-high transition-colors cursor-pointer active:opacity-80">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <button className="p-2 rounded text-on-surface-variant hover:bg-surface-container-high transition-colors cursor-pointer active:opacity-80">
            <span className="material-symbols-outlined">settings</span>
          </button>
          <button className="p-2 rounded text-on-surface-variant hover:bg-surface-container-high transition-colors cursor-pointer active:opacity-80">
            <span className="material-symbols-outlined">help</span>
          </button>
          <div className="w-8 h-8 rounded-full bg-secondary-container ml-2 overflow-hidden border border-outline-variant cursor-pointer">
            <img alt="Compliance Officer Profile" className="w-full h-full object-cover" src="" />
          </div>
        </div>
      </header>

      {/* Main Content Canvas */}
      <main className="flex-1 overflow-y-auto p-container-padding bg-surface-container-lowest">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Page Header & Actions */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="font-headline-md text-headline-md text-on-surface">Financial Monitoring Dashboard</h1>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">ABC Program Funds Allocation & Disbursement Tracking</p>
            </div>
            <button className="bg-primary text-on-primary font-label-bold text-label-bold px-4 py-2 rounded flex items-center gap-2 hover:bg-primary-fixed transition-colors">
              <span className="material-symbols-outlined text-[18px]">add</span>
              New Fund Request
            </button>
          </div>

          {/* Budget Overview Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Total Allocation" value="₹450.0M" trend="FY 2024" trendColor="primary" />
            <StatCard label="Funds Disbursed" value="₹285.5M" trend="63.4% of total" trendColor="secondary" />
            <StatCard label="Pending Requests" value="₹42.8M" trend="14 Requests pending review" trendColor="error" />
            <StatCard label="Available Balance" value="₹121.7M" trend="Projected end-of-Q3" trendColor="primary" />
          </div>

          {/* Main Content Area: Tabs */}
          <div className="bg-surface rounded-lg border border-outline-variant overflow-hidden">
            <div className="border-b border-outline-variant">
              <nav className="flex -mb-px" aria-label="Fund tracking tabs">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                      activeTab === tab.id
                        ? 'text-primary font-bold bg-secondary-container/10 border-primary'
                        : 'text-on-surface-variant font-medium hover:bg-secondary-container/20'
                    }`}
                    onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  >
                    <span className="material-symbols-outlined">{tab.icon}</span>
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>

            <div className="p-4">
              {activeTab === 'grants' && (
                <div className="lg:col-span-2 bg-surface rounded-lg border border-outline-variant overflow-hidden flex flex-col">
                  <div className="p-4 border-b border-outline-variant flex justify-between items-center bg-surface-container">
                    <h2 className="font-headline-sm text-headline-sm text-on-surface">Recent Disbursements</h2>
                    <button className="text-primary font-label-bold text-label-bold hover:underline">View All</button>
                  </div>
                  <div className="overflow-x-auto flex-1">
                    <DataTable
                      data={[
                        { date: '2023-10-24', centre: 'North Regional Hub', amount: 12500000, purpose: 'Infrastructure Upgrade', status: 'Approved' },
                        { date: '2023-10-22', centre: 'Eastern Tech Park', amount: 8250000, purpose: 'Operational Costs Q4', status: 'Processing' },
                        { date: '2023-10-18', centre: 'South District Hq', amount: 4100000, purpose: 'Training & Compliance', status: 'Approved' },
                        { date: '2023-10-15', centre: 'Central Data Center', amount: 22000000, purpose: 'Server Procurement', status: 'Flagged' },
                        { date: '2023-10-10', centre: 'West Operations Facility', amount: 5750000, purpose: 'Facility Maintenance', status: 'Approved' },
                      ]}
                      columns={[
                        { key: 'date', header: 'Date' },
                        { key: 'centre', header: 'Centre' },
                        { key: 'amount', header: 'Amount (₹)', align: 'right', render: (r: any) => formatCurrency(r.amount) },
                        { key: 'purpose', header: 'Purpose' },
                        {
                          key: 'status',
                          header: 'Status',
                          render: (r: any) => (
                            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-[11px] font-bold ${
                              r.status === 'Approved' ? 'bg-primary-container/20 text-primary' :
                              r.status === 'Processing' ? 'bg-secondary-container/50 text-secondary' :
                              'bg-error/20 text-error'
                            }`}>
                              {r.status === 'Processing' && <span className="material-symbols-outlined text-[12px]">sync</span>}
                              {r.status === 'Flagged' && <span className="material-symbols-outlined text-[12px]">error</span>}
                              {r.status}
                            </span>
                          )
                        },
                      ]}
                    />
                  </div>
                </div>
              )}

              {activeTab === 'allocations' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-1 bg-surface rounded-lg border border-outline-variant p-4 flex flex-col">
                    <h2 className="font-headline-sm text-headline-sm text-on-surface mb-4">Monthly Fund Disbursement</h2>
                    <ChartPlaceholder height="250px">
                      <div className="flex-1 min-h-[250px] relative w-full flex items-end justify-between gap-2 pt-8">
                        <div className="absolute left-0 top-0 bottom-6 w-8 flex flex-col justify-between text-[10px] text-on-surface-variant font-code-sm">
                          <span>100M</span><span>75M</span><span>50M</span><span>25M</span><span>0</span>
                        </div>
                        <div className="ml-10 flex-1 flex items-end justify-between gap-1 h-full pb-6 relative border-b border-outline-variant">
                          <div className="w-full bg-secondary-container hover:bg-primary transition-colors h-[30%] rounded-t group relative">
                            <span className="absolute -top-6 left-1/2 -translate-x-1/2 bg-surface-container-highest px-2 py-1 rounded text-[10px] hidden group-hover:block z-10">₹30M</span>
                          </div>
                          <div className="w-full bg-secondary-container hover:bg-primary transition-colors h-[45%] rounded-t group relative">
                            <span className="absolute -top-6 left-1/2 -translate-x-1/2 bg-surface-container-highest px-2 py-1 rounded text-[10px] hidden group-hover:block z-10">₹45M</span>
                          </div>
                          <div className="w-full bg-secondary-container hover:bg-primary transition-colors h-[25%] rounded-t group relative">
                            <span className="absolute -top-6 left-1/2 -translate-x-1/2 bg-surface-container-highest px-2 py-1 rounded text-[10px] hidden group-hover:block z-10">₹25M</span>
                          </div>
                          <div className="w-full bg-secondary-container hover:bg-primary transition-colors h-[60%] rounded-t group relative">
                            <span className="absolute -top-6 left-1/2 -translate-x-1/2 bg-surface-container-highest px-2 py-1 rounded text-[10px] hidden group-hover:block z-10">₹60M</span>
                          </div>
                          <div className="w-full bg-secondary-container hover:bg-primary transition-colors h-[80%] rounded-t group relative">
                            <span className="absolute -top-6 left-1/2 -translate-x-1/2 bg-surface-container-highest px-2 py-1 rounded text-[10px] hidden group-hover:block z-10">₹80M</span>
                          </div>
                          <div className="w-full bg-primary h-[45%] rounded-t group relative shadow-[0_0_10px_rgba(107,216,203,0.3)]">
                            <span className="absolute -top-6 left-1/2 -translate-x-1/2 bg-surface-container-highest px-2 py-1 rounded text-[10px] hidden group-hover:block z-10">₹45M</span>
                          </div>
                        </div>
                        <div className="absolute bottom-0 left-10 right-0 flex justify-between text-[10px] text-on-surface-variant font-code-sm pt-2">
                          <span>Jan</span><span>Feb</span><span>Mar</span><span>Apr</span><span>May</span><span>Jun</span>
                        </div>
                      </div>
                    </ChartPlaceholder>
                  </div>

                  <div className="lg:col-span-2 bg-surface rounded-lg border border-outline-variant overflow-hidden flex flex-col">
                    <div className="p-4 border-b border-outline-variant flex justify-between items-center bg-surface-container">
                      <h2 className="font-headline-sm text-headline-sm text-on-surface">Recent Disbursements</h2>
                      <button className="text-primary font-label-bold text-label-bold hover:underline">View All</button>
                    </div>
                    <div className="overflow-x-auto flex-1">
                      <DataTable
                        data={[
                          { date: '2023-10-24', centre: 'North Regional Hub', amount: 12500000, purpose: 'Infrastructure Upgrade', status: 'Approved' },
                          { date: '2023-10-22', centre: 'Eastern Tech Park', amount: 8250000, purpose: 'Operational Costs Q4', status: 'Processing' },
                          { date: '2023-10-18', centre: 'South District Hq', amount: 4100000, purpose: 'Training & Compliance', status: 'Approved' },
                          { date: '2023-10-15', centre: 'Central Data Center', amount: 22000000, purpose: 'Server Procurement', status: 'Flagged' },
                          { date: '2023-10-10', centre: 'West Operations Facility', amount: 5750000, purpose: 'Facility Maintenance', status: 'Approved' },
                        ]}
                        columns={[
                          { key: 'date', header: 'Date' },
                          { key: 'centre', header: 'Centre' },
                          { key: 'amount', header: 'Amount (₹)', align: 'right', render: (r: any) => formatCurrency(r.amount) },
                          { key: 'purpose', header: 'Purpose' },
                          {
                            key: 'status',
                            header: 'Status',
                            render: (r: any) => (
                              <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-[11px] font-bold ${
                                r.status === 'Approved' ? 'bg-primary-container/20 text-primary' :
                                r.status === 'Processing' ? 'bg-secondary-container/50 text-secondary' :
                                'bg-error/20 text-error'
                              }`}>
                                {r.status === 'Processing' && <span className="material-symbols-outlined text-[12px]">sync</span>}
                                {r.status === 'Flagged' && <span className="material-symbols-outlined text-[12px]">error</span>}
                                {r.status}
                              </span>
                            )
                          },
                        ]}
                      />
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'expenses' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-1 bg-surface rounded-lg border border-outline-variant p-4 flex flex-col">
                    <h2 className="font-headline-sm text-headline-sm text-on-surface mb-4">Expense Categories</h2>
                    <ChartPlaceholder height="250px">
                      <div className="flex-1 flex items-end gap-2 pt-8">
                        {['medicine', 'equipment', 'infrastructure', 'training', 'maintenance'].map((cat, i) => (
                          <div key={cat} className="flex-1 bg-secondary-container hover:bg-primary transition-colors h-[30%] rounded-t group relative">
                            <span className="absolute -top-6 left-1/2 -translate-x-1/2 bg-surface-container-highest px-2 py-1 rounded text-[10px] hidden group-hover:block z-10">₹{(i+1)*2}M</span>
                          </div>
                        ))}
                      </div>
                    </ChartPlaceholder>
                  </div>

                  <div className="lg:col-span-2 bg-surface rounded-lg border border-outline-variant overflow-hidden flex flex-col">
                    <div className="p-4 border-b border-outline-variant flex justify-between items-center bg-surface-container">
                      <h2 className="font-headline-sm text-headline-sm text-on-surface">Recent Expenses</h2>
                      <button className="text-primary font-label-bold text-label-bold hover:underline">View All</button>
                    </div>
                    <div className="overflow-x-auto flex-1">
                      <DataTable
                        data={[
                          { date: '2023-10-24', allocation: 'A1', category: 'medicine', amount: 2500000, billRef: 'BILL-001', status: 'Paid' },
                          { date: '2023-10-22', allocation: 'A1', category: 'equipment', amount: 15000000, billRef: 'BILL-002', status: 'Pending' },
                          { date: '2023-10-18', allocation: 'A2', category: 'infrastructure', amount: 8000000, billRef: 'BILL-003', status: 'Paid' },
                        ]}
                        columns={[
                          { key: 'date', header: 'Date' },
                          { key: 'allocation', header: 'Allocation' },
                          { key: 'category', header: 'Category' },
                          { key: 'amount', header: 'Amount (₹)', align: 'right', render: (r: any) => formatCurrency(r.amount) },
                          { key: 'billRef', header: 'Bill Ref' },
                          {
                            key: 'status',
                            header: 'Status',
                            render: (r: any) => (
                              <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-[11px] font-bold ${
                                r.status === 'Paid' ? 'bg-primary-container/20 text-primary' : 'bg-secondary-container/50 text-secondary'
                              }`}>
                                {r.status === 'Pending' && <span className="material-symbols-outlined text-[12px]">sync</span>}
                                {r.status}
                              </span>
                            )
                          },
                        ]}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}