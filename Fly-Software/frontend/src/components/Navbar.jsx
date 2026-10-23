import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Plane, LogOut, LayoutDashboard, Luggage, ChevronDown, Check, User, Globe } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

const CURRENCIES = [
  { code: 'EUR', symbol: '€', region: 'EU', label: 'EUR (€)' },
  { code: 'USD', symbol: '$', region: 'US', label: 'USD ($)' },
  { code: 'GBP', symbol: '£', region: 'GB', label: 'GBP (£)' },
  { code: 'IQD', symbol: 'د.ع', region: 'IQ', label: 'IQD (د.ع)' },
  { code: 'AED', symbol: 'د.إ', region: 'AE', label: 'AED (د.إ)' },
  { code: 'TRY', symbol: '₺', region: 'TR', label: 'TRY (₺)' },
];

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [currencyOpen, setCurrencyOpen] = useState(false);
  const [selectedCurrency, setSelectedCurrency] = useState(CURRENCIES[0]);
  
  const currencyRef = useRef(null);
  const userMenuRef = useRef(null);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (currencyRef.current && !currencyRef.current.contains(event.target)) {
        setCurrencyOpen(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <nav className="relative z-50 bg-[#070b14]/95 backdrop-blur-2xl border-b border-white/10 sticky top-0 text-white shadow-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-20 items-center gap-4">
          
          {/* Left Section */}
          <div className="flex items-center gap-6 sm:gap-10">
            {/* Logo Section */}
            <Link to="/" className="flex items-center gap-3 group shrink-0">
              <div className="w-11 h-11 rounded-2xl bg-[#0b1329] border border-cyan-400/50 shadow-sm shadow-cyan-500/30 flex items-center justify-center transition-transform group-hover:scale-105">
                <Plane className="h-5 w-5 text-cyan-300 stroke-[1.8]" />
              </div>
              <div>
                <div className="flex items-center gap-1.5 font-extrabold text-lg sm:text-xl tracking-tight text-white">
                  <span>BookingSoft</span>
                  <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block shadow-sm shadow-cyan-400"></span>
                </div>
                <span className="text-[8.5px] font-bold tracking-[0.24em] text-slate-400 uppercase block -mt-0.5">
                  AERO INTELLIGENCE
                </span>
              </div>
            </Link>

            {/* Airlines Page Link */}
            <Link 
              to="/airlines" 
              className="hidden sm:flex items-center gap-2 text-sm font-bold text-slate-300 hover:text-cyan-400 transition-colors px-3 py-2 rounded-xl hover:bg-slate-800/50 border border-transparent hover:border-slate-700/50"
            >
              <Globe className="h-4 w-4" />
              <span>All Airlines</span>
            </Link>
          </div>
          {/* Right Action Items */}
          <div className="flex items-center gap-3 sm:gap-4 shrink-0">
            {/* Currency Selector */}
            <div className="relative" ref={currencyRef}>
              <button
                type="button"
                onClick={() => setCurrencyOpen(!currencyOpen)}
                className="bg-slate-900/90 hover:bg-slate-800 border border-slate-700/70 rounded-xl px-3 py-2 text-xs sm:text-sm font-medium text-slate-200 flex items-center gap-2 cursor-pointer transition-colors shadow-sm"
              >
                <span className="text-[10px] font-bold text-slate-400 tracking-wider">
                  {selectedCurrency.region}
                </span>
                <span className="font-semibold text-white">
                  {selectedCurrency.label}
                </span>
                <ChevronDown className={`h-3.5 w-3.5 text-slate-400 transition-transform ${currencyOpen ? 'rotate-180' : ''}`} />
              </button>

              {currencyOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-slate-900/98 border border-slate-700/80 rounded-2xl shadow-2xl py-1.5 z-50 backdrop-blur-2xl divide-y divide-slate-800">
                  <div className="px-3.5 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Select Currency
                  </div>
                  <div className="py-1">
                    {CURRENCIES.map((curr) => (
                      <button
                        key={curr.code}
                        type="button"
                        onClick={() => {
                          setSelectedCurrency(curr);
                          setCurrencyOpen(false);
                        }}
                        className={`w-full text-left px-3.5 py-2 text-xs font-semibold flex items-center justify-between hover:bg-slate-800/80 transition-colors ${
                          selectedCurrency.code === curr.code
                            ? 'text-cyan-300 bg-cyan-950/30'
                            : 'text-slate-300'
                        }`}
                      >
                        <span className="flex items-center gap-2">
                          <span className="w-5 text-[10px] font-bold text-slate-400">{curr.region}</span>
                          <span>{curr.label}</span>
                        </span>
                        {selectedCurrency.code === curr.code && (
                          <Check className="h-3.5 w-3.5 text-cyan-400" />
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* My Trips */}
            <Link
              to="/my-orders"
              className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-slate-300 hover:text-white transition-colors px-2.5 py-2 rounded-xl hover:bg-slate-800/60"
            >
              <Luggage className="h-4 w-4 text-slate-400" />
              <span>My Trips</span>
            </Link>

            {/* Auth Section */}
            {user ? (
              <div className="flex items-center gap-3">
                {(user.is_agent || user.is_admin_role) && (
                  <Link
                    to="/agent-dashboard"
                    className="hidden lg:flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-indigo-300 hover:text-white transition-colors px-2.5 py-2 rounded-xl hover:bg-slate-800/60"
                  >
                    <LayoutDashboard className="h-4 w-4" />
                    <span>Agent Dashboard</span>
                  </Link>
                )}

                <div className="relative" ref={userMenuRef}>
                  <button
                    type="button"
                    onClick={() => setMenuOpen(!menuOpen)}
                    className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-white bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/70 px-3 py-2 rounded-xl transition-colors focus:outline-none"
                  >
                    <User className="h-4 w-4 text-cyan-400" />
                    <span className="max-w-[100px] truncate">{user.username}</span>
                    <ChevronDown className={`h-3.5 w-3.5 text-slate-400 transition-transform ${menuOpen ? 'rotate-180' : ''}`} />
                  </button>

                  {menuOpen && (
                    <div className="absolute right-0 mt-2 w-48 bg-slate-900/98 border border-slate-700/80 rounded-2xl shadow-2xl py-1.5 z-50 backdrop-blur-2xl">
                      <div className="px-4 py-2 border-b border-slate-800">
                        <p className="text-xs text-slate-400">Signed in as</p>
                        <p className="text-sm font-bold text-white truncate">{user.username}</p>
                      </div>
                      <Link
                        to="/my-orders"
                        onClick={() => setMenuOpen(false)}
                        className="px-4 py-2.5 text-xs sm:text-sm text-slate-300 hover:text-white hover:bg-slate-800/80 flex items-center gap-2 transition-colors"
                      >
                        <Luggage className="h-4 w-4 text-cyan-400" />
                        <span>My Trips & Bookings</span>
                      </Link>
                      {(user.is_agent || user.is_admin_role) && (
                        <Link
                          to="/agent-dashboard"
                          onClick={() => setMenuOpen(false)}
                          className="px-4 py-2.5 text-xs sm:text-sm text-slate-300 hover:text-white hover:bg-slate-800/80 flex items-center gap-2 transition-colors lg:hidden"
                        >
                          <LayoutDashboard className="h-4 w-4 text-indigo-400" />
                          <span>Agent Dashboard</span>
                        </Link>
                      )}
                      <button
                        type="button"
                        onClick={handleLogout}
                        className="w-full text-left px-4 py-2.5 text-xs sm:text-sm text-red-400 hover:text-red-300 hover:bg-slate-800/80 flex items-center gap-2 transition-colors border-t border-slate-800"
                      >
                        <LogOut className="h-4 w-4" />
                        <span>Sign out</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2.5 sm:gap-3">
                <Link
                  to="/login"
                  className="text-xs sm:text-sm font-semibold text-slate-300 hover:text-white transition-colors px-2 py-1.5"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="bg-gradient-to-r from-[#6366f1] via-[#7c3aed] to-[#a855f7] hover:from-[#4f46e5] hover:to-[#9333ea] text-white font-bold text-xs sm:text-sm px-4 py-2 rounded-xl shadow-lg shadow-purple-900/30 transition-all hover:scale-[1.02] active:scale-[0.98]"
                >
                  Sign Up Free
                </Link>
              </div>
            )}
          </div>

        </div>
      </div>
    </nav>
  );
};

export default Navbar;
