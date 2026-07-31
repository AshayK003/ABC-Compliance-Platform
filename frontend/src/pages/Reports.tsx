import { useState } from 'react';
import { MOCK_REPORT_TEMPLATES } from '../mocks';

export function Reports() {
  const [templates] = useState(MOCK_REPORT_TEMPLATES);

  const [dateRange, setDateRange] = useState('Last 30 Days');
  const [region, setRegion] = useState('All India');
  const [metric, setMetric] = useState('Overall Compliance %');
  const [includeSubEntities, setIncludeSubEntities] = useState(true);
  const [highlightCritical, setHighlightCritical] = useState(false);
  const [compareBenchmark, setCompareBenchmark] = useState(true);

  const dateRanges = ['Last 30 Days', 'Current Quarter', 'Year to Date', 'Custom Range...'];
  const regions = ['All India', 'North Zone', 'South Zone', 'East Zone', 'West Zone'];
  const metrics = ['Overall Compliance %', 'Audit Deficiencies', 'Financial Irregularities', 'Protocol Adherence'];

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-background overflow-hidden">
      {/* TopAppBar */}
      <header className="flex justify-between items-center h-16 px-gutter w-full sticky top-0 z-40 bg-surface-container border-b border-outline-variant shrink-0">
        <div className="md:hidden flex items-center gap-2">
          <span className="font-headline-md text-headline-md font-bold text-primary">ABC Digital Compliance</span>
        </div>
        <div className="hidden md:flex items-center flex-1 max-w-md relative">
          <span className="material-symbols-outlined absolute left-3 text-on-surface-variant pointer-events-none text-sm">search</span>
          <input
            className="w-full bg-surface-container-lowest border border-outline-variant text-on-surface font-body-sm text-body-sm rounded-DEFAULT py-1.5 pl-9 pr-3 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors placeholder:text-on-surface-variant/50"
            placeholder="Search reports, entities, or metrics..."
            type="text"
          />
        </div>
        <div className="flex items-center gap-1 ml-auto">
          <button className="w-9 h-9 rounded-full flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high transition-colors cursor-pointer active:opacity-80">
            <span className="material-symbols-outlined text-[20px]">notifications</span>
          </button>
          <button className="w-9 h-9 rounded-full flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high transition-colors cursor-pointer active:opacity-80">
            <span className="material-symbols-outlined text-[20px]">settings</span>
          </button>
          <button className="w-9 h-9 rounded-full flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high transition-colors cursor-pointer active:opacity-80">
            <span className="material-symbols-outlined text-[20px]">help</span>
          </button>
          <div className="h-8 w-px bg-outline-variant mx-2"></div>
          <button className="w-8 h-8 rounded-full bg-tertiary-container overflow-hidden border border-outline-variant ml-1 cursor-pointer active:opacity-80 transition-opacity">
            <span className="material-symbols-outlined text-on-tertiary-container icon-fill text-lg">person</span>
          </button>
        </div>
      </header>

      {/* Canvas Content */}
      <div className="flex-1 overflow-y-auto p-container-padding">
        <div className="max-w-[1600px] mx-auto space-y-element-gap">
          {/* Page Header & Actions */}
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-4">
            <div>
              <h2 className="font-headline-md text-headline-md text-on-surface">Reporting & Analytics</h2>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">Generate, preview, and export high-density compliance data.</p>
            </div>
            <div className="flex items-center gap-2">
              <button className="flex items-center gap-2 px-3 py-1.5 border border-outline-variant rounded bg-surface hover:bg-surface-container-highest transition-colors">
                <span className="material-symbols-outlined text-[18px]">calendar_month</span>
                <span className="font-label-md text-label-md">{dateRange}</span>
              </button>
              <button className="flex items-center gap-2 px-3 py-1.5 border border-outline-variant rounded bg-surface text-secondary hover:text-on-surface hover:border-secondary transition-colors group">
                <span className="material-symbols-outlined text-[18px]">download</span>
                <span className="font-label-md text-label-md">Excel</span>
              </button>
              <button className="flex items-center gap-2 px-4 py-1.5 rounded bg-primary text-on-primary hover:bg-primary-container transition-colors">
                <span className="material-symbols-outlined text-[18px]">picture_as_pdf</span>
                <span className="font-label-md text-label-md font-bold">Export PDF</span>
              </button>
            </div>
          </div>

          {/* Main Bento Grid */}
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-element-gap">
            {/* Left Column: Custom Builder */}
            <div className="xl:col-span-8 bg-surface border border-outline-variant rounded-lg p-5 flex flex-col">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-primary text-[20px]">build</span>
                <h3 className="font-headline-sm text-headline-sm text-on-surface">Custom Report Builder</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="space-y-1.5">
                  <label className="font-label-bold text-label-bold text-on-surface-variant uppercase tracking-wider">Date Range</label>
                  <div className="relative">
                    <select
                      value={dateRange}
                      onChange={(e) => setDateRange(e.target.value)}
                      className="w-full bg-background border border-outline-variant text-on-surface font-body-sm text-body-sm rounded-DEFAULT py-2 pl-3 pr-8 appearance-none focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                    >
                      {dateRanges.map(r => <option key={r} value={r}>{r}</option>)}
                    </select>
                    <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none text-[18px]">expand_more</span>
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label className="font-label-bold text-label-bold text-on-surface-variant uppercase tracking-wider">Region / Zone</label>
                  <div className="relative">
                    <select
                      value={region}
                      onChange={(e) => setRegion(e.target.value)}
                      className="w-full bg-background border border-outline-variant text-on-surface font-body-sm text-body-sm rounded-DEFAULT py-2 pl-3 pr-8 appearance-none focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                    >
                      {regions.map(r => <option key={r} value={r}>{r}</option>)}
                    </select>
                    <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none text-[18px]">expand_more</span>
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label className="font-label-bold text-label-bold text-on-surface-variant uppercase tracking-wider">Primary Metric</label>
                  <div className="relative">
                    <select
                      value={metric}
                      onChange={(e) => setMetric(e.target.value)}
                      className="w-full bg-background border border-outline-variant text-on-surface font-body-sm text-body-sm rounded-DEFAULT py-2 pl-3 pr-8 appearance-none focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                    >
                      {metrics.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                    <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none text-[18px]">expand_more</span>
                  </div>
                </div>
              </div>
              <div className="flex flex-wrap gap-4 mt-auto pt-4 border-t border-outline-variant">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input checked={includeSubEntities} onChange={(e) => setIncludeSubEntities(e.target.checked)} className="w-4 h-4 rounded bg-background border-outline-variant text-primary focus:ring-primary focus:ring-offset-background" type="checkbox" />
                  <span className="font-body-sm text-body-sm text-on-surface-variant group-hover:text-on-surface transition-colors">Include Sub-entities</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input checked={highlightCritical} onChange={(e) => setHighlightCritical(e.target.checked)} className="w-4 h-4 rounded bg-background border-outline-variant text-primary focus:ring-primary focus:ring-offset-background" type="checkbox" />
                  <span className="font-body-sm text-body-sm text-on-surface-variant group-hover:text-on-surface transition-colors">Highlight Critical Flags</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input checked={compareBenchmark} onChange={(e) => setCompareBenchmark(e.target.checked)} className="w-4 h-4 rounded bg-background border-outline-variant text-primary focus:ring-primary focus:ring-offset-background" type="checkbox" />
                  <span className="font-body-sm text-body-sm text-on-surface-variant group-hover:text-on-surface transition-colors">Compare to Benchmark</span>
                </label>
                <button className="ml-auto flex items-center gap-2 px-4 py-1.5 rounded bg-surface-container-high border border-outline-variant hover:bg-secondary-container transition-colors">
                  <span className="material-symbols-outlined text-[16px] text-primary">play_arrow</span>
                  <span className="font-label-md text-label-md text-on-surface">Generate Preview</span>
                </button>
              </div>
            </div>

            {/* Right Column: Templates */}
            <div className="xl:col-span-4 bg-surface border border-outline-variant rounded-lg p-5">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-secondary text-[20px]">description</span>
                <h3 className="font-headline-sm text-headline-sm text-on-surface">Report Templates</h3>
              </div>
              <div className="space-y-2">
                {templates.map((template) => (
                  <button
                    key={template.id}
                    className="w-full flex items-center justify-between p-3 rounded bg-background border border-outline-variant hover:border-primary/50 hover:bg-surface-container-lowest transition-all group text-left"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded bg-surface-container flex items-center justify-center text-on-surface-variant group-hover:text-primary transition-colors">
                        <span className="material-symbols-outlined text-[18px]">{template.icon}</span>
                      </div>
                      <div>
                        <p className="font-label-md text-label-md text-on-surface">{template.name}</p>
                        <p className="font-code-sm text-code-sm text-on-surface-variant mt-0.5">{template.code}</p>
                      </div>
                    </div>
                    <span className="material-symbols-outlined text-on-surface-variant/30 group-hover:text-primary transition-colors">arrow_forward</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Row 2: Visual Previews */}
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-element-gap mt-6">
            {/* Map Heatmap */}
            <div className="xl:col-span-6 bg-surface border border-outline-variant rounded-lg p-5 flex flex-col h-[400px]">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-on-surface-variant text-[20px]">map</span>
                  <h3 className="font-label-md text-label-md text-on-surface uppercase tracking-wider">Compliance Heatmap</h3>
                </div>
                <span className="font-code-sm text-code-sm text-secondary bg-secondary/10 px-2 py-0.5 rounded">LIVE</span>
              </div>
              <div className="flex-1 relative rounded bg-background border border-outline-variant overflow-hidden">
                <img
                  className="absolute inset-0 w-full h-full object-cover opacity-80 mix-blend-screen"
                  alt="A highly detailed, dark-mode data visualization map of India constructed from glowing cyan and teal geometric grids. Specific states pulse with red and green light to indicate data heatmaps."
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuAVsdOh8qQzzPCbs2px1JH1Nlm9uQTMB9OyNAvtnhTNO1JsT4thT5iEnD6tMgjI-LdOPLkAa-FRCv_pPtVu8PbTeFPbcNvE8hGQHHFtrXrVKg_MUFnV5dAoMdHL38rQsXRHC90qXu1Z8iIBFtNxjpZ3iSmJAULNoX3MnyEax7RdEE2qWcXxIwAwnFqhyK8gXs1i3YyvRCsnVg_KBOJsiAxs2bIkvFAwSKL-Ex2D133u9lATs3umY58"
                />
                <div className="absolute bottom-3 left-3 bg-surface/90 backdrop-blur-sm border border-outline-variant p-2 rounded text-xs space-y-1">
                  <div className="flex items-center gap-2"><div className="w-2 h-2 bg-error rounded-full"></div><span className="text-on-surface-variant">Critical Risk</span></div>
                  <div className="flex items-center gap-2"><div className="w-2 h-2 bg-secondary rounded-full"></div><span className="text-on-surface-variant">Moderate</span></div>
                  <div className="flex items-center gap-2"><div className="w-2 h-2 bg-primary rounded-full"></div><span className="text-on-surface-variant">Compliant</span></div>
                </div>
              </div>
            </div>

            {/* Chart Preview */}
            <div className="xl:col-span-6 bg-surface border border-outline-variant rounded-lg p-5 flex flex-col h-[400px]">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-on-surface-variant text-[20px]">bar_chart</span>
                  <h3 className="font-label-md text-label-md text-on-surface uppercase tracking-wider">Year-on-Year Adherence</h3>
                </div>
                <div className="font-headline-sm text-headline-sm text-primary">+12.4% <span className="material-symbols-outlined align-middle text-[18px]">arrow_upward</span></div>
              </div>
              <div className="flex-1 flex items-end gap-2 pt-8 relative">
                {/* Y-axis lines */}
                <div className="absolute inset-0 flex flex-col justify-between pb-8 pointer-events-none">
                  <div className="w-full h-px bg-outline-variant/30"></div>
                  <div className="w-full h-px bg-outline-variant/30"></div>
                  <div className="w-full h-px bg-outline-variant/30"></div>
                  <div className="w-full h-px bg-outline-variant/30"></div>
                </div>
                {/* Bars */}
                <div className="flex-1 flex flex-col items-center gap-2 z-10 group">
                  <div className="w-full bg-secondary-container rounded-t relative overflow-hidden chart-bar" style={{ '--target-h': '40%' } as React.CSSProperties}>
                    <div className="absolute bottom-0 w-full h-full bg-secondary/20"></div>
                  </div>
                  <span className="font-code-sm text-code-sm text-on-surface-variant">Q1</span>
                </div>
                <div className="flex-1 flex flex-col items-center gap-2 z-10 group">
                  <div className="w-full bg-secondary-container rounded-t relative overflow-hidden chart-bar" style={{ '--target-h': '55%' } as React.CSSProperties}>
                    <div className="absolute bottom-0 w-full h-full bg-secondary/20"></div>
                  </div>
                  <span className="font-code-sm text-code-sm text-on-surface-variant">Q2</span>
                </div>
                <div className="flex-1 flex flex-col items-center gap-2 z-10 group">
                  <div className="w-full bg-secondary-container rounded-t relative overflow-hidden chart-bar" style={{ '--target-h': '48%' } as React.CSSProperties}>
                    <div className="absolute bottom-0 w-full h-full bg-secondary/20"></div>
                  </div>
                  <span className="font-code-sm text-code-sm text-on-surface-variant">Q3</span>
                </div>
                <div className="flex-1 flex flex-col items-center gap-2 z-10 group">
                  <div className="w-full bg-secondary-container rounded-t relative overflow-hidden chart-bar" style={{ '--target-h': '70%' } as React.CSSProperties}>
                    <div className="absolute bottom-0 w-full h-full bg-secondary/20"></div>
                  </div>
                  <span className="font-code-sm text-code-sm text-on-surface-variant">Q4</span>
                </div>
                <div className="flex-1 flex flex-col items-center gap-2 z-10 group">
                  <div className="w-full bg-primary-container rounded-t relative overflow-hidden chart-bar" style={{ '--target-h': '85%' } as React.CSSProperties}>
                    <div className="absolute inset-0 bg-gradient-to-t from-transparent to-primary/20"></div>
                  </div>
                  <span className="font-code-sm text-code-sm text-primary font-bold">Q1 '24</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}