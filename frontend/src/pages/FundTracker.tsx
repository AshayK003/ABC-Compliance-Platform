import { useState, useEffect } from 'react';
import { DataTable } from '../components/DataTable';
import { StatCard } from '../components/StatCard';
import { ChartPlaceholder } from '../components/ChartPlaceholder';
import { api } from '../services/api';

type FundDisbursement = {
  date: string;
  centre: string;
  amount: number;
  purpose: string;
  status: 'Approved' | 'Processing' | 'Flagged';
};

type ExpenseRecord = {
  date: string;
  allocation: string;
  category: string;
  amount: number;
  billRef: string;
  status: 'Paid' | 'Pending';
};

export function FundTracker() {
  const [activeTab, setActiveTab] = useState<'grants' | 'allocations' | 'expenses'>('grants');
  const [loading, setLoading] = useState(true);
  const [disbursements, setDisbursements] = useState<FundDisbursement[]>([]);
  const [allocations, setAllocations] = useState<FundDisbursement[]>([]);
  const [expenses, setExpenses] = useState<ExpenseRecord[]>([]);
  const [fundStats, setFundStats] = useState({ total: 0, disbursed: 0, pending: 0, available: 0 });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [grantData, allocationData, expenseData, centreData] = await Promise.all([
        api.getGrants(),
        api.getAllocations().catch(() => [] as never[]),
        api.getExpenses().catch(() => [] as never[]),
        api.getCentres().catch(() => [] as never[]),
      ]);
      const centreMap = new Map((centreData as Array<{ id: string; name: string }>).map(c => [c.id, c.name]));

      const grants = grantData as Array<{ awbi_ref: string; amount: number; purpose: string; financial_year: string; status: string }>;
      const allocs = allocationData as Array<{ id: string; grant_id: string; centre_id: string; amount: number; allocated_at: string }>;
      const exps = expenseData as Array<{ allocation_id: string; category: string; amount: number; bill_ref?: string; expense_at: string }>;

      setDisbursements(grants.map(g => ({
        date: g.financial_year,
        centre: 'AWBI Central',
        amount: g.amount,
        purpose: g.purpose,
        status: (g.status === 'approved' ? 'Approved' : g.status === 'pending' ? 'Processing' : 'Flagged') as FundDisbursement['status'],
      })));
      setAllocations(allocs.map(a => ({
        date: (a.allocated_at ?? '').slice(0, 10),
        centre: centreMap.get(a.centre_id) ?? a.centre_id,
        amount: a.amount,
        purpose: `Allocation ${a.id.slice(0, 8)}`,
        status: 'Approved' as const,
      })));
      setExpenses(exps.map(e => ({
        date: (e.expense_at ?? '').slice(0, 10),
        allocation: e.allocation_id.slice(0, 8),
        category: e.category,
        amount: e.amount,
        billRef: e.bill_ref ?? '—',
        status: 'Paid' as const,
      })));

      const total = grants.reduce((s, g) => s + g.amount, 0);
      const disbursed = grants.filter(g => g.status === 'approved' || g.status === 'disbursed').reduce((s, g) => s + g.amount, 0);
      const pending = grants.filter(g => g.status === 'pending').reduce((s, g) => s + g.amount, 0);
      setFundStats({ total, disbursed, pending, available: total - disbursed });
    } catch (error) {
      console.error('Failed to load fund data:', error);
    } finally {
      setLoading(false);
    }
  };

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
            <span className="material-symbols-outlined text-on-secondary-container icon-fill text-lg">person</span>
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
            <StatCard label="Total Allocation" value={`₹${(fundStats.total / 1_00_000).toFixed(1)}M`} trend="All grants" trendColor="primary" />
            <StatCard label="Funds Disbursed" value={`₹${(fundStats.disbursed / 1_00_000).toFixed(1)}M`} trend={fundStats.total ? `${((fundStats.disbursed / fundStats.total) * 100).toFixed(1)}% of total` : '0% of total'} trendColor="secondary" />
            <StatCard label="Pending Requests" value={`₹${(fundStats.pending / 1_00_000).toFixed(1)}M`} trend={`${disbursements.filter(d => d.status === 'Processing').length} Requests pending review`} trendColor="error" />
            <StatCard label="Available Balance" value={`₹${(fundStats.available / 1_00_000).toFixed(1)}M`} trend="Computed from grants" trendColor="primary" />
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
                      data={disbursements}
                      columns={[
                        { key: 'date', header: 'Date' },
                        { key: 'centre', header: 'Centre' },
                        { key: 'amount', header: 'Amount (₹)', align: 'right', render: (r: FundDisbursement) => formatCurrency(r.amount) },
                        { key: 'purpose', header: 'Purpose' },
                        {
                          key: 'status',
                          header: 'Status',
                          render: (r: FundDisbursement) => (
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
                          <div className="w-full bg-secondary-container hover:bg-primary transition-colors h-[30%] rounded-t group relative chart-bar" style={{ '--target-h': '30%' } as React.CSSProperties}>
                            <span className="absolute -top-6 left-1/2 -translate-x-1/2 bg-surface-container-highest px-2 py-1 rounded text-[10px] hidden group-hover:block z-10">₹30M</span>
                          </div>
                          <div className="w-full bg-secondary-container hover:bg-primary transition-colors h-[45%] rounded-t group relative chart-bar" style={{ '--target-h': '45%' } as React.CSSProperties}>
                            <span className="absolute -top-6 left-1/2 -translate-x-1/2 bg-surface-container-highest px-2 py-1 rounded text-[10px] hidden group-hover:block z-10">₹45M</span>
                          </div>
                          <div className="w-full bg-secondary-container hover:bg-primary transition-colors h-[25%] rounded-t group relative chart-bar" style={{ '--target-h': '25%' } as React.CSSProperties}>
                            <span className="absolute -top-6 left-1/2 -translate-x-1/2 bg-surface-container-highest px-2 py-1 rounded text-[10px] hidden group-hover:block z-10">₹25M</span>
                          </div>
                          <div className="w-full bg-secondary-container hover:bg-primary transition-colors h-[60%] rounded-t group relative chart-bar" style={{ '--target-h': '60%' } as React.CSSProperties}>
                            <span className="absolute -top-6 left-1/2 -translate-x-1/2 bg-surface-container-highest px-2 py-1 rounded text-[10px] hidden group-hover:block z-10">₹60M</span>
                          </div>
                          <div className="w-full bg-secondary-container hover:bg-primary transition-colors h-[80%] rounded-t group relative chart-bar" style={{ '--target-h': '80%' } as React.CSSProperties}>
                            <span className="absolute -top-6 left-1/2 -translate-x-1/2 bg-surface-container-highest px-2 py-1 rounded text-[10px] hidden group-hover:block z-10">₹80M</span>
                          </div>
                          <div className="w-full bg-primary h-[45%] rounded-t group relative chart-bar" style={{ '--target-h': '45%' } as React.CSSProperties}>
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
                        data={allocations}
                        columns={[
                          { key: 'date', header: 'Date' },
                          { key: 'centre', header: 'Centre' },
                          { key: 'amount', header: 'Amount (₹)', align: 'right', render: (r: FundDisbursement) => formatCurrency(r.amount) },
                          { key: 'purpose', header: 'Purpose' },
                          {
                            key: 'status',
                            header: 'Status',
                            render: (r: FundDisbursement) => (
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
                          <div key={cat} className="flex-1 bg-secondary-container hover:bg-primary transition-colors h-[30%] rounded-t group relative chart-bar" style={{ '--target-h': `${(i+1)*15}%` } as React.CSSProperties}>
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
                        data={expenses}
                        columns={[
                          { key: 'date', header: 'Date' },
                          { key: 'allocation', header: 'Allocation' },
                          { key: 'category', header: 'Category' },
                          { key: 'amount', header: 'Amount (₹)', align: 'right', render: (r: ExpenseRecord) => formatCurrency(r.amount) },
                          { key: 'billRef', header: 'Bill Ref' },
                          {
                            key: 'status',
                            header: 'Status',
                            render: (r: ExpenseRecord) => (
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