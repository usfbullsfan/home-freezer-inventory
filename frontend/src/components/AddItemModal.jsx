import { useState, useEffect } from 'react';
import { itemsAPI } from '../services/api';

function AddItemModal({ item, categories, onClose, onSave }) {
  const [formData, setFormData] = useState({
    qr_code: '',
    upc: '',
    name: '',
    source: '',
    weight: '',
    weight_unit: 'lb',
    category_id: '',
    added_date: '',
    expiration_date: '',
    notes: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [upcLookupLoading, setUpcLookupLoading] = useState(false);
  const [upcMessage, setUpcMessage] = useState('');

  useEffect(() => {
    if (item) {
      setFormData({
        qr_code: item.qr_code || '',
        upc: item.upc || '',
        name: item.name || '',
        source: item.source || '',
        weight: item.weight || '',
        weight_unit: item.weight_unit || 'lb',
        category_id: item.category_id || '',
        added_date: item.added_date
          ? new Date(item.added_date).toISOString().split('T')[0]
          : '',
        expiration_date: item.expiration_date
          ? new Date(item.expiration_date).toISOString().split('T')[0]
          : '',
        notes: item.notes || '',
      });
    }
  }, [item]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleCategoryChange = (e) => {
    const categoryId = e.target.value;
    setFormData((prev) => ({ ...prev, category_id: categoryId }));

    // Auto-calculate expiration date based on category default
    if (categoryId && !formData.expiration_date) {
      const category = categories.find((c) => c.id === parseInt(categoryId));
      if (category && category.default_expiration_days) {
        const expirationDate = new Date();
        expirationDate.setDate(expirationDate.getDate() + category.default_expiration_days);
        setFormData((prev) => ({
          ...prev,
          expiration_date: expirationDate.toISOString().split('T')[0],
        }));
      }
    }
  };

  const handleLookupUPC = async () => {
    if (!formData.upc || !formData.upc.trim()) {
      setUpcMessage('Please enter a UPC code');
      return;
    }

    setUpcLookupLoading(true);
    setUpcMessage('');
    setError('');

    try {
      const response = await itemsAPI.lookupUPC(formData.upc.trim());
      const result = response.data;

      setUpcMessage(result.message);

      if (result.found && result.data) {
        // Auto-fill form fields with UPC lookup data
        setFormData(prev => ({
          ...prev,
          name: result.data.name || prev.name,
          source: result.data.brand || prev.source,
          notes: result.data.notes || prev.notes,
          category_id: result.data.category_id || prev.category_id,
        }));
      }
    } catch (err) {
      setError('Failed to lookup UPC. Please try again or enter details manually.');
    } finally {
      setUpcLookupLoading(false);
    }
  };

  const handleSubmit = async (e, keepOpen = false) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const submitData = {
        ...formData,
        weight: formData.weight ? parseFloat(formData.weight) : null,
        category_id: formData.category_id ? parseInt(formData.category_id) : null,
        upc: formData.upc || null,
      };

      if (item && item.id) {
        // Update existing item
        await itemsAPI.updateItem(item.id, submitData);
      } else {
        // Create new item
        await itemsAPI.createItem(submitData);
      }

      if (keepOpen) {
        // Reset form for next entry, but keep category selected
        const savedCategoryId = formData.category_id;
        const savedCategoryExpiration = formData.expiration_date;

        setFormData({
          qr_code: '',
          upc: '',
          name: '',
          source: '',
          weight: '',
          weight_unit: 'lb',
          category_id: savedCategoryId,
          added_date: '',
          expiration_date: savedCategoryExpiration,
          notes: '',
        });
        setUpcMessage('');

        // Trigger a soft refresh to update the items list in the background
        onSave(true);
      } else {
        onSave();
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save item. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddAndCreateMore = (e) => {
    handleSubmit(e, true);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{item && item.id ? 'Edit Item' : 'Add New Item'}</h2>
        </div>

        <div className="modal-content">
          {error && <div className="error-message">{error}</div>}
          {upcMessage && (
            <div className={upcMessage.includes('already have') || upcMessage.includes('Found product') ? 'success-message' : 'error-message'} style={{ fontSize: '0.9rem' }}>
              {upcMessage}
            </div>
          )}

          <form onSubmit={handleSubmit} id="item-form">
          {/* UPC Lookup Section */}
          <div style={{
            background: '#f8f9fa',
            padding: '1rem',
            borderRadius: '6px',
            marginBottom: '1rem',
            border: '1px solid #e0e0e0'
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.5rem' }}>
              <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                <label htmlFor="upc" style={{ fontSize: '0.9rem', marginBottom: '0.35rem' }}>
                  UPC / Barcode (Optional)
                </label>
                <input
                  type="text"
                  id="upc"
                  name="upc"
                  value={formData.upc}
                  onChange={handleChange}
                  placeholder="e.g., 012345678901"
                  style={{ padding: '0.65rem' }}
                />
              </div>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleLookupUPC}
                disabled={upcLookupLoading || !formData.upc}
                style={{
                  padding: '0.65rem 1rem',
                  fontSize: '0.9rem',
                  whiteSpace: 'nowrap'
                }}
              >
                {upcLookupLoading ? '🔍 Looking up...' : '🔍 Lookup'}
              </button>
            </div>
            <small style={{ color: '#6c757d', display: 'block', marginTop: '0.5rem', fontSize: '0.8rem' }}>
              Scan or enter the barcode to auto-fill product details
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="name">Item Name *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              placeholder="e.g., Prime Ribeye Steak"
            />
          </div>

          <div className="form-row form-row-2">
            <div className="form-group">
              <label htmlFor="source">Source</label>
              <input
                type="text"
                id="source"
                name="source"
                value={formData.source}
                onChange={handleChange}
                placeholder="e.g., Costco"
              />
            </div>

            <div className="form-group">
              <label htmlFor="category_id">Category</label>
              <select
                id="category_id"
                name="category_id"
                value={formData.category_id}
                onChange={handleCategoryChange}
              >
                <option value="">Select</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row form-row-3">
            <div className="form-group">
              <label htmlFor="weight">Weight</label>
              <input
                type="number"
                id="weight"
                name="weight"
                value={formData.weight}
                onChange={handleChange}
                step="0.01"
                placeholder="e.g., 1.5"
              />
            </div>

            <div className="form-group">
              <label htmlFor="weight_unit">Unit</label>
              <select
                id="weight_unit"
                name="weight_unit"
                value={formData.weight_unit}
                onChange={handleChange}
              >
                <option value="lb">lb</option>
                <option value="oz">oz</option>
                <option value="kg">kg</option>
                <option value="g">g</option>
              </select>
            </div>
          </div>

          <div className="form-row form-row-2">
            <div className="form-group">
              <label htmlFor="added_date">Date Added</label>
              <input
                type="date"
                id="added_date"
                name="added_date"
                value={formData.added_date}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label htmlFor="expiration_date">Expires</label>
              <input
                type="date"
                id="expiration_date"
                name="expiration_date"
                value={formData.expiration_date}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="qr_code">QR Code (optional)</label>
            <input
              type="text"
              id="qr_code"
              name="qr_code"
              value={formData.qr_code}
              onChange={handleChange}
              placeholder="Auto-generated if blank"
              disabled={item && item.id}
            />
          </div>

          <div className="form-group">
            <label htmlFor="notes">Notes (optional)</label>
            <textarea
              id="notes"
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              rows="2"
              placeholder="Additional notes..."
            />
          </div>
          </form>
        </div>

        <div className="modal-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </button>
          {!item?.id && (
            <button
              type="button"
              className="btn btn-success"
              onClick={handleAddAndCreateMore}
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Add + Create More'}
            </button>
          )}
          <button
            type="submit"
            form="item-form"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Saving...' : item && item.id ? 'Update Item' : 'Add Item'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default AddItemModal;
