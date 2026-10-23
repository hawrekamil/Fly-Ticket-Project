import { useState, useEffect } from 'react';
import api from '../api';

const AgentDashboard = () => {
  const [holds, setHolds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHolds();
  }, []);

  const fetchHolds = async () => {
    try {
      const res = await api.get('flights/agent/holds/');
      setHolds(res.data);
    } catch (err) {
      console.error("Failed to fetch holds", err);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (orderId) => {
    if (!window.confirm('Are you sure you want to mark this cash hold as paid?')) return;
    try {
      await api.post(`flights/agent/holds/${orderId}/confirm/`);
      fetchHolds(); // refresh
    } catch (err) {
      alert('Failed to confirm payment: ' + (err.response?.data?.error || err.message));
    }
  };

  if (loading) return <div className="text-center py-12">Loading...</div>;

  return (
    <div className="max-w-6xl mx-auto py-8">
      <h1 className="text-3xl font-extrabold text-slate-900 mb-8">Agent Dashboard</h1>

      <div className="glass rounded-3xl overflow-hidden shadow-lg border border-slate-200">
        <div className="px-6 py-5 border-b border-slate-200 bg-white/50">
          <h3 className="text-lg leading-6 font-medium text-slate-900">Active Cash Holds</h3>
          <p className="mt-1 text-sm text-slate-500">Manage pending cash reservations across all customers.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50/50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Ref / Date</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Customer</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Amount</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Expires At</th>
                <th className="px-6 py-4 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white/40 divide-y divide-slate-200">
              {holds.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-sm text-slate-500">No active cash holds found.</td>
                </tr>
              ) : (
                holds.map((hold) => (
                  <tr key={hold.id} className="hover:bg-indigo-50/50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-bold text-slate-900">{hold.booking_reference}</div>
                      <div className="text-xs text-slate-500">{new Date(hold.created_at).toLocaleDateString()}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-slate-900">{hold.user_email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-semibold text-slate-900">{hold.total_amount} <span className="uppercase text-slate-500 font-normal">{hold.total_currency}</span></div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-red-600 font-medium">
                        {new Date(hold.hold_expires_at).toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button 
                        onClick={() => handleConfirm(hold.id)}
                        className="text-white bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg shadow-sm transition-colors"
                      >
                        Confirm Payment
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AgentDashboard;
