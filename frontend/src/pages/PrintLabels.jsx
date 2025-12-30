import { useState, useEffect } from 'react';
import { itemsAPI, categoriesAPI } from '../services/api';

function PrintLabels() {
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  // Label options
  const [showName, setShowName] = useState(true);
  const [showExpiration, setShowExpiration] = useState(true);
  const [showCategory, setShowCategory] = useState(false);
  const [showWeight, setShowWeight] = useState(false);

  useEffect(() => {
    fetchItems();
    fetchCategories();
  }, []);

  const fetchItems = async () => {
    try {
      setLoading(true);
      const response = await itemsAPI.getItems({ status: 'in_freezer' });
      setItems(response.data);
    } catch (err) {
      setError('Failed to load items');
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await categoriesAPI.getCategories();
      setCategories(response.data);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const handleSelectAll = () => {
    if (selectedItems.length === filteredItems.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(filteredItems.map(item => item.id));
    }
  };

  const handleSelectItem = (itemId) => {
    if (selectedItems.includes(itemId)) {
      setSelectedItems(selectedItems.filter(id => id !== itemId));
    } else {
      setSelectedItems([...selectedItems, itemId]);
    }
  };

  const handlePrintLabels = async () => {
    if (selectedItems.length === 0) {
      setError('Please select at least one item');
      return;
    }

    try {
      setError('');
      await itemsAPI.printLabels(selectedItems, {
        show_name: showName,
        show_expiration: showExpiration,
        show_category: showCategory,
        show_weight: showWeight,
      });
      // PDF will download automatically
    } catch (err) {
      setError('Failed to generate labels: ' + (err.message || 'Unknown error'));
    }
  };

  // Filter items based on search and category
  const filteredItems = items.filter(item => {
    const matchesSearch = searchTerm === '' ||
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.qr_code && item.qr_code.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesCategory = filterCategory === '' || item.category_id === parseInt(filterCategory);

    return matchesSearch && matchesCategory;
  });

  if (loading) {
    return (
      <div className="container">
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div className="loading-spinner"></div>
          <p>Loading items...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="page-header">
        <h1>🏷️ Print QR Code Labels</h1>
        <p>Select items to print labels for physical labeling of freezer items</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>Label Options</h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input
              type="checkbox"
              checked={showName}
              onChange={(e) => setShowName(e.target.checked)}
            />
            <span>Show Item Name</span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input
              type="checkbox"
              checked={showExpiration}
              onChange={(e) => setShowExpiration(e.target.checked)}
            />
            <span>Show Expiration Date</span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input
              type="checkbox"
              checked={showCategory}
              onChange={(e) => setShowCategory(e.target.checked)}
            />
            <span>Show Category</span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input
              type="checkbox"
              checked={showWeight}
              onChange={(e) => setShowWeight(e.target.checked)}
            />
            <span>Show Size/Weight</span>
          </label>
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
          <button
            onClick={handlePrintLabels}
            className="btn btn-primary"
            disabled={selectedItems.length === 0}
          >
            🖨️ Generate Labels ({selectedItems.length} selected)
          </button>

          <button
            onClick={() => setSelectedItems([])}
            className="btn btn-secondary"
            disabled={selectedItems.length === 0}
          >
            Clear Selection
          </button>
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Search items..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ flex: 1, minWidth: '200px' }}
          />

          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            style={{ minWidth: '150px' }}
          >
            <option value="">All Categories</option>
            {categories.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>

          <button
            onClick={handleSelectAll}
            className="btn btn-secondary"
          >
            {selectedItems.length === filteredItems.length ? 'Deselect All' : 'Select All'}
          </button>
        </div>

        <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1rem' }}>
          Showing {filteredItems.length} items
        </div>

        <div className="items-table">
          <table>
            <thead>
              <tr>
                <th style={{ width: '40px' }}>
                  <input
                    type="checkbox"
                    checked={selectedItems.length === filteredItems.length && filteredItems.length > 0}
                    onChange={handleSelectAll}
                  />
                </th>
                <th>Code</th>
                <th>Name</th>
                <th>Category</th>
                <th>Size</th>
                <th>Expires</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                    No items found
                  </td>
                </tr>
              ) : (
                filteredItems.map(item => (
                  <tr key={item.id} style={{ cursor: 'pointer' }} onClick={() => handleSelectItem(item.id)}>
                    <td onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selectedItems.includes(item.id)}
                        onChange={() => handleSelectItem(item.id)}
                      />
                    </td>
                    <td>
                      <code style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                        {item.qr_code}
                      </code>
                    </td>
                    <td>{item.name}</td>
                    <td>{item.category_name || '-'}</td>
                    <td>
                      {item.weight ? `${item.weight} ${item.weight_unit}` : '-'}
                    </td>
                    <td>
                      {item.expiration_date
                        ? new Date(item.expiration_date).toLocaleDateString()
                        : '-'
                      }
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card" style={{ marginTop: '1.5rem', background: '#f8f9fa' }}>
        <h3 style={{ marginBottom: '0.5rem' }}>💡 Tips</h3>
        <ul style={{ marginLeft: '1.5rem', lineHeight: '1.6' }}>
          <li>Labels are 1.5" x 1.5" squares, designed for standard label sheets</li>
          <li>Each sheet fits 4 columns of labels across a letter-sized page</li>
          <li>Use the checkboxes above to customize what information appears on each label</li>
          <li>The QR code and alphanumeric code always appear on every label</li>
          <li>A PDF will download automatically - open and print it when ready</li>
          <li>No need to adjust browser print settings - PDFs print perfectly every time</li>
        </ul>
      </div>
    </div>
  );
}

export default PrintLabels;
