import { useState, useEffect } from 'react';
import api from '../services/api';

/**
 * Admin-only data cleanup panel for fixing/removing duplicate item names and
 * store (source) values that pollute the autocomplete suggestion list.
 *
 * - Rename: bulk-renames a value across all item records (all statuses)
 * - Delete: for names, permanently deletes all item records; for sources,
 *   clears the source field. Both are blocked when active (in-freezer) items
 *   still use the value.
 */
function DataCleanup() {
  const [activeTab, setActiveTab] = useState('names');
  const [names, setNames] = useState([]);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  // { value: string, newValue: string }
  const [renaming, setRenaming] = useState(null);
  // { value: string, totalCount: number, type: 'names'|'sources' }
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [namesRes, sourcesRes] = await Promise.all([
        api.get('/admin/cleanup/names'),
        api.get('/admin/cleanup/sources'),
      ]);
      setNames(namesRes.data);
      setSources(sourcesRes.data);
    } catch {
      setError('Failed to load cleanup data');
    } finally {
      setLoading(false);
    }
  };

  const handleRenameStart = (value) => {
    setConfirmDelete(null);
    setRenaming({ value, newValue: value });
    setError('');
    setSuccess('');
  };

  const handleRenameSubmit = async (e) => {
    e.preventDefault();
    if (!renaming) return;
    const trimmed = renaming.newValue.trim();
    if (!trimmed || trimmed === renaming.value) {
      setRenaming(null);
      return;
    }
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      let res;
      if (activeTab === 'names') {
        res = await api.patch('/admin/cleanup/names', { old_name: renaming.value, new_name: trimmed });
        setSuccess(`Renamed to "${trimmed}" — ${res.data.updated_count} item(s) updated`);
      } else {
        res = await api.patch('/admin/cleanup/sources', { old_source: renaming.value, new_source: trimmed });
        setSuccess(`Renamed to "${trimmed}" — ${res.data.updated_count} item(s) updated`);
      }
      setRenaming(null);
      loadData();
    } catch (err) {
      setError(err.response?.data?.error || 'Rename failed');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!confirmDelete) return;
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      if (confirmDelete.type === 'names') {
        const res = await api.delete('/admin/cleanup/names', { data: { name: confirmDelete.value } });
        setSuccess(`Deleted ${res.data.deleted_count} item record(s) for "${confirmDelete.value}"`);
      } else {
        const res = await api.delete('/admin/cleanup/sources', { data: { source: confirmDelete.value } });
        setSuccess(`Cleared store "${confirmDelete.value}" from ${res.data.updated_count} item(s)`);
      }
      setConfirmDelete(null);
      loadData();
    } catch (err) {
      setError(err.response?.data?.error || 'Delete failed');
      setConfirmDelete(null);
    } finally {
      setSaving(false);
    }
  };

  const rows = activeTab === 'names' ? names : sources;
  const valueKey = activeTab === 'names' ? 'name' : 'source';
  const colLabel = activeTab === 'names' ? 'Item Name' : 'Store Name';

  const tabStyle = (tab) => ({
    padding: '0.4rem 1rem',
    border: '1px solid #dee2e6',
    borderBottom: activeTab === tab ? '1px solid white' : '1px solid #dee2e6',
    borderRadius: '4px 4px 0 0',
    background: activeTab === tab ? 'white' : '#f8f9fa',
    cursor: 'pointer',
    fontWeight: activeTab === tab ? '600' : 'normal',
    marginRight: '0.25rem',
    fontSize: '0.9rem',
    color: activeTab === tab ? '#212529' : '#6c757d',
    position: 'relative',
    bottom: '-1px',
  });

  const btnStyle = (variant = 'default') => {
    const base = {
      padding: '0.2rem 0.55rem',
      borderRadius: '4px',
      fontSize: '0.8rem',
      cursor: 'pointer',
      border: '1px solid',
      lineHeight: '1.4',
    };
    if (variant === 'danger') return { ...base, background: '#fff5f5', borderColor: '#f5c2c7', color: '#842029' };
    if (variant === 'primary') return { ...base, background: '#e7f1ff', borderColor: '#b6d4fe', color: '#084298' };
    if (variant === 'success') return { ...base, background: '#d1e7dd', borderColor: '#a3cfbb', color: '#0a3622' };
    if (variant === 'disabled') return { ...base, background: '#f8f9fa', borderColor: '#dee2e6', color: '#adb5bd', cursor: 'not-allowed' };
    return { ...base, background: '#f8f9fa', borderColor: '#dee2e6', color: '#495057' };
  };

  return (
    <div>
      <p style={{ margin: '0 0 1rem', fontSize: '0.9rem', color: '#6c757d' }}>
        View and fix duplicate or misspelled item names and store names that appear in autocomplete suggestions.
        Rename merges all records to the new value; delete removes historical records (blocked if items are currently in the freezer).
      </p>

      {error && (
        <div style={{ background: '#f8d7da', border: '1px solid #f5c2c7', color: '#842029', padding: '0.6rem 0.9rem', borderRadius: '4px', marginBottom: '0.75rem', fontSize: '0.875rem' }}>
          {error}
        </div>
      )}
      {success && (
        <div style={{ background: '#d1e7dd', border: '1px solid #a3cfbb', color: '#0a3622', padding: '0.6rem 0.9rem', borderRadius: '4px', marginBottom: '0.75rem', fontSize: '0.875rem' }}>
          {success}
        </div>
      )}

      {/* Tabs */}
      <div style={{ marginBottom: '-1px' }}>
        <button style={tabStyle('names')} onClick={() => { setActiveTab('names'); setRenaming(null); setConfirmDelete(null); }}>
          Item Names {names.length > 0 && <span style={{ color: '#6c757d', fontWeight: 'normal' }}>({names.length})</span>}
        </button>
        <button style={tabStyle('sources')} onClick={() => { setActiveTab('sources'); setRenaming(null); setConfirmDelete(null); }}>
          Store Names {sources.length > 0 && <span style={{ color: '#6c757d', fontWeight: 'normal' }}>({sources.length})</span>}
        </button>
      </div>

      {/* Table */}
      <div style={{ border: '1px solid #dee2e6', borderRadius: '0 4px 4px 4px', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#6c757d' }}>Loading…</div>
        ) : rows.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#6c757d' }}>No data found.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: '#f8f9fa', borderBottom: '1px solid #dee2e6' }}>
                <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', fontWeight: '600', color: '#495057' }}>{colLabel}</th>
                <th style={{ padding: '0.5rem 0.75rem', textAlign: 'center', fontWeight: '600', color: '#495057', whiteSpace: 'nowrap' }}>In Freezer</th>
                <th style={{ padding: '0.5rem 0.75rem', textAlign: 'center', fontWeight: '600', color: '#495057' }}>Total</th>
                <th style={{ padding: '0.5rem 0.75rem', textAlign: 'right', fontWeight: '600', color: '#495057' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => {
                const val = row[valueKey];
                const isRenaming = renaming?.value === val;
                const isConfirmingDelete = confirmDelete?.value === val;
                const canDelete = row.active_count === 0;
                const deleteTooltip = canDelete
                  ? ''
                  : `${row.active_count} item(s) currently in the freezer — rename or remove them first`;

                return (
                  <tr
                    key={val}
                    style={{
                      borderBottom: idx < rows.length - 1 ? '1px solid #f0f0f0' : 'none',
                      background: isRenaming || isConfirmingDelete ? '#f8f9fa' : 'white',
                    }}
                  >
                    {/* Name/source cell — shows input when renaming */}
                    <td style={{ padding: '0.45rem 0.75rem' }}>
                      {isRenaming ? (
                        <form onSubmit={handleRenameSubmit} style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                          <input
                            autoFocus
                            type="text"
                            value={renaming.newValue}
                            onChange={(e) => setRenaming({ ...renaming, newValue: e.target.value })}
                            style={{ flex: 1, padding: '0.2rem 0.4rem', border: '1px solid #86b7fe', borderRadius: '4px', fontSize: '0.875rem', outline: 'none' }}
                          />
                          <button type="submit" style={btnStyle('success')} disabled={saving}>Save</button>
                          <button type="button" style={btnStyle()} onClick={() => setRenaming(null)}>Cancel</button>
                        </form>
                      ) : isConfirmingDelete ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ color: '#842029' }}>
                            {activeTab === 'names'
                              ? `Delete all ${row.total_count} record(s) for "${val}"?`
                              : `Clear store "${val}" from ${row.total_count} record(s)?`}
                          </span>
                        </div>
                      ) : (
                        <span style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{val}</span>
                      )}
                    </td>

                    <td style={{ padding: '0.45rem 0.75rem', textAlign: 'center' }}>
                      <span style={{
                        fontWeight: row.active_count > 0 ? '600' : 'normal',
                        color: row.active_count > 0 ? '#0a3622' : '#6c757d',
                      }}>
                        {row.active_count}
                      </span>
                    </td>

                    <td style={{ padding: '0.45rem 0.75rem', textAlign: 'center', color: '#6c757d' }}>
                      {row.total_count}
                    </td>

                    {/* Actions cell */}
                    <td style={{ padding: '0.45rem 0.75rem', textAlign: 'right', whiteSpace: 'nowrap' }}>
                      {isConfirmingDelete ? (
                        <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end' }}>
                          <button style={btnStyle('danger')} onClick={handleDeleteConfirm} disabled={saving}>
                            Confirm
                          </button>
                          <button style={btnStyle()} onClick={() => setConfirmDelete(null)}>Cancel</button>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end' }}>
                          <button
                            style={btnStyle('primary')}
                            onClick={() => handleRenameStart(val)}
                          >
                            Rename
                          </button>
                          <span title={deleteTooltip}>
                            <button
                              style={btnStyle(canDelete ? 'danger' : 'disabled')}
                              disabled={!canDelete}
                              onClick={() => canDelete && setConfirmDelete({ value: val, totalCount: row.total_count, type: activeTab })}
                            >
                              Delete
                            </button>
                          </span>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <div style={{ marginTop: '0.75rem', textAlign: 'right' }}>
        <button style={{ ...btnStyle(), fontSize: '0.8rem' }} onClick={loadData} disabled={loading}>
          Refresh
        </button>
      </div>
    </div>
  );
}

export default DataCleanup;
