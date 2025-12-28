import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ItemCard from '../ItemCard';

describe('ItemCard', () => {
  const mockItem = {
    id: 1,
    name: 'Ribeye Steak',
    qr_code: 'FRZ-ABC123',
    source: 'Costco',
    weight: 2.5,
    weight_unit: 'lb',
    category_name: 'Beef',
    added_date: new Date().toISOString(),
    expiration_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    status: 'in_freezer',
    notes: 'Prime cut'
  };

  const mockOnEdit = vi.fn();
  const mockOnStatusChange = vi.fn();

  it('renders item name', () => {
    render(<ItemCard item={mockItem} onEdit={mockOnEdit} onStatusChange={mockOnStatusChange} />);
    expect(screen.getByText('Ribeye Steak')).toBeInTheDocument();
  });

  it('renders item details', () => {
    render(<ItemCard item={mockItem} onEdit={mockOnEdit} onStatusChange={mockOnStatusChange} />);
    expect(screen.getByText(/Costco/)).toBeInTheDocument();
    expect(screen.getByText(/2.5 lb/)).toBeInTheDocument();
    expect(screen.getByText(/Beef/)).toBeInTheDocument();
  });

  it('displays QR code when QR button is clicked', () => {
    render(<ItemCard item={mockItem} onEdit={mockOnEdit} onStatusChange={mockOnStatusChange} />);

    // QR code is hidden initially
    expect(screen.queryByText('FRZ-ABC123')).not.toBeInTheDocument();

    // Click QR button to show QR code
    const qrButton = screen.getByText('QR');
    fireEvent.click(qrButton);

    // Now QR code should be visible
    expect(screen.getByText('FRZ-ABC123')).toBeInTheDocument();
  });

  it('calculates days in freezer', () => {
    render(<ItemCard item={mockItem} onEdit={mockOnEdit} onStatusChange={mockOnStatusChange} />);
    expect(screen.getByText('Days in freezer:')).toBeInTheDocument();
    expect(screen.getByText(/0 days/)).toBeInTheDocument();
  });

  it('shows expiration warning for items expiring soon', () => {
    const expiringItem = {
      ...mockItem,
      expiration_date: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString()
    };

    const { container } = render(<ItemCard item={expiringItem} onEdit={mockOnEdit} onStatusChange={mockOnStatusChange} />);
    expect(container.querySelector('.expiring-soon')).toBeInTheDocument();
  });

  it('shows expired warning for expired items', () => {
    const expiredItem = {
      ...mockItem,
      expiration_date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString()
    };

    const { container } = render(<ItemCard item={expiredItem} onEdit={mockOnEdit} onStatusChange={mockOnStatusChange} />);
    expect(container.querySelector('.expired')).toBeInTheDocument();
  });

  it('calls onEdit when Edit button is clicked', () => {
    render(<ItemCard item={mockItem} onEdit={mockOnEdit} onStatusChange={mockOnStatusChange} />);
    const editButton = screen.getByText('Edit');
    fireEvent.click(editButton);
    expect(mockOnEdit).toHaveBeenCalled();
  });

  it('calls onStatusChange when Consumed button is clicked', () => {
    render(<ItemCard item={mockItem} onEdit={mockOnEdit} onStatusChange={mockOnStatusChange} />);
    const consumeButton = screen.getByText('Consumed');
    fireEvent.click(consumeButton);
    expect(mockOnStatusChange).toHaveBeenCalledWith('consumed');
  });

  it('does not render negative days in freezer', () => {
    const futureItem = {
      ...mockItem,
      added_date: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString()
    };

    render(<ItemCard item={futureItem} onEdit={mockOnEdit} onStatusChange={mockOnStatusChange} />);
    expect(screen.getByText('Days in freezer:')).toBeInTheDocument();
    expect(screen.getByText(/0 days/)).toBeInTheDocument();
  });

  it('displays notes when present', () => {
    render(<ItemCard item={mockItem} onEdit={mockOnEdit} onStatusChange={mockOnStatusChange} />);
    expect(screen.getByText(/Prime cut/)).toBeInTheDocument();
  });
});
