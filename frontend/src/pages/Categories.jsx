import { useState, useEffect } from 'react';
import { categoriesAPI } from '../services/api';

function Categories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [showForm, setShowForm] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    default_expiration_days: 180,
  });

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await categoriesAPI.getCategories();
      setCategories(response.data);
    } catch (err) {
      setError('Failed to load categories');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingCategory(null);
    setFormData({ name: '', default_expiration_days: 180 });
    setShowForm(true);
  };

  const handleEdit = (category) => {
    setEditingCategory(category);
    setFormData({
      name: category.name,
      default_expiration_days: category.default_expiration_days,
    });
    setShowForm(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      if (editingCategory) {
        await categoriesAPI.updateCategory(editingCategory.id, formData);
        setSuccess('Category updated successfully');
      } else {
        await categoriesAPI.createCategory(formData);
        setSuccess('Category created successfully');
      }

      setShowForm(false);
      loadCategories();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to save category');
    }
  };

  const handleDelete = async (category) => {
    if (category.is_system) {
      alert('Cannot delete system categories');
      return;
    }

    if (!window.confirm(`Are you sure you want to delete "${category.name}"?`)) {
      return;
    }

    try {
      await categoriesAPI.deleteCategory(category.id);
      setSuccess('Category deleted successfully');
      loadCategories();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to delete category');
    }
  };

  return (
    <div className="container">
      <div className="inventory-header">
        <h2>Categories</h2>
        <button className="btn btn-success" onClick={handleAdd}>
          ➕ Add Category
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      {loading ? (
        <div className="loading">Loading categories...</div>
      ) : (
        <div style={{ background: 'white', padding: '1.5rem', borderRadius: '8px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd' }}>
                <th style={{ padding: '1rem', textAlign: 'left' }}>Name</th>
                <th style={{ padding: '1rem', textAlign: 'left' }}>Default Expiration</th>
                <th style={{ padding: '1rem', textAlign: 'left' }}>Type</th>
                <th style={{ padding: '1rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {categories.map((category) => (
                <tr key={category.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '1rem' }}>{category.name}</td>
                  <td style={{ padding: '1rem' }}>{category.default_expiration_days} days</td>
                  <td style={{ padding: '1rem' }}>
                    {category.is_system && (
                      <span className="status-badge status-in_freezer">System</span>
                    )}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'right' }}>
                    <button
                      className="btn btn-primary"
                      onClick={() => handleEdit(category)}
                      style={{ marginRight: '0.5rem', padding: '0.5rem 1rem' }}
                    >
                      Edit
                    </button>
                    {!category.is_system && (
                      <button
                        className="btn btn-danger"
                        onClick={() => handleDelete(category)}
                        style={{ padding: '0.5rem 1rem' }}
                      >
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{editingCategory ? 'Edit Category' : 'Add New Category'}</h2>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="name">Category Name *</label>
                <input
                  type="text"
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  placeholder="e.g., Lamb"
                />
              </div>

              <div className="form-group">
                <label htmlFor="default_expiration_days">Default Expiration (days) *</label>
                <input
                  type="number"
                  id="default_expiration_days"
                  value={formData.default_expiration_days}
                  onChange={(e) =>
                    setFormData({ ...formData, default_expiration_days: parseInt(e.target.value) })
                  }
                  required
                  min="1"
                />
                <small style={{ color: '#7f8c8d' }}>
                  Items in this category will default to this expiration period
                </small>
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowForm(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingCategory ? 'Update Category' : 'Add Category'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Categories;
