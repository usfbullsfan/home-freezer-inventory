import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line,
} from 'recharts';
import { dashboardAPI } from '../services/api';
import './Dashboard.css';

const CATEGORY_COLORS = [
  '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
  '#1abc9c', '#e67e22', '#34495e', '#e91e63', '#00bcd4',
  '#8bc34a', '#ff5722', '#607d8b', '#795548', '#ffc107',
  '#673ab7', '#03a9f4', '#4caf50', '#ff9800', '#9c27b0',
];

function StatCard({ label, value, color, subtitle }) {
  return (
    <div className="stat-card" style={{ borderTopColor: color }}>
      <div className="stat-value" style={{ color }}>{value}</div>
      <div className="stat-label">{label}</div>
      {subtitle && <div className="stat-subtitle">{subtitle}</div>}
    </div>
  );
}

const RADIAN = Math.PI / 180;
function PieLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent }) {
  if (percent < 0.05) return null;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={12} fontWeight="bold">
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    dashboardAPI.getStats()
      .then(res => setStats(res.data))
      .catch(err => setError(err.response?.data?.message || 'Failed to load dashboard data'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="dashboard-loading">Loading dashboard...</div>;
  if (error) return <div className="dashboard-error">{error}</div>;

  const { summary, items_by_category, oldest_items, expiration_timeline, consumption_patterns, added_per_month } = stats;

  // Merge added_per_month and consumption_patterns by month for the activity chart
  const activityData = added_per_month.map((entry, i) => ({
    month: entry.month,
    added: entry.count,
    consumed: consumption_patterns[i]?.consumed ?? 0,
    thrown_out: consumption_patterns[i]?.thrown_out ?? 0,
  }));

  return (
    <div className="dashboard">
      <h2 className="dashboard-title">Inventory Dashboard</h2>

      {/* Summary cards */}
      <section className="dashboard-section">
        <div className="stat-cards">
          <StatCard label="In Freezer" value={summary.total_in_freezer} color="#3498db" />
          <StatCard label="Expiring Soon" value={summary.expiring_soon} color="#f39c12" subtitle="within 30 days" />
          <StatCard label="Expired" value={summary.expired} color="#e74c3c" subtitle="still in freezer" />
          <StatCard label="Consumed" value={summary.total_consumed} color="#2ecc71" />
          <StatCard label="Thrown Out" value={summary.total_thrown_out} color="#95a5a6" />
        </div>
      </section>

      {/* Items by Category */}
      <section className="dashboard-section">
        <h3 className="section-title">Items by Category</h3>
        <div className="chart-row">
          <div className="chart-container chart-pie">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={items_by_category}
                  dataKey="count"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={110}
                  labelLine={false}
                  label={<PieLabel />}
                >
                  {items_by_category.map((_, index) => (
                    <Cell key={index} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value, name) => [value, name]} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container chart-bar-category">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={items_by_category} layout="vertical" margin={{ left: 20, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" allowDecimals={false} />
                <YAxis type="category" dataKey="category" width={120} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" name="Items" radius={[0, 4, 4, 0]}>
                  {items_by_category.map((_, index) => (
                    <Cell key={index} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      {/* Expiration Timeline */}
      <section className="dashboard-section">
        <h3 className="section-title">Expiration Timeline (Next 12 Months)</h3>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={expiration_timeline} margin={{ left: 10, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" name="Expiring Items" fill="#e74c3c" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Activity Over Time */}
      <section className="dashboard-section">
        <h3 className="section-title">Activity Over the Past 12 Months</h3>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={activityData} margin={{ left: 10, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="added" name="Added" stroke="#3498db" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="consumed" name="Consumed" stroke="#2ecc71" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="thrown_out" name="Thrown Out" stroke="#e74c3c" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Oldest Items */}
      <section className="dashboard-section">
        <h3 className="section-title">Oldest Items in Freezer</h3>
        {oldest_items.length === 0 ? (
          <p className="empty-state">No items currently in the freezer.</p>
        ) : (
          <div className="oldest-items-table-wrap">
            <table className="oldest-items-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Item</th>
                  <th>Category</th>
                  <th>Date Added</th>
                  <th>Days in Freezer</th>
                </tr>
              </thead>
              <tbody>
                {oldest_items.map((item, i) => {
                  const ageClass = item.days_in_freezer > 365 ? 'age-old' : item.days_in_freezer > 180 ? 'age-warn' : '';
                  return (
                    <tr key={item.id} className={ageClass}>
                      <td>{i + 1}</td>
                      <td>{item.name}</td>
                      <td>{item.category}</td>
                      <td>{new Date(item.added_date).toLocaleDateString()}</td>
                      <td>
                        <span className={`days-badge ${ageClass}`}>{item.days_in_freezer}d</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
