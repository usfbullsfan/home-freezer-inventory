import { useState, useEffect } from 'react';
import { categoriesAPI, uploadsAPI } from '../services/api';

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
    image_url: '',
  });
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [formError, setFormError] = useState('');

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
    setFormData({ name: '', default_expiration_days: 180, image_url: '' });
    setSelectedFile(null);
    setFormError('');
    setShowForm(true);
  };

  const handleEdit = (category) => {
    setEditingCategory(category);
    setFormData({
      name: category.name,
      default_expiration_days: category.default_expiration_days,
      image_url: category.image_url || '',
    });
    setSelectedFile(null);
    setFormError('');
    setShowForm(true);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        setFormError('Invalid file type. Please select an image (PNG, JPEG, GIF, or WebP).');
        e.target.value = '';
        return;
      }

      // Validate file size (5MB)
      if (file.size > 5 * 1024 * 1024) {
        setFormError('File too large. Maximum size is 5MB.');
        e.target.value = '';
        return;
      }

      setSelectedFile(file);
      setFormError('');

      // Create a preview URL
      const reader = new FileReader();
      reader.onload = (e) => {
        setFormData(prev => ({ ...prev, image_url: e.target.result }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setFormError('');

    let imageUrl = formData.image_url;

    // Upload file if one is selected
    if (selectedFile) {
      setUploadingImage(true);
      try {
        const response = await uploadsAPI.uploadCategoryImage(selectedFile);
        imageUrl = response.data.image_url;
      } catch (err) {
        setFormError(err.response?.data?.error || 'Failed to upload image');
        setUploadingImage(false);
        return;
      }
      setUploadingImage(false);
    }

    try {
      const submitData = {
        ...formData,
        image_url: imageUrl || formData.image_url || null,
      };

      if (editingCategory) {
        await categoriesAPI.updateCategory(editingCategory.id, submitData);
        setSuccess('Category updated successfully');
      } else {
        await categoriesAPI.createCategory(submitData);
        setSuccess('Category created successfully');
      }

      setShowForm(false);
      setSelectedFile(null);
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
            <div className="modal-header">
              <h2>{editingCategory ? 'Edit Category' : 'Add New Category'}</h2>
            </div>

            <div className="modal-content">
              {formError && <div className="error-message">{formError}</div>}
              <form onSubmit={handleSubmit} id="category-form">
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

                <div className="form-group">
                  <label>Default Image (optional)</label>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => document.getElementById('file-upload').click()}
                      style={{ flex: 1 }}
                      disabled={uploadingImage}
                    >
                      {selectedFile ? '✓ File Selected' : '📁 Upload Image'}
                    </button>
                    <span style={{ color: '#95a5a6' }}>or</span>
                    <input
                      type="url"
                      value={selectedFile ? '' : formData.image_url}
                      onChange={(e) => {
                        setSelectedFile(null);
                        setFormData({ ...formData, image_url: e.target.value });
                      }}
                      placeholder="Enter URL"
                      style={{ flex: 2 }}
                      disabled={selectedFile || uploadingImage}
                    />
                  </div>
                  <input
                    type="file"
                    id="file-upload"
                    accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                  />
                  <small style={{ color: '#7f8c8d', display: 'block' }}>
                    {selectedFile
                      ? `Selected: ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)`
                      : 'Upload an image or enter a URL. Leave blank to use default stock images.'}
                  </small>
                </div>

                {formData.image_url && (
                  <div style={{
                    display: 'flex',
                    justifyContent: 'center',
                    padding: '1rem',
                    background: '#f8f9fa',
                    borderRadius: '6px',
                    marginTop: '0.5rem'
                  }}>
                    <img
                      src={formData.image_url}
                      alt="Category preview"
                      style={{
                        maxWidth: '200px',
                        maxHeight: '200px',
                        objectFit: 'contain',
                        borderRadius: '4px'
                      }}
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  </div>
                )}
              </form>
            </div>

            <div className="modal-actions">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowForm(false)}
              >
                Cancel
              </button>
              <button type="submit" form="category-form" className="btn btn-primary">
                {editingCategory ? 'Update Category' : 'Add Category'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Categories;
