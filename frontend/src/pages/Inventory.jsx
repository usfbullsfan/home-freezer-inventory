import { useState, useEffect } from 'react';
import { itemsAPI, categoriesAPI } from '../services/api';
import ItemCard from '../components/ItemCard';
import AddItemModal from '../components/AddItemModal';
import QRInputModal from '../components/QRInputModal';
import QRScanner from '../components/QRScanner';
import SessionBanner from '../components/SessionBanner';

function Inventory() {
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Detect if running in development mode
  const isDev = import.meta.env.DEV;

  // Search and filter state
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('in_freezer');
  const [sortBy, setSortBy] = useState('added_date');
  const [sortOrder, setSortOrder] = useState('desc');

  // Modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [showQRModal, setShowQRModal] = useState(false);
  const [showQRScanner, setShowQRScanner] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  // Session tracking - force re-render when session changes
  const [sessionKey, setSessionKey] = useState(0);

  useEffect(() => {
    loadCategories();
    loadItems();
  }, [search, categoryFilter, statusFilter, sortBy, sortOrder]);

  // Listen for session changes to update the banner
  useEffect(() => {
    const handleStorageChange = () => {
      setSessionKey(prev => prev + 1);
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const loadCategories = async () => {
    try {
      const response = await categoriesAPI.getCategories();
      setCategories(response.data);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const loadItems = async () => {
    setLoading(true);
    setError('');

    try {
      const params = {
        status: statusFilter,
        search,
        sort_by: sortBy,
        sort_order: sortOrder,
      };

      if (categoryFilter) {
        params.category_id = categoryFilter;
      }

      const response = await itemsAPI.getItems(params);
      setItems(response.data);
    } catch (err) {
      setError('Failed to load items. Please try again.');
      console.error('Failed to load items:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = () => {
    setEditingItem(null);
    setShowAddModal(true);
  };

  const handleEditItem = (item) => {
    setEditingItem(item);
    setShowAddModal(true);
  };

  const handleItemSaved = (keepOpen = false) => {
    if (!keepOpen) {
      setShowAddModal(false);
      setEditingItem(null);
    }
    loadItems();
    // Refresh session banner
    setSessionKey(prev => prev + 1);
  };

  const handleStatusChange = async (itemId, newStatus) => {
    try {
      await itemsAPI.updateItemStatus(itemId, newStatus);
      loadItems();
    } catch (err) {
      console.error('Failed to update item status:', err);
      alert('Failed to update item status');
    }
  };

  const handleQRSubmit = async (qrCode) => {
    try {
      const response = await itemsAPI.getItemByQR(qrCode);
      const item = response.data;

      // Show item details and action options
      const action = window.confirm(
        `Item Found: ${item.name}\n\n` +
        `Category: ${item.category_name || 'N/A'}\n` +
        `Source: ${item.source || 'N/A'}\n` +
        `Added: ${new Date(item.added_date).toLocaleDateString()}\n` +
        `Status: ${item.status}\n\n` +
        `Click OK to mark as consumed, Cancel to edit`
      );

      if (action) {
        await handleStatusChange(item.id, 'consumed');
      } else {
        handleEditItem(item);
      }

      setShowQRModal(false);
    } catch (err) {
      if (err.response?.status === 404) {
        // Item not found, create new
        const create = window.confirm(
          `Item code not found in database.\n\nWould you like to create a new item with this code?`
        );

        if (create) {
          setEditingItem({ qr_code: qrCode });
          setShowAddModal(true);
        }
      } else {
        alert('Failed to lookup item code');
      }
      setShowQRModal(false);
    }
  };

  const handlePurgeAllItems = async () => {
    // Double confirmation for safety
    const firstConfirm = window.confirm(
      '⚠️ WARNING: This will permanently delete ALL items from the database!\n\n' +
      'This includes:\n' +
      '• Items in freezer\n' +
      '• Consumed items\n' +
      '• Thrown out items\n\n' +
      'This action CANNOT be undone!\n\n' +
      'Are you sure you want to continue?'
    );

    if (!firstConfirm) return;

    // Second confirmation
    const secondConfirm = window.confirm(
      '⚠️ FINAL WARNING ⚠️\n\n' +
      'You are about to delete ALL items permanently.\n\n' +
      'Click OK to proceed with deletion, or Cancel to abort.'
    );

    if (!secondConfirm) return;

    try {
      setLoading(true);
      const response = await itemsAPI.purgeAllItems();
      alert(response.data.message || 'All items purged successfully');
      loadItems();
    } catch (err) {
      console.error('Failed to purge items:', err);
      const errorMsg = err.response?.data?.error || 'Failed to purge items';
      alert(`Error: ${errorMsg}`);
      setLoading(false);
    }
  };

  const handleCopyProdDb = async () => {
    // Confirmation for database copy
    const confirm = window.confirm(
      '📋 Copy Production Database to Dev?\n\n' +
      'This will:\n' +
      '• Replace the current dev database with production data\n' +
      '• Create a backup of the current dev database\n' +
      '• Reload all items from production\n\n' +
      'Are you sure you want to continue?'
    );

    if (!confirm) return;

    try {
      setLoading(true);
      const response = await itemsAPI.copyProdDb();
      const msg = response.data.message || 'Production database copied successfully';
      const count = response.data.items_count || 0;
      alert(`${msg}\n\nItems loaded: ${count}`);
      loadItems();
    } catch (err) {
      console.error('Failed to copy prod database:', err);
      const errorMsg = err.response?.data?.error || 'Failed to copy production database';
      alert(`Error: ${errorMsg}`);
      setLoading(false);
    }
  };

  // Analyze items for warnings
  const expiringSoonCount = items.filter(item => {
    if (item.status !== 'in_freezer' || !item.expiration_date) return false;
    const daysUntilExpiry = Math.floor(
      (new Date(item.expiration_date) - new Date()) / (1000 * 60 * 60 * 24)
    );
    return daysUntilExpiry <= 30 && daysUntilExpiry >= 0;
  }).length;

  const expiredCount = items.filter(item => {
    if (item.status !== 'in_freezer' || !item.expiration_date) return false;
    return new Date(item.expiration_date) < new Date();
  }).length;

  return (
    <div className="container">
      <SessionBanner key={sessionKey} />

      <div className="inventory-header">
        <div>
          <h2>Freezer Inventory</h2>
          {expiringSoonCount > 0 && (
            <p style={{ color: '#f39c12', marginTop: '0.5rem' }}>
              ⚠️ {expiringSoonCount} item(s) expiring soon
            </p>
          )}
          {expiredCount > 0 && (
            <p style={{ color: '#e74c3c', marginTop: '0.5rem' }}>
              🚨 {expiredCount} item(s) expired
            </p>
          )}
        </div>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={() => setShowQRModal(true)}>
            🔍 Locate Item by Code
          </button>
          <button className="btn btn-secondary" onClick={() => setShowQRScanner(true)}>
            📷 Scan QR Code
          </button>
          <button className="btn btn-success" onClick={handleAddItem}>
            ➕ Add Item
          </button>
          {isDev && (
            <>
              <button
                className="btn btn-primary"
                onClick={handleCopyProdDb}
                style={{ marginLeft: 'auto' }}
              >
                📋 Copy Prod DB
              </button>
              <button
                className="btn btn-danger"
                onClick={handlePurgeAllItems}
              >
                🗑️ Purge All Items
              </button>
            </>
          )}
        </div>
      </div>

      <div className="search-filters">
        <div className="search-row">
          <div className="form-group">
            <label>Search</label>
            <input
              type="text"
              placeholder="Search by name, source, or notes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Category</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="in_freezer">In Freezer</option>
              <option value="consumed">Consumed</option>
              <option value="thrown_out">Thrown Out</option>
              <option value="all">All</option>
            </select>
          </div>
        </div>

        <div className="filter-row">
          <div className="form-group">
            <label>Sort By</label>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="added_date">Date Added</option>
              <option value="expiration_date">Expiration Date</option>
              <option value="name">Name</option>
            </select>
          </div>
          <div className="form-group">
            <label>Order</label>
            <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value)}>
              <option value="desc">Newest First</option>
              <option value="asc">Oldest First</option>
            </select>
          </div>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">Loading items...</div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <h3>No items found</h3>
          <p>Add your first item to get started!</p>
        </div>
      ) : (
        <div className="items-grid">
          {items.map((item) => (
            <ItemCard
              key={item.id}
              item={item}
              onEdit={() => handleEditItem(item)}
              onStatusChange={(status) => handleStatusChange(item.id, status)}
            />
          ))}
        </div>
      )}

      {showAddModal && (
        <AddItemModal
          item={editingItem}
          categories={categories}
          onClose={() => {
            setShowAddModal(false);
            setEditingItem(null);
          }}
          onSave={handleItemSaved}
          onCategoryCreated={loadCategories}
        />
      )}

      {showQRModal && (
        <QRInputModal
          onClose={() => setShowQRModal(false)}
          onSubmit={handleQRSubmit}
        />
      )}

      {showQRScanner && (
        <QRScanner
          onClose={() => setShowQRScanner(false)}
          onScan={(item) => {
            setShowQRScanner(false);
            setEditingItem(item);
            setShowAddModal(true);
          }}
        />
      )}
    </div>
  );
}

export default Inventory;
