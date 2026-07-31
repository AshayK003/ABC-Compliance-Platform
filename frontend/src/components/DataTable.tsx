interface DataTableProps<T> {
  data: T[];
  columns: Array<{
    key: string;
    header: string;
    render?: (item: T) => React.ReactNode;
    align?: 'left' | 'center' | 'right';
  }>;
  emptyMessage?: string;
  onRowClick?: (item: T) => void;
  className?: string;
}

export function DataTable<T>({
  data,
  columns,
  emptyMessage = 'No data available',
  onRowClick,
  className = '',
}: DataTableProps<T>) {
  return (
    <div className={`overflow-x-auto flex-1 ${className}`}>
      <table className="w-full text-left border-collapse min-w-[800px]">
        <thead>
          <tr className="bg-surface-container border-b border-outline-variant text-on-surface-variant font-label-bold text-label-bold uppercase tracking-wider">
            {columns.map((col) => (
              <th key={col.key} className={`p-table-cell-padding ${col.align ? `text-${col.align}` : ''}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="font-body-sm text-body-sm text-on-surface divide-y divide-outline-variant">
          {data.length > 0 ? (
            data.map((item, index) => (
              <tr
                key={index}
                className={`hover:bg-surface-container-highest/50 transition-colors ${onRowClick ? 'cursor-pointer' : ''}`}
                onClick={() => onRowClick?.(item)}
              >
                {columns.map((col) => (
                  <td key={col.key} className={`p-table-cell-padding ${col.align ? `text-${col.align}` : ''}`}>
                    {col.render ? col.render(item as T) : (item as Record<string, unknown>)[col.key] as React.ReactNode}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length} className="p-table-cell-padding text-center text-on-surface-variant py-8">
                {emptyMessage}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}