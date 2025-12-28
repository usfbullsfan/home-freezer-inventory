import { useState, useEffect } from 'react';
import { itemsAPI } from '../services/api';

function AddItemModal({ item, categories, onClose, onSave }) {
  const [formData, setFormData] = useState({
    qr_code: '',
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

  useEffect(() => {
    if (item) {
      setFormData({
        qr_code: item.qr_code || '',
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

  const handleSubmit = async (e, keepOpen = false) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const submitData = {
        ...formData,
        weight: formData.weight ? parseFloat(formData.weight) : null,
        category_id: formData.category_id ? parseInt(formData.category_id) : null,
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
          name: '',
          source: '',
          weight: '',
          weight_unit: 'lb',
          category_id: savedCategoryId,
          added_date: '',
          expiration_date: savedCategoryExpiration,
          notes: '',
        });

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

          <form onSubmit={handleSubmit} id="item-form">
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

          <div className="form-group">
            <label htmlFor="qr_code">QR Code / Barcode</label>
            <input
              type="text"
              id="qr_code"
              name="qr_code"
              value={formData.qr_code}
              onChange={handleChange}
              placeholder="Leave blank to auto-generate"
              disabled={item && item.id} // Can't change QR code of existing item
            />
            {formData.qr_code && (
              <small style={{ color: '#7f8c8d' }}>
                This code will be used to identify this item
              </small>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="source">Source</label>
            <input
              type="text"
              id="source"
              name="source"
              value={formData.source}
              onChange={handleChange}
              placeholder="e.g., Costco, Butcher Shop"
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
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

          <div className="form-group">
            <label htmlFor="category_id">Category</label>
            <select
              id="category_id"
              name="category_id"
              value={formData.category_id}
              onChange={handleCategoryChange}
            >
              <option value="">Select a category</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name} (default {cat.default_expiration_days} days)
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="added_date">Date Added to Freezer</label>
            <input
              type="date"
              id="added_date"
              name="added_date"
              value={formData.added_date}
              onChange={handleChange}
            />
            <small style={{ color: '#7f8c8d' }}>
              Leave blank to use today's date
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="expiration_date">Expiration Date</label>
            <input
              type="date"
              id="expiration_date"
              name="expiration_date"
              value={formData.expiration_date}
              onChange={handleChange}
            />
            <small style={{ color: '#7f8c8d' }}>
              Leave blank to use category default, or enter specific date
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="notes">Notes</label>
            <textarea
              id="notes"
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              rows="3"
              placeholder="Any additional notes about this item..."
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
