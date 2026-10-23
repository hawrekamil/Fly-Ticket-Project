import { useState, useEffect, useRef } from 'react';
import { Plane, MapPin, Loader2, X, Globe } from 'lucide-react';
import api from '../api';

const POPULAR_DEFAULTS = [
  { iata_code: 'COUNTRY:DE', name: 'All Major Airports (FRA, MUC, BER, DUS)', city_name: 'Germany (All Airports)', country: 'Germany', type: 'country' },
  { iata_code: 'COUNTRY:GB', name: 'All Major Airports (London LON, Manchester MAN)', city_name: 'United Kingdom / England (All Airports)', country: 'United Kingdom', type: 'country' },
  { iata_code: 'COUNTRY:TR', name: 'All Major Airports (Istanbul IST/SAW, Antalya AYT)', city_name: 'Turkey (All Airports)', country: 'Turkey', type: 'country' },
  { iata_code: 'LHR', name: 'Heathrow Airport', city_name: 'London', country: 'GB', type: 'airport' },
  { iata_code: 'FRA', name: 'Frankfurt Airport', city_name: 'Frankfurt', country: 'DE', type: 'airport' },
  { iata_code: 'BER', name: 'Berlin Brandenburg', city_name: 'Berlin', country: 'DE', type: 'airport' },
  { iata_code: 'IST', name: 'Istanbul Airport', city_name: 'Istanbul', country: 'TR', type: 'airport' },
  { iata_code: 'EBL', name: 'Erbil International Airport', city_name: 'Erbil', country: 'IQ', type: 'airport' },
  { iata_code: 'DXB', name: 'Dubai International', city_name: 'Dubai', country: 'AE', type: 'airport' },
  { iata_code: 'CDG', name: 'Charles de Gaulle Airport', city_name: 'Paris', country: 'FR', type: 'airport' },
  { iata_code: 'JFK', name: 'John F. Kennedy Airport', city_name: 'New York', country: 'US', type: 'airport' },
  { iata_code: 'AMS', name: 'Schiphol Airport', city_name: 'Amsterdam', country: 'NL', type: 'airport' },
];

