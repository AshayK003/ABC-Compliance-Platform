import { useState, useMemo, useCallback } from 'react';

function getSortArrow(
  sortConfig: { key: string; direction: 'asc' | 'desc' } | null,
  columnKey: string
) {
  if (sortConfig && sortConfig.key === columnKey) {
    return sortConfig.direction === 'asc' ? '▲' : '▼';
  }
  return <span className="text-on-surface-variant/50">▼</span>;
}

interface Column<T> {
  readonly key: string;
  readonly header: string;
  readonly render?: (item: T) => React.ReactNode;
  readonly align?: 'left' | 'center' | 'right';
  readonly width?: string;
  readonly sortable?: boolean;
  readonly filterable?: boolean;
  readonly filterOptions?: readonly { readonly value: string; readonly label: string }[];
}

interface DataTableProps<T> {
  readonly data: readonly T[];
  readonly columns: readonly Column<T>[];
  readonly emptyMessage?: string;
  readonly onRowClick?: (item: T) => void;
  readonly className?: string;
  readonly enablePagination?: boolean;
  readonly pageSize?: number;
  readonly enableSorting?: boolean;
  readonly enableFiltering?: boolean;
  readonly enableExport?: boolean;
  readonly exportFilename?: string;
  readonly onFilterChange?: (filters: Record<string, string>) => void;
  readonly onSortChange?: (sort: { key: string; direction: 'asc' | 'desc' } | null) => void;
}

