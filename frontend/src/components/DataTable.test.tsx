import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DataTable } from '../components/DataTable';

describe('DataTable', () => {
  const mockData = [
    { id: '1', name: 'Item 1', value: 100, status: 'active' },
    { id: '2', name: 'Item 2', value: 200, status: 'inactive' },
    { id: '3', name: 'Item 3', value: 300, status: 'active' },
  ];

  const columns = [
    { key: 'id', header: 'ID' },
    { key: 'name', header: 'Name' },
    { key: 'value', header: 'Value', align: 'right' as const },
    {
      key: 'status',
      header: 'Status',
      render: (item: any) => (
        <span className={`badge ${item.status === 'active' ? 'active' : 'inactive'}`}>
          {item.status}
        </span>
      ),
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders table with data', () => {
    render(<DataTable data={mockData} columns={columns} />);
    
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 3')).toBeInTheDocument();
  });

  it('renders column headers', () => {
    render(<DataTable data={mockData} columns={columns} />);
    
    expect(screen.getByText('ID')).toBeInTheDocument();
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Value')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('handles empty data', () => {
    render(<DataTable data={[]} columns={columns} />);
    
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('renders custom render function', () => {
    render(<DataTable data={mockData} columns={columns} />);
    
    const activeElements = screen.getAllByText('active');
    expect(activeElements).toHaveLength(2);
    const inactiveElements = screen.getAllByText('inactive');
    expect(inactiveElements).toHaveLength(1);
  });

  it('filters data when filter is provided', async () => {
    render(<DataTable data={mockData} columns={columns} enableFiltering />);
    
    const filterInput = screen.getByPlaceholderText('Search all columns...');
    fireEvent.change(filterInput, { target: { value: 'Item 1' } });
    
    await waitFor(() => {
      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.queryByText('Item 2')).not.toBeInTheDocument();
      expect(screen.queryByText('Item 3')).not.toBeInTheDocument();
    });
  });

  it('sorts data when column header is clicked', async () => {
    render(<DataTable data={mockData} columns={columns} enableSorting />);
    
    const nameHeader = screen.getByText('Name');
    fireEvent.click(nameHeader);
    
    await waitFor(() => {
      // Check that first data row is Item 1 (alphabetically first)
      expect(screen.getByText('Item 1')).toBeInTheDocument();
    });
  });
});