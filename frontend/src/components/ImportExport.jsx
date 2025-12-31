import { useState } from 'react';
import { itemsAPI } from '../services/api';

function ImportExport() {
  const [exportStatus, setExportStatus] = useState('in_freezer');
  const [importFormat, setImportFormat] = useState('csv');
  const [importFile, setImportFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [importResult, setImportResult] = useState(null);

  const handleExportCSV = async () => {
    try {
      setError('');
      await itemsAPI.exportCSV(exportStatus);
      setSuccess('CSV file downloaded successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to export CSV: ' + err.message);
    }
  };

  const handleExportJSON = async () => {
    try {
      setError('');
      await itemsAPI.exportJSON(exportStatus);
      setSuccess('JSON file downloaded successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to export JSON: ' + err.message);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImportFile(file);
      setError('');
      setImportResult(null);
    }
  };

  const handleImport = async () => {
    if (!importFile) {
      setError('Please select a file to import');
      return;
    }

    // Validate file extension
    const fileExt = importFile.name.split('.').pop().toLowerCase();
    if (importFormat === 'csv' && fileExt !== 'csv') {
      setError('Please select a CSV file');
      return;
    }
    if (importFormat === 'json' && fileExt !== 'json') {
      setError('Please select a JSON file');
      return;
    }

    try {
      setImporting(true);
      setError('');
      setSuccess('');
      setImportResult(null);

      const response = importFormat === 'csv'
        ? await itemsAPI.importCSV(importFile)
        : await itemsAPI.importJSON(importFile);

      const result = response.data;
      setImportResult(result);

      if (result.imported > 0) {
        setSuccess(
          `Successfully imported ${result.imported} item(s). ` +
          (result.skipped > 0 ? `Skipped ${result.skipped} item(s).` : '')
        );
        setImportFile(null);
        document.getElementById('import-file').value = '';
      } else {
        setError('No items were imported. ' + (result.skipped > 0 ? `Skipped ${result.skipped} item(s).` : ''));
      }
    } catch (err) {
      setError('Failed to import file: ' + (err.response?.data?.error || err.message));
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="import-export-section">
      <h2>Import / Export</h2>
      <p style={{ color: '#666', marginBottom: '1.5rem' }}>
        Export your inventory to CSV or JSON for backup and spreadsheet management.
        Import data from previously exported files or migrate from other systems.
      </p>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3>📥 Export Data</h3>
        <p style={{ color: '#666', marginBottom: '1rem', fontSize: '0.9rem' }}>
          Download your inventory data in CSV or JSON format
        </p>

        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="export-status" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
            Items to Export:
          </label>
          <select
            id="export-status"
            value={exportStatus}
            onChange={(e) => setExportStatus(e.target.value)}
            style={{ maxWidth: '300px' }}
          >
            <option value="in_freezer">Items in Freezer Only</option>
            <option value="consumed">Consumed Items Only</option>
            <option value="thrown_out">Thrown Out Items Only</option>
            <option value="all">All Items (including history)</option>
          </select>
        </div>

        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <button
            onClick={handleExportCSV}
            className="btn btn-primary"
          >
            📊 Export as CSV
          </button>

          <button
            onClick={handleExportJSON}
            className="btn btn-primary"
          >
            📄 Export as JSON
          </button>
        </div>
      </div>

      <div className="card">
        <h3>📤 Import Data</h3>
        <p style={{ color: '#666', marginBottom: '1rem', fontSize: '0.9rem' }}>
          Import items from a CSV or JSON file
        </p>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
            File Format:
          </label>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="radio"
                name="import-format"
                value="csv"
                checked={importFormat === 'csv'}
                onChange={(e) => setImportFormat(e.target.value)}
              />
              <span>CSV</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="radio"
                name="import-format"
                value="json"
                checked={importFormat === 'json'}
                onChange={(e) => setImportFormat(e.target.value)}
              />
              <span>JSON</span>
            </label>
          </div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="import-file" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
            Select File:
          </label>
          <input
            type="file"
            id="import-file"
            accept={importFormat === 'csv' ? '.csv' : '.json'}
            onChange={handleFileSelect}
            disabled={importing}
          />
          {importFile && (
            <div style={{ marginTop: '0.5rem', color: '#666', fontSize: '0.9rem' }}>
              Selected: {importFile.name}
            </div>
          )}
        </div>

        <button
          onClick={handleImport}
          className="btn btn-primary"
          disabled={!importFile || importing}
        >
          {importing ? 'Importing...' : '📤 Import Items'}
        </button>

        {importResult && (
          <div style={{ marginTop: '1rem', padding: '1rem', background: '#f8f9fa', borderRadius: '4px' }}>
            <h4 style={{ marginBottom: '0.5rem' }}>Import Results:</h4>
            <ul style={{ marginLeft: '1.5rem', lineHeight: '1.6' }}>
              <li>✓ Imported: {importResult.imported} item(s)</li>
              {importResult.skipped > 0 && <li>⊘ Skipped: {importResult.skipped} item(s)</li>}
            </ul>
            {importResult.errors && importResult.errors.length > 0 && (
              <div style={{ marginTop: '0.5rem' }}>
                <strong>Errors:</strong>
                <ul style={{ marginLeft: '1.5rem', marginTop: '0.25rem', fontSize: '0.85rem', color: '#d32f2f' }}>
                  {importResult.errors.map((err, idx) => (
                    <li key={idx}>{err}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="card" style={{ marginTop: '1.5rem', background: '#e3f2fd' }}>
        <h3 style={{ marginBottom: '0.5rem' }}>📝 CSV Format</h3>
        <p style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>
          CSV files should include these columns:
        </p>
        <code style={{ display: 'block', background: 'white', padding: '0.5rem', borderRadius: '4px', fontSize: '0.85rem', overflow: 'auto' }}>
          QR Code, UPC, Name, Category, Source, Weight, Weight Unit, Added Date, Expiration Date, Status, Removed Date, Notes
        </code>
        <p style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#666' }}>
          • Categories will be created automatically if they don't exist<br />
          • Items with duplicate QR codes will be skipped<br />
          • Dates should be in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        </p>
      </div>

      <div className="card" style={{ marginTop: '1rem', background: '#e8f5e9' }}>
        <h3 style={{ marginBottom: '0.5rem' }}>📝 JSON Format</h3>
        <p style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>
          JSON files should follow this structure:
        </p>
        <pre style={{ background: 'white', padding: '0.5rem', borderRadius: '4px', fontSize: '0.75rem', overflow: 'auto' }}>
{`{
  "items": [
    {
      "qr_code": "ABC123",
      "name": "Item name",
      "category": "Category name",
      "weight": 1.5,
      "weight_unit": "lb",
      ...
    }
  ]
}`}
        </pre>
      </div>
    </div>
  );
}

export default ImportExport;