function getFilterElement(col: Column<any>, filters: Record<string, string>, onFilterChange: (key: string, value: string) => void) {
  if (col.filterOptions && col.filterOptions.length > 0) {
    return (
      <select
        value={filters[col.key] ?? ''}
        onChange={e => onFilterChange(col.key, e.target.value)}
        className="w-full bg-background border border-outline-variant rounded px-3 py-1.5 text-on-surface font-body-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none appearance-none cursor-pointer"
      >
        <option value="">All</option>
        {col.filterOptions.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    );
  }
  
  return (
    <input
      type="text"
      placeholder={'Filter ' + col.header + '...'}
      value={filters[col.key] ?? ''}
      onChange={e => onFilterChange(col.key, e.target.value)}
      className="w-full bg-background border border-outline-variant rounded px-3 py-1.5 text-on-surface font-body-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none placeholder:text-outline"
    />
  );
}

function FilterRow({ 
  filters, 
  onFilterChange, 
  columns 
}: { 
  filters: Record<string, string>; 
  readonly onFilterChange: (key: string, value: string) => void; 
  readonly columns: readonly Column<any>[]; 
}) {
  const filterableColumns = columns.filter(col => col.filterable);
  if (filterableColumns.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 p-4 bg-surface-container border-b border-outline-variant">
      {columns
        .filter(col => col.filterable)
        .map(col => (
          <div key={col.key} className="flex-1 min-w-[150px] max-w-xs">
            <label className="block font-label-sm text-label-sm text-on-surface-variant mb-1">{col.header}</label>
            {getFilterElement(col, filters, onFilterChange)}
          </div>
        ))}
    </div>
  );
}

function Toolbar({ 
  enableFiltering, 
  enableExport, 
  exportFilename, 
  globalFilter, 
  setGlobalFilter, 
  setFilters, 
  setCurrentPage,
  filteredAndSortedData,
  hasActiveFilters,
  columns,
}: {
  readonly enableFiltering: boolean;
  readonly enableExport: boolean;
  readonly exportFilename: string;
  readonly globalFilter: string;
  readonly setGlobalFilter: (value: string) => void;
  readonly setFilters: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  readonly setCurrentPage: React.Dispatch<React.SetStateAction<number>>;
  readonly filteredAndSortedData: readonly any[];
  readonly hasActiveFilters: boolean;
  readonly columns: readonly any[];
}) {
  if (!enableFiltering && !enableExport) return null;

  const handleExport = () => {
      const csvContent = [
        columns.map(c => c.header).join(','),
        filteredAndSortedData.map(row =>
          columns.map(col => {
            const value = (row as Record<string, unknown>)[col.key];
            return '"' + String(value ?? '').replaceAll('"', '""') + '"';
          }).join(',')
        ),
      ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = exportFilename + '_' + new Date().toISOString().split('T')[0] + '.csv';
    link.click();
  };

  const handleClearFilters = () => {
    setFilters({});
    setGlobalFilter('');
    setCurrentPage(1);
  };

  return (
    <div className="flex flex-col sm:flex-row gap-4 p-4 bg-surface-container-high border-b border-outline-variant">
      <div className="flex-1 flex gap-2 min-w-0">
        <div className="relative flex-1 max-w-xs">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant/50">search</span>
          <input
            type="text"
            placeholder="Search all columns..."
            value={globalFilter}
            onChange={e => setGlobalFilter(e.target.value)}
            className="w-full bg-background border border-outline-variant rounded pl-10 pr-3 py-2 text-on-surface font-body-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-outline"
          />
        </div>
        {hasActiveFilters && (
                                  <button
                                    type="button"
                                    onClick={handleClearFilters}
                                    className="px-3 py-2 bg-surface-container-high border border-outline-variant rounded text-on-surface-variant font-label-sm hover:bg-surface-variant transition-colors flex items-center gap-1"
                                    disabled={!hasActiveFilters}
                                  >
                            <span className="material-symbols-outlined w-4 h-4">filter_list</span>
                            <span>Clear Filters</span>
                          </button>
                        )}
      </div>
      <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleExport}
                className="px-3 py-2 bg-primary text-on-primary font-label-bold text-label-sm rounded transition-colors hover:bg-primary/90 flex items-center gap-2"
              >
                <span className="material-symbols-outlined w-4 h-4">download</span>
                Export CSV
              </button>
            </div>
    </div>
  );
}

function Pagination({ 
  currentPage, 
  setCurrentPage, 
  totalPages, 
  pageSize, 
  filteredAndSortedData,
}: {
  readonly currentPage: number;
  readonly setCurrentPage: (page: number | ((prev: number) => number)) => void;
  readonly totalPages: number;
  readonly pageSize: number;
  readonly filteredAndSortedData: readonly any[];
}) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between p-4 bg-surface-container-highest border-t border-outline-variant">
      <div className="font-body-sm text-on-surface-variant">
        Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, filteredAndSortedData.length)} of {filteredAndSortedData.length} entries
      </div>
      <div className="flex items-center gap-1">
        <button
                  type="button"
                  onClick={() => setCurrentPage(1)}
                  disabled={currentPage === 1}
                  className="p-2 rounded text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="First page"
                >
                  <span className="material-symbols-outlined w-5 h-5">first_page</span>
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="p-2 rounded text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Previous page"
                >
                  <span className="material-symbols-outlined w-5 h-5">chevron_left</span>
                </button>
        <div className="flex items-center gap-1 mx-2">
          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
            let pageNum;
            if (totalPages <= 5) {
              pageNum = i + 1;
            } else if (currentPage <= 3) {
              pageNum = i + 1;
            } else if (currentPage >= totalPages - 2) {
              pageNum = totalPages - 4 + i;
            } else {
              pageNum = currentPage - 2 + i;
            }
            return (
              <button
                key={pageNum}
                onClick={() => setCurrentPage(pageNum)}
                className={'w-8 h-8 rounded font-label-md text-label-md flex items-center justify-center transition-colors ' + (
                  currentPage === pageNum
                    ? 'bg-primary text-on-primary'
                    : 'hover:bg-surface-container text-on-surface-variant hover:text-on-surface'
                )}
              >
                {pageNum}
              </button>
            );
          })}
        </div>
        <button
                  type="button"
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="p-2 rounded text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Next page"
                >
                  <span className="material-symbols-outlined w-5 h-5">chevron_right</span>
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentPage(totalPages)}
                  disabled={currentPage === totalPages}
                  className="p-2 rounded text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Last page"
                >
                  <span className="material-symbols-outlined w-5 h-5">last_page</span>
                </button>
      </div>
    </div>
  );
}