export default function AirportAutocomplete({
  label,
  value,
  onChange,
  placeholder = 'Type country, city or airport...',
  required = false,
  inputClassName = '',
  icon: IconComponent = Plane,
  iconClassName = '',
  headerRight = null,
}) {
  const getInitialDisplay = () => {
    if (!value) return '';
    const match = POPULAR_DEFAULTS.find((a) => a.iata_code.toUpperCase() === value.toUpperCase());
    if (match) {
      return match.type === 'country' ? match.city_name : `${match.city_name} (${match.iata_code})`;
    }
    if (value.startsWith('COUNTRY:')) {
      const code = value.replace('COUNTRY:', '');
      return `${code} (All Airports)`;
    }
    return value;
  };

  const [query, setQuery] = useState(getInitialDisplay());
  const [suggestions, setSuggestions] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const wrapperRef = useRef(null);

  // Sync if value changes externally
  useEffect(() => {
    if (!value) {
      setQuery('');
    } else if (!query.includes(value)) {
      const match = POPULAR_DEFAULTS.find((a) => a.iata_code.toUpperCase() === value.toUpperCase());
      if (match) {
        setQuery(match.type === 'country' ? match.city_name : `${match.city_name} (${match.iata_code})`);
      } else {
        setQuery(value);
      }
    }
  }, [value]);

  // Click outside listener to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch suggestions with debounce
  useEffect(() => {
    if (!isOpen) return;

    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setSuggestions(POPULAR_DEFAULTS);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await api.get(`flights/airports/suggestions/?q=${encodeURIComponent(trimmed)}`);
        setSuggestions(res.data && res.data.length > 0 ? res.data : []);
      } catch (err) {
        console.warn('Failed to load airport suggestions', err);
        // Local fallback
        const local = POPULAR_DEFAULTS.filter(
          (a) =>
            a.city_name.toLowerCase().includes(trimmed.toLowerCase()) ||
            a.name.toLowerCase().includes(trimmed.toLowerCase()) ||
            a.iata_code.toLowerCase().includes(trimmed.toLowerCase()) ||
            (a.country && a.country.toLowerCase().includes(trimmed.toLowerCase()))
        );
        setSuggestions(local);
      } finally {
        setLoading(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [query, isOpen]);

  const handleSelect = (item) => {
    const isCountry = item.type === 'country' || item.iata_code.startsWith('COUNTRY:');
    const displayText = isCountry
      ? item.city_name || `${item.name} (All Airports)`
      : `${item.city_name || item.name} (${item.iata_code})`;
    setQuery(displayText);
    onChange(item.iata_code);
    setIsOpen(false);
  };

  const handleInputChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    setIsOpen(true);
    // Allow direct typing of countries, cities, or IATA codes
    onChange(val.trim());
  };

  const handleClear = () => {
    setQuery('');
    onChange('');
    setSuggestions(POPULAR_DEFAULTS);
    setIsOpen(true);
  };

  return (
    <div className="relative" ref={wrapperRef}>
      {(label || headerRight) && (
        <div className="flex items-center justify-between mb-1.5">
          {label && (
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-300">
              {label}
            </label>
          )}
          {headerRight}
        </div>
      )}

      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
          <IconComponent className={iconClassName || "h-4 w-4 text-indigo-400"} />
        </div>

        <input
          type="text"
          required={required}
          value={query}
          title={query}
          onChange={handleInputChange}
          onFocus={() => {
            setIsOpen(true);
            if (suggestions.length === 0) setSuggestions(POPULAR_DEFAULTS);
          }}
          placeholder={placeholder}
          className={
            inputClassName ||
            'w-full bg-black/40 backdrop-blur-xl border border-white/15 hover:border-white/25 focus:border-indigo-400 rounded-2xl pl-10 pr-9 py-3 text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 text-sm font-semibold transition-all'
          }
          autoComplete="off"
        />

        <div className="absolute inset-y-0 right-0 pr-3 flex items-center gap-1">
          {loading && <Loader2 className="h-4 w-4 text-indigo-400 animate-spin" />}
          {query && !loading && (
            <button
              type="button"
              onClick={handleClear}
              className="text-slate-400 hover:text-white p-1 rounded-full hover:bg-slate-700 transition-colors"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Floating Suggestions Dropdown */}
      {isOpen && (
        <div className="absolute z-50 mt-2 left-0 w-[380px] sm:w-[440px] max-w-[92vw] bg-slate-900/98 border border-slate-700 rounded-2xl shadow-2xl max-h-80 overflow-y-auto backdrop-blur-2xl divide-y divide-slate-800 animate-in fade-in slide-in-from-top-2 duration-150">
          {suggestions.length === 0 && !loading ? (
            <div className="p-4 text-center text-sm text-slate-400">
              No matching countries, cities or airports found. You can still search by country or airport name.
            </div>
          ) : (
            <>
              <div className="px-4 py-2.5 text-xs font-semibold text-slate-400 uppercase tracking-wider bg-slate-800/60 flex items-center justify-between">
                <span>{query.trim().length >= 2 ? 'Matching Destinations' : 'Popular Destinations'}</span>
                <span className="text-[11px] text-indigo-400 normal-case font-medium">Country, city or airport</span>
              </div>
              {suggestions.map((item, idx) => {
                const isCountry = item.type === 'country' || item.iata_code?.startsWith('COUNTRY:');

                return (
                  <button
                    key={`${item.iata_code}-${idx}`}
                    type="button"
                    onClick={() => handleSelect(item)}
                    className={`w-full text-left px-4 py-3 flex items-center justify-between gap-3.5 transition-colors group ${
                      isCountry
                        ? 'bg-indigo-950/25 hover:bg-indigo-900/40 hover:border-l-4 hover:border-emerald-400'
                        : 'hover:bg-indigo-600/20 hover:border-l-4 hover:border-indigo-500'
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <div
                        className={`p-2.5 rounded-xl shrink-0 transition-colors ${
                          isCountry
                            ? 'bg-emerald-950/80 text-emerald-400 group-hover:bg-emerald-600 group-hover:text-white'
                            : 'bg-slate-800 text-indigo-400 group-hover:bg-indigo-600 group-hover:text-white'
                        }`}
                      >
                        {isCountry ? (
                          <Globe className="h-4 w-4" />
                        ) : (
                          <MapPin className="h-4 w-4" />
                        )}
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-bold text-white group-hover:text-indigo-300">
                            {item.city_name || item.name}
                          </span>
                          {isCountry ? (
                            <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                              Country · All Airports
                            </span>
                          ) : item.country ? (
                            <span className="text-xs text-slate-400 font-medium">
                              ({item.country})
                            </span>
                          ) : null}
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5 group-hover:text-slate-200">
                          {item.name}
                        </p>
                      </div>
                    </div>

                    <span
                      className={`shrink-0 px-2.5 py-1 text-xs font-mono font-bold rounded-lg border transition-colors ${
                        isCountry
                          ? 'bg-emerald-950/70 text-emerald-300 border-emerald-700/50 group-hover:border-emerald-400'
                          : 'bg-slate-800 text-indigo-400 border-slate-700 group-hover:border-indigo-500 group-hover:bg-indigo-950/80'
                      }`}
                    >
                      {isCountry ? 'ALL' : item.iata_code}
                    </span>
                  </button>
                );
              })}
            </>
          )}
        </div>
      )}
    </div>
  );
}
