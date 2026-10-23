import { useState, useEffect } from 'react';
import api from '../api';
import { Ticket } from 'lucide-react';
import { Link } from 'react-router-dom';

const MyOrders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        const res = await api.get('flights/my-orders/');
        setOrders(res.data);
      } catch (err) {
        console.error("Failed to fetch orders", err);
      } finally {
        setLoading(false);
      }
    };
    fetchOrders();
  }, []);

  if (loading) return <div className="text-center py-12">Loading...</div>;

  return (
    <div className="max-w-5xl mx-auto py-8">
      <h1 className="text-3xl font-extrabold text-slate-900 mb-8">My Bookings</h1>

      {orders.length === 0 ? (
        <div className="glass p-12 text-center rounded-3xl">
          <Ticket className="mx-auto h-16 w-16 text-slate-400" />
          <h3 className="mt-4 text-xl font-medium text-slate-900">No trips yet</h3>
          <p className="mt-2 text-slate-500">Ready for your next adventure?</p>
          <div className="mt-6">
            <Link to="/" className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-xl shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 hover-lift">
              Search Flights
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {orders.map(order => (
            <div key={order.id} className="glass p-6 rounded-3xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
              <div className="flex-grow">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-xl font-bold text-slate-900">Ref: {order.booking_reference}</h3>
                  <span className={`px-3 py-1 text-xs font-semibold rounded-full ${
                    order.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                    order.status === 'hold_pending_cash' ? 'bg-blue-100 text-blue-800' :
                    order.status === 'expired' ? 'bg-slate-100 text-slate-800' :
                    'bg-amber-100 text-amber-800'
                  }`}>
                    {order.status.replace(/_/g, ' ').toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-slate-500">
                  Booked on {new Date(order.created_at).toLocaleDateString()}
                </p>
                {order.status === 'hold_pending_cash' && (
                  <div className="mt-3 p-3 bg-blue-50 border border-blue-100 rounded-lg inline-block">
                    <p className="text-sm text-blue-800 font-medium">
                      Expires: {new Date(order.hold_expires_at).toLocaleString()}
                    </p>
                  </div>
                )}
              </div>
              <div className="text-right bg-white/50 p-4 rounded-xl border border-slate-100 w-full md:w-auto">
                <p className="text-sm font-medium text-slate-500 uppercase">{order.total_currency}</p>
                <p className="text-2xl font-extrabold text-slate-900">{order.total_amount}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyOrders;
