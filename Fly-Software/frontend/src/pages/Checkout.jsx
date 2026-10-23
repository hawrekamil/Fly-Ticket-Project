import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';
import api from '../api';
import { useAuth } from '../context/AuthContext';

// Load Stripe outside of component
const stripePromise = loadStripe('pk_test_TYooMQauvdEDq54NiTphI7jx'); // Demo key

const CheckoutForm = ({ clientSecret, onSuccess }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!stripe || !elements) return;

    setLoading(true);
    const { error: submitError } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: `${window.location.origin}/my-orders`,
      },
      redirect: "if_required"
    });

    if (submitError) {
      setError(submitError.message);
      setLoading(false);
    } else {
      onSuccess();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mt-6 border border-slate-200 p-4 rounded-xl">
      <PaymentElement />
      {error && <div className="text-red-500 mt-4 text-sm font-medium">{error}</div>}
      <button disabled={!stripe || loading} className="mt-6 w-full bg-indigo-600 text-white py-3 rounded-xl font-bold hover:bg-indigo-700 disabled:opacity-50 transition-colors">
        {loading ? 'Processing...' : 'Pay Now'}
      </button>
    </form>
  );
};

const Checkout = () => {
  const { offerId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [offer, setOffer] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('stripe');
  const [clientSecret, setClientSecret] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [passenger, setPassenger] = useState({
    given_name: user?.first_name || '',
    family_name: user?.last_name || '',
    born_on: '1990-01-01',
    gender: 'm',
    title: 'mr',
    email: user?.email || '',
    phone_number: '+1234567890'
  });

  useEffect(() => {
    // In a real app we'd fetch the offer details by ID. For now we assume user filled it out.
    // The previous implementation didn't have an endpoint just for fetching the offer snapshot, 
    // it was passed via Django templates. Since it's a SPA, we need to pass data or fetch.
    // Let's assume we can proceed with booking directly.
  }, [offerId]);

  const handleChange = (e) => setPassenger({ ...passenger, [e.target.name]: e.target.value });

  const handleCashCheckout = async () => {
    setLoading(true);
    try {
      await api.post('flights/book/', {
        offer_id: offerId,
        payment_method: 'cash',
        passengers: [{ ...passenger, passenger_type: 'adult' }]
      });
      navigate('/my-orders');
    } catch (err) {
      setError(err.response?.data?.error || 'Booking failed.');
    } finally {
      setLoading(false);
    }
  };

  const initStripePayment = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.post('flights/book/', {
        offer_id: offerId,
        payment_method: 'stripe',
        passengers: [{ ...passenger, passenger_type: 'adult' }]
      });
      setClientSecret(res.data.stripe_client_secret);
    } catch (err) {
      setError(err.response?.data?.error || 'Payment initialization failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="glass p-8 rounded-3xl">
        <h2 className="text-2xl font-bold text-slate-900 mb-6">Complete your booking</h2>
        
        {error && <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg">{error}</div>}

        {!clientSecret ? (
          <div className="space-y-6">
            <h3 className="text-lg font-bold text-slate-800">Passenger Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <input type="text" name="given_name" placeholder="Given Name" value={passenger.given_name} onChange={handleChange} className="p-3 border rounded-lg" />
              <input type="text" name="family_name" placeholder="Family Name" value={passenger.family_name} onChange={handleChange} className="p-3 border rounded-lg" />
              <input type="date" name="born_on" value={passenger.born_on} onChange={handleChange} className="p-3 border rounded-lg" />
              <input type="email" name="email" placeholder="Email" value={passenger.email} onChange={handleChange} className="p-3 border rounded-lg" />
              <input type="tel" name="phone_number" placeholder="Phone" value={passenger.phone_number} onChange={handleChange} className="p-3 border rounded-lg" />
            </div>

            <h3 className="text-lg font-bold text-slate-800 mt-6">Payment Method</h3>
            <div className="flex gap-4">
              <label className={`flex-1 border p-4 rounded-xl cursor-pointer ${paymentMethod === 'stripe' ? 'border-indigo-600 bg-indigo-50' : ''}`}>
                <input type="radio" name="payment_method" value="stripe" checked={paymentMethod === 'stripe'} onChange={(e) => setPaymentMethod(e.target.value)} className="sr-only" />
                <span className="font-bold block">Credit Card</span>
                <span className="text-sm text-gray-500">Instant confirmation via Stripe</span>
              </label>
              <label className={`flex-1 border p-4 rounded-xl cursor-pointer ${paymentMethod === 'cash' ? 'border-indigo-600 bg-indigo-50' : ''}`}>
                <input type="radio" name="payment_method" value="cash" checked={paymentMethod === 'cash'} onChange={(e) => setPaymentMethod(e.target.value)} className="sr-only" />
                <span className="font-bold block">Cash Hold</span>
                <span className="text-sm text-gray-500">Pay at desk within 24h</span>
              </label>
            </div>

            <button 
              onClick={paymentMethod === 'cash' ? handleCashCheckout : initStripePayment}
              disabled={loading}
              className="w-full bg-slate-900 text-white font-bold py-4 rounded-xl hover:bg-indigo-600 transition-colors disabled:opacity-50 mt-6"
            >
              {loading ? 'Processing...' : (paymentMethod === 'cash' ? 'Confirm Cash Booking' : 'Proceed to Payment')}
            </button>
          </div>
        ) : (
          <div>
            <h3 className="text-xl font-bold text-slate-800 mb-4">Payment Details</h3>
            <Elements stripe={stripePromise} options={{ clientSecret, appearance: { theme: 'stripe' } }}>
              <CheckoutForm clientSecret={clientSecret} onSuccess={() => navigate('/my-orders')} />
            </Elements>
          </div>
        )}
      </div>
    </div>
  );
};

export default Checkout;
