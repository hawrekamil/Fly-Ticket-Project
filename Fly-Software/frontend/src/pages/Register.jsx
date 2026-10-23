import { useState } from 'react';
import api from '../api';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';

const Register = () => {
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    username: '', email: '', password: '', password_confirm: ''
  });
  const [errors, setErrors] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrors(null);
    try {
      await api.post('accounts/register/', formData);
      await login(formData.username, formData.password);
    } catch (err) {
      if (err.response && err.response.data) {
        setErrors(err.response.data);
      } else {
        setErrors({ non_field_errors: ['An unexpected error occurred.'] });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  return (
    <div className="flex items-center justify-center min-h-[70vh]">
      <div className="glass w-full max-w-md p-8 rounded-3xl relative overflow-hidden">
        <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-pink-500 rounded-full mix-blend-multiply filter blur-2xl opacity-20"></div>
        
        <div className="relative z-10 text-center mb-8">
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">Create an account</h2>
          <p className="mt-2 text-sm text-slate-500">Join BookingSoft for seamless travel.</p>
        </div>

        {errors && (
          <div className="mb-4 bg-red-50 text-red-700 p-3 rounded-lg text-sm font-medium border border-red-200">
            <ul className="list-disc pl-4">
              {Object.entries(errors).map(([key, val]) => (
                <li key={key}><span className="capitalize">{key}</span>: {Array.isArray(val) ? val[0] : val}</li>
              ))}
            </ul>
          </div>
        )}

        <form onSubmit={handleSubmit} className="relative z-10 space-y-5">
          {['username', 'email', 'password', 'password_confirm'].map(field => (
            <div key={field}>
              <label className="block text-sm font-medium text-slate-700 capitalize">{field.replace('_', ' ')}</label>
              <input 
                type={field.includes('password') ? 'password' : field === 'email' ? 'email' : 'text'} 
                name={field}
                required 
                value={formData[field]}
                onChange={handleChange}
                className="mt-1 block w-full px-4 py-3 border border-slate-300 rounded-xl shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 bg-white/70 backdrop-blur-sm transition-all"
              />
            </div>
          ))}
          <button 
            type="submit" 
            disabled={loading}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-md text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 hover-lift disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Sign up'}
          </button>
        </form>
        
        <div className="mt-6 text-center relative z-10">
          <p className="text-sm text-slate-600">
            Already have an account? <Link to="/login" className="font-medium text-indigo-600 hover:text-indigo-500">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