export function DataTable<T>({
  data,
  columns,
  emptyMessage = 'No data available',
  onRowClick,
  className = '',
  enablePagination = true,
  pageSize = 10,
  enableSorting = true,
  enableFiltering = true,
  enableExport = false,
  exportFilename = 'export',
  onFilterChange,
  onSortChange,
}: DataTableProps<T>) {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [globalFilter, setGlobalFilter] = useState('');

  const filteredAndSortedData = useMemo(() => {
    let result = [...data];

    if (globalFilter) {
      const searchTerm = globalFilter.toLowerCase();
      result = result.filter(item =>
        Object.values(item as Record<string, unknown>).some(
          val => String(val).toLowerCase().includes(searchTerm)
        )
      );
    }

    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        result = result.filter(item =>
          String((item as Record<string, unknown>)[key] ?? '').toLowerCase().includes(value.toLowerCase())
        );
      }
    });

    if (sortConfig) {
              result.sort((a, b) => {
                const aVal = (a as Record<string, unknown>)[sortConfig.key];
                const bVal = (b as Record<string, unknown>)[sortConfig.key];
                if (aVal === bVal) return 0;
                const direction = sortConfig.direction === 'asc' ? 1 : -1;
                if (typeof aVal === 'string' && typeof bVal === 'string') {
                  return aVal.localeCompare(bVal) * direction;
                }
                if (typeof aVal === 'number' && typeof bVal === 'number') {
                  return (aVal - bVal) * direction;
                }
                return String(aVal ?? '').localeCompare(String(bVal ?? '')) * direction;
              });
            }

    return result;
  }, [data, filters, globalFilter, sortConfig]);

  const handleSort = useCallback((key: string) => {
    if (!enableSorting) return;
    setSortConfig(current => {
      if (current && current.key === key && current.direction === 'asc') {
        return { key, direction: 'desc' };
      }
      return { key, direction: 'asc' };
    });
    onSortChange?.({ key, direction: sortConfig?.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc' });
  }, [enableSorting, sortConfig, onSortChange]);

  const handleFilterChange = useCallback((key: string, value: string) => {
      if (!enableFiltering) return;
      setFilters(prev => ({ ...prev, [key]: value }));
      onFilterChange?.({ ...filters, [key]: value });
    }, [enableFiltering, filters, onFilterChange]);

    const paginatedData = useMemo(() => {
    if (!enablePagination) return filteredAndSortedData;
    const start = (currentPage - 1) * pageSize;
    return filteredAndSortedData.slice(start, start + pageSize);
  }, [filteredAndSortedData, currentPage, pageSize, enablePagination]);

  const totalPages = Math.ceil(filteredAndSortedData.length / pageSize);

  const hasActiveFilters = Boolean(Object.values(filters).some(v => v) || globalFilter);

    const tbodyContent = paginatedData.length > 0 ? (
      paginatedData.map((item, index) => (
        <tr
          key={index}
          className={'hover:bg-surface-container-highest/50 transition-colors ' + (onRowClick ? 'cursor-pointer' : '')}
          onClick={() => onRowClick && onRowClick(item)}
        >
          {columns.map((col) => (
            <td
              key={col.key}
              className={'p-table-cell-padding ' + (col.align ? 'text-' + col.align : '')}
              style={col.width ? { width: col.width, minWidth: col.width } : undefined}
            >
              {col.render ? col.render(item as T) : String((item as Record<string, unknown>)[col.key] ?? '')}
            </td>
          ))}
        </tr>
      ))
    ) : (
      <tr>
        <td colSpan={columns.length} className="p-table-cell-padding text-center text-on-surface-variant py-12">
          {hasActiveFilters ? 'No results match your filters' : 'No data available'}
        </td>
      </tr>
    );

    // Early return for empty data without filters
    if (!data.length && !hasActiveFilters) {
      return (
        <div className={'overflow-x-auto flex-1 ' + className}>
          <div className="flex flex-col items-center justify-center h-full p-8">
            <span className="material-symbols-outlined w-12 h-12 text-on-surface-variant/50 mb-4">search</span>
            <h3 className="font-headline-sm text-on-surface mb-1">{emptyMessage}</h3>
            <p className="font-body-sm text-on-surface-variant">Try adjusting your filters or search terms</p>
          </div>
        </div>
      );
    }

    return (
      <div className={'flex flex-col h-full ' + className}>
        <Toolbar
              enableFiltering={enableFiltering}
              enableExport={enableExport}
              exportFilename={exportFilename}
              globalFilter={globalFilter}
              setGlobalFilter={setGlobalFilter}
              setFilters={setFilters}
              setCurrentPage={setCurrentPage}
              filteredAndSortedData={filteredAndSortedData}
              hasActiveFilters={hasActiveFilters}
              columns={columns}
            />

      {enableFiltering && <FilterRow filters={filters} onFilterChange={handleFilterChange} columns={columns} />}

      <div className={'overflow-x-auto flex-1 ' + className}>
        <table className="w-full text-left border-collapse min-w-[800px]">
          <thead>
            <tr className="bg-surface-container border-b border-outline-variant text-on-surface-variant font-label-bold text-label-bold uppercase tracking-wider">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={'p-table-cell-padding ' + (col.align ? 'text-' + col.align : '')}
                  style={col.width ? { width: col.width, minWidth: col.width } : undefined}
                >
                  <div className="flex items-center gap-1">
                    {col.header}
                    {enableSorting && col.sortable && (
                                          <button
                                            type="button"
                                            onClick={() => handleSort(col.key)}
                                            className="p-1 rounded hover:bg-surface-variant transition-colors"
                                            aria-label={'Sort by ' + col.header}
                                          >
                                            {getSortArrow(sortConfig, col.key)}
                                          </button>
                                        )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="font-body-sm text-body-sm text-on-surface divide-y divide-outline-variant">
            {tbodyContent}
          </tbody>
        </table>
      </div>

      <Pagination
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        filteredAndSortedData={filteredAndSortedData}
      />
    </div>
  );
}