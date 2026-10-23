import { useState, useMemo, useEffect, useRef } from 'react';
import api from '../api';
import {
  Search,
  Loader2,
  Plane,
  PlaneTakeoff,
  PlaneLanding,
  ChevronDown,
  ChevronUp,
  Clock,
  Luggage,
  MapPin,
  AlertCircle,
  Building2,
  SlidersHorizontal,
  Sunrise,
  Sun,
  Sunset,
  Moon,
  RotateCcw,
  Check,
  Globe,
  Wifi,
  Zap,
  Utensils,
  Tv,
  Briefcase,
  ShieldCheck,
  Leaf,
  Sparkles,
  Info,
  Printer,
  Download,
  ArrowLeftRight,
  Calendar,
  Minus,
  Plus,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import AirportAutocomplete from '../components/AirportAutocomplete';

const getDefaultDepartureDate = () => {
  const d = new Date();
  d.setDate(d.getDate() + 14);
  return d.toISOString().split('T')[0];
};

const getTodayDate = () => {
  return new Date().toISOString().split('T')[0];
};

/**
 * Robust timezone-neutral formatter that preserves the exact local airport time.
 * e.g. "2026-09-19T13:56:00" -> "13:56"
 */
export const formatFlightTime = (isoString) => {
  if (!isoString) return '--:--';
  if (isoString.includes('T')) {
    const timePart = isoString.split('T')[1];
    return timePart.substring(0, 5);
  }
  return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

export const formatFlightDate = (isoString) => {
  if (!isoString) return '';
  const datePart = isoString.split('T')[0];
  const parts = datePart.split('-');
  if (parts.length === 3) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const month = months[parseInt(parts[1], 10) - 1] || parts[1];
    return `${month} ${parseInt(parts[2], 10)}`;
  }
  return new Date(isoString).toLocaleDateString([], { month: 'short', day: 'numeric' });
};

export const formatFlightDateWithDay = (isoString) => {
  if (!isoString) return '';
  try {
    const datePart = isoString.split('T')[0];
    const parts = datePart.split('-');
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1;
      const day = parseInt(parts[2], 10);
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const localDate = new Date(year, month, day);
      return `${months[month]} ${day}, ${days[localDate.getDay()]}`;
    }
  } catch (e) {
    // fallback
  }
  return formatFlightDate(isoString);
};

export const isDifferentDay = (depIso, arrIso) => {
  if (!depIso || !arrIso) return false;
  const depDate = depIso.split('T')[0];
  const arrDate = arrIso.split('T')[0];
  return depDate !== arrDate;
};

export const formatDurationString = (dur) => {
  if (!dur) return '';
  if (typeof dur === 'string' && dur.startsWith('PT')) {
    const hoursMatch = dur.match(/(\d+)H/);
    const minsMatch = dur.match(/(\d+)M/);
    const h = hoursMatch ? `${hoursMatch[1]}h` : '';
    const m = minsMatch ? `${minsMatch[1]}m` : '';
    const formatted = [h, m].filter(Boolean).join(' ');
    return formatted || dur;
  }
  return dur;
};

const getTimeOfDay = (isoString) => {
  if (!isoString || !isoString.includes('T')) return 'other';
  const hour = parseInt(isoString.split('T')[1].substring(0, 2), 10);
  if (hour >= 6 && hour < 12) return 'morning';
  if (hour >= 12 && hour < 18) return 'afternoon';
  if (hour >= 18 && hour <= 23) return 'evening';
  return 'night'; // 00:00 - 05:59
};

const formatErrorMessage = (err) => {
  if (!err) return '';
  if (typeof err === 'string') {
    if (err.includes('<html') || err.includes('<!DOCTYPE') || err.includes('Internal Server Error')) {
      return 'No flights available for the selected route or date. Please try another destination or date.';
    }
    return err;
  }
  if (err.error) {
    if (typeof err.error === 'string' && (err.error.includes('<html') || err.error.includes('<!DOCTYPE'))) {
      return 'No flights available for the selected route or date. Please try another destination or date.';
    }
    return err.error;
  }
  if (err.detail) return err.detail;
  return (
    Object.entries(err)
      .map(([k, v]) => `${k.replace('_', ' ')}: ${Array.isArray(v) ? v.join(', ') : v}`)
      .join(' | ') || 'No flights found for this search. Please try alternative airports or dates.'
  );
};

const Home = () => {
  const [formData, setFormData] = useState({
    origin: 'COUNTRY:DE',
    destination: 'LON',
    departure_date: getDefaultDepartureDate(),
    return_date: '',
    adult_count: 1,
    child_count: 0,
    cabin_class: 'economy',
  });
  const [loading, setLoading] = useState(false);
  const [offers, setOffers] = useState(null);
  const [error, setError] = useState(null);
  const [expandedOfferId, setExpandedOfferId] = useState(null);
  const [searchMetadata, setSearchMetadata] = useState(null);
  const resultsRef = useRef(null);

  // Filter States
  const [selectedMaxPrice, setSelectedMaxPrice] = useState(null);
  const [selectedAirlines, setSelectedAirlines] = useState([]);
  const [airlineSortType, setAirlineSortType] = useState('count');
  const [selectedTimeOfDay, setSelectedTimeOfDay] = useState('all');
  const [selectedStops, setSelectedStops] = useState('all');
  const [selectedOriginAirport, setSelectedOriginAirport] = useState('all');
  const [sortBy, setSortBy] = useState('cheapest');
  const [showFilters, setShowFilters] = useState(true);
  const [tripType, setTripType] = useState('one_way');
  const [includeRail, setIncludeRail] = useState(false);

  const handleSwap = () => {
    setFormData((prev) => ({
      ...prev,
      origin: prev.destination,
      destination: prev.origin,
    }));
  };

  const updateAdults = (delta) => {
    setFormData((prev) => ({
      ...prev,
      adult_count: Math.max(1, Math.min(9, prev.adult_count + delta)),
    }));
  };

  const updateChildren = (delta) => {
    setFormData((prev) => ({
      ...prev,
      child_count: Math.max(0, Math.min(9, prev.child_count + delta)),
    }));
  };

  const handleAdd7DaysReturn = () => {
    setTripType('round_trip');
    const baseDate = formData.departure_date ? new Date(formData.departure_date) : new Date();
    baseDate.setDate(baseDate.getDate() + 7);
    const returnDateStr = baseDate.toISOString().split('T')[0];
    setFormData((prev) => ({ ...prev, return_date: returnDateStr }));
  };

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const toggleExpand = (id) => {
    setExpandedOfferId((prev) => (prev === id ? null : id));
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setOffers(null);
    setExpandedOfferId(null);
    // Smoothly scroll down to loading indicator
    setTimeout(() => {
      resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 60);

    try {
      const payload = {
        ...formData,
        origin: formData.origin.trim(),
        destination: formData.destination.trim(),
      };
      if (!payload.return_date) delete payload.return_date;
      const res = await api.post('flights/search/', payload);
      setOffers(res.data.offers);
      setSearchMetadata({
        originLabel: res.data.origin_label,
        destinationLabel: res.data.destination_label,
        isCountrySearch: res.data.is_country_search,
        totalOffers: res.data.total_offers,
      });
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 120);
    } catch (err) {
      setError(err.response?.data || { error: 'Failed to search flights. Please try another route or date.' });
    } finally {
      setLoading(false);
    }
  };

  // Compute stats across all offers
  const { minPrice, maxPrice, airlinesList, currency, originAirports } = useMemo(() => {
    if (!offers || offers.length === 0) {
      return { minPrice: 0, maxPrice: 1000, airlinesList: [], currency: 'EUR', originAirports: [] };
    }
    const prices = offers.map((o) => parseFloat(o.total_amount));
    const minP = Math.floor(Math.min(...prices));
    const maxP = Math.ceil(Math.max(...prices));

    const airlineMap = {};
    const originMap = new Map();

    offers.forEach((o) => {
      const name = o.airline_name || 'Other';
      airlineMap[name] = (airlineMap[name] || 0) + 1;

      // Extract departure airport
      const firstSlice = o.raw_offer?.slices?.[0];
      const seg0 = firstSlice?.segments?.[0];
      const originObj = seg0?.origin || firstSlice?.origin;
      const code = originObj?.iata_code;
      const originName = originObj?.city_name || originObj?.name || code;
      if (code) {
        if (!originMap.has(code)) {
          originMap.set(code, { code, name: originName, count: 0 });
        }
        originMap.get(code).count += 1;
      }
    });

    const aList = Object.entries(airlineMap)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => {
        if (airlineSortType === 'alpha') {
          return a.name.localeCompare(b.name);
        }
        return b.count - a.count;
      });

    const origins = Array.from(originMap.values()).sort((a, b) => b.count - a.count);

    return {
      minPrice: minP,
      maxPrice: maxP,
      airlinesList: aList,
      originAirports: origins,
      currency: offers[0].total_currency || 'EUR',
    };
  }, [offers, airlineSortType]);

  // Sync initial max price when new offers load
  useEffect(() => {
    if (offers && offers.length > 0) {
      const prices = offers.map((o) => parseFloat(o.total_amount));
      const maxP = Math.ceil(Math.max(...prices));
      setSelectedMaxPrice(maxP);
      setSelectedAirlines([]);
      setSelectedTimeOfDay('all');
      setSelectedStops('all');
      setSelectedOriginAirport('all');
    }
  }, [offers]);

  // Filter & Sort Offers
  const filteredOffers = useMemo(() => {
    if (!offers) return [];
    return offers
      .filter((offer) => {
        // Departure Airport Filter (when country search returns multiple hubs)
        if (selectedOriginAirport !== 'all') {
          const firstSlice = offer.raw_offer?.slices?.[0];
          const seg0 = firstSlice?.segments?.[0];
          const origCode = seg0?.origin?.iata_code || firstSlice?.origin?.iata_code;
          if (origCode && origCode !== selectedOriginAirport) return false;
        }

        // Price Filter
        if (selectedMaxPrice !== null && parseFloat(offer.total_amount) > selectedMaxPrice) {
          return false;
        }
        // Airline Filter
        if (selectedAirlines.length > 0 && !selectedAirlines.includes(offer.airline_name)) {
          return false;
        }
        // Flight Time Filter
        if (selectedTimeOfDay !== 'all') {
          const tod = getTimeOfDay(offer.departure_time);
          if (tod !== selectedTimeOfDay) return false;
        }
        // Stops Filter
        if (selectedStops === 'direct' && offer.stops !== 0) return false;
        if (selectedStops === '1_stop' && offer.stops !== 1) return false;
        if (selectedStops === 'multi_stop' && offer.stops < 2) return false;

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'cheapest') return parseFloat(a.total_amount) - parseFloat(b.total_amount);
        if (sortBy === 'fastest') return (a.duration_minutes || 9999) - (b.duration_minutes || 9999);
        if (sortBy === 'earliest') return (a.departure_time || '').localeCompare(b.departure_time || '');
        return 0;
      });
  }, [offers, selectedOriginAirport, selectedMaxPrice, selectedAirlines, selectedTimeOfDay, selectedStops, sortBy]);

  const hasActiveFilters =
    (selectedMaxPrice !== null && selectedMaxPrice < maxPrice) ||
    selectedAirlines.length > 0 ||
    selectedTimeOfDay !== 'all' ||
    selectedStops !== 'all' ||
    selectedOriginAirport !== 'all';

  const resetFilters = () => {
    setSelectedMaxPrice(maxPrice);
    setSelectedAirlines([]);
    setSelectedTimeOfDay('all');
    setSelectedStops('all');
    setSelectedOriginAirport('all');
  };

  const toggleAirline = (name) => {
    setSelectedAirlines((prev) =>
      prev.includes(name) ? prev.filter((a) => a !== name) : [...prev, name]
    );
  };

  return (
    <div className="animate-page-enter">
      {/* Unified Hero Banner with Integrated Search */}
      <div className="relative w-full rounded-[36px] overflow-hidden mb-12 shadow-2xl bg-gradient-to-r from-[#4421cb] via-[#5d2bd8] to-[#9e27a6] animate-gradient-flow p-6 sm:p-10 lg:p-12 text-white">
        {/* Glowing Ambient Light Orbs floating smoothly under the search area */}
        <div className="absolute -top-24 -left-20 w-96 h-96 bg-indigo-400/25 rounded-full blur-3xl pointer-events-none animate-float-slow"></div>
        <div className="absolute -bottom-28 -right-16 w-[28rem] h-[28rem] bg-fuchsia-500/25 rounded-full blur-3xl pointer-events-none animate-float-reverse"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[42rem] h-[22rem] bg-purple-500/20 rounded-full blur-3xl pointer-events-none animate-pulse-glow"></div>

        {/* Subtle decorative curved flight trajectory SVG with smooth flowing animation */}
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none"
          viewBox="0 0 1200 600"
          fill="none"
          preserveAspectRatio="none"
        >
          {/* Main animated flight path */}
          <path
            d="M-50 480 C 250 450, 450 150, 800 220 C 1000 260, 1100 100, 1250 80"
            stroke="white"
            strokeWidth="2"
            className="animate-flight-dash opacity-30"
          />
          {/* Secondary animated flight path */}
          <path
            d="M-80 200 C 260 140, 520 480, 880 380 C 1040 330, 1150 420, 1280 400"
            stroke="#e879f9"
            strokeWidth="1.5"
            className="animate-flight-dash-reverse opacity-25"
          />
          {/* Pulsing waypoint radar nodes */}
          <g transform="translate(800, 220)">
            <circle r="9" fill="white" className="animate-ping opacity-35" />
            <circle r="4" fill="white" />
            <circle r="2" fill="#38bdf8" />
          </g>
          <g transform="translate(450, 150)">
            <circle r="7" fill="#c084fc" className="animate-ping opacity-30" />
            <circle r="3.5" fill="#c084fc" />
          </g>
        </svg>

        {/* Top Centered Header Content */}
        <div className="relative z-10 text-center max-w-4xl mx-auto mb-8">
          {/* Live Inventory Pill */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-xs sm:text-sm font-medium text-white/95 mb-6 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="font-semibold text-emerald-300">Live Global Inventory</span>
            <span className="text-white/40">•</span>
            <span>400+ Direct Airlines & Rail Systems</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight mb-3 drop-shadow-md">
            Where to next?
          </h1>
          <p className="text-white/85 text-sm sm:text-base font-normal max-w-2xl mx-auto leading-relaxed">
            Experience seamless booking with global inventory, dynamic fare prediction, and transparent multi-airport itineraries.
          </p>
        </div>

        {/* Controls Above Search Card */}
        <div className="relative z-10 max-w-6xl mx-auto mb-3 flex flex-wrap items-center justify-between gap-3 px-1">
          {/* Trip Type Segmented Selector */}
          <div className="bg-black/35 backdrop-blur-md p-1 rounded-full border border-white/10 inline-flex items-center gap-1 shadow-inner">
            <button
              type="button"
              onClick={() => {
                setTripType('round_trip');
                if (!formData.return_date) handleAdd7DaysReturn();
              }}
              className={`px-4 py-1.5 rounded-full text-xs sm:text-sm font-semibold transition-all ${
                tripType === 'round_trip'
                  ? 'bg-white/20 text-white shadow-sm'
                  : 'text-white/70 hover:text-white'
              }`}
            >
              Round Trip
            </button>
            <button
              type="button"
              onClick={() => {
                setTripType('one_way');
                setFormData((prev) => ({ ...prev, return_date: '' }));
              }}
              className={`px-4 py-1.5 rounded-full text-xs sm:text-sm font-semibold transition-all ${
                tripType === 'one_way'
                  ? 'bg-white/20 text-white shadow-sm'
                  : 'text-white/70 hover:text-white'
              }`}
            >
              One-Way
            </button>
            <button
              type="button"
              onClick={() => setTripType('multi_city')}
              className={`px-4 py-1.5 rounded-full text-xs sm:text-sm font-semibold transition-all inline-flex items-center gap-1.5 ${
                tripType === 'multi_city'
                  ? 'bg-white/20 text-white shadow-sm'
                  : 'text-white/70 hover:text-white'
              }`}
            >
              <span>Multi-City</span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.2 bg-cyan-500/30 text-cyan-300 rounded border border-cyan-400/40">
                Pro
              </span>
            </button>
          </div>

          {/* Right Side Options */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="bg-black/35 hover:bg-black/50 backdrop-blur-md border border-white/10 px-3.5 py-1.5 rounded-full text-xs font-medium text-white flex items-center gap-2 transition-all shadow-sm"
              title="Compare fares ±3 days around your chosen dates"
            >
              <Calendar className="w-3.5 h-3.5 text-slate-300" />
              <span>Low Fare Calendar</span>
              <span className="text-[11px] font-bold text-emerald-400 bg-emerald-500/20 px-1.5 py-0.5 rounded">
                ±3 Days
              </span>
            </button>

            <label className="flex items-center gap-2 text-xs font-medium text-white cursor-pointer select-none bg-black/25 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10">
              <input
                type="checkbox"
                checked={includeRail}
                onChange={(e) => setIncludeRail(e.target.checked)}
                className="w-3.5 h-3.5 rounded accent-indigo-500 cursor-pointer"
              />
              <span>Include Direct Rail</span>
            </label>
          </div>
        </div>

        {/* Transparent Frosted Blur Search Card with glowing aura */}
        <div className="relative z-10 max-w-6xl mx-auto">
          {/* Smooth breathing backlight aura under search fields */}
          <div className="absolute -inset-1.5 bg-gradient-to-r from-indigo-500/30 via-purple-600/25 to-fuchsia-500/30 rounded-[34px] blur-2xl opacity-75 animate-pulse-glow -z-10"></div>

          <div className="bg-black/35 backdrop-blur-2xl rounded-3xl p-6 sm:p-7 border border-white/20 shadow-2xl shadow-black/40">
          <form onSubmit={handleSearch} className="space-y-5">
            {/* Row 1: Origin, Swap, Destination, Departure Date, Return Date */}
            <div className="grid grid-cols-1 lg:grid-cols-[1.3fr_auto_1.3fr_1fr_1fr] gap-4 items-start">
              {/* Origin */}
              <div>
                <AirportAutocomplete
                  label="Flying From (Origin)"
                  headerRight={
                    <span className="text-[11px] font-bold text-cyan-400 tracking-wider lowercase">
                      all hubs
                    </span>
                  }
                  placeholder="City or Airport (e.g. London, Germany)"
                  value={formData.origin}
                  onChange={(iata) => setFormData((prev) => ({ ...prev, origin: iata }))}
                  icon={PlaneTakeoff}
                  iconClassName="h-4 w-4 text-cyan-300 animate-neon-takeoff"
                  required
                />
              </div>

              {/* Swap Button */}
              <div className="hidden lg:flex items-center justify-center pt-7">
                <button
                  type="button"
                  onClick={handleSwap}
                  title="Swap Origin and Destination"
                  className="w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 backdrop-blur-xl flex items-center justify-center text-white transition-all shadow-md active:scale-95"
                >
                  <ArrowLeftRight className="w-4 h-4" />
                </button>
              </div>

              {/* Destination */}
              <div>
                <AirportAutocomplete
                  label="Flying To (Destination)"
                  headerRight={
                    <span className="text-[11px] font-bold text-emerald-400 tracking-wider uppercase">
                      DEALS FROM €49
                    </span>
                  }
                  placeholder="City or Airport (e.g. London, New York)"
                  value={formData.destination}
                  onChange={(iata) => setFormData((prev) => ({ ...prev, destination: iata }))}
                  icon={PlaneLanding}
                  iconClassName="h-4 w-4 text-cyan-300 animate-neon-landing"
                  required
                />
              </div>

              {/* Departure Date */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-300">
                    Departure Date
                  </label>
                </div>
                <div className="relative">
                  <input
                    type="date"
                    name="departure_date"
                    required
                    min={getTodayDate()}
                    value={formData.departure_date}
                    onChange={handleChange}
                    className="w-full bg-black/40 backdrop-blur-xl border border-white/15 hover:border-white/25 focus:border-indigo-400 rounded-2xl px-3.5 py-3 text-white text-sm font-semibold focus:ring-2 focus:ring-indigo-500 transition-all cursor-pointer"
                  />
                </div>
                <div className="text-[11px] text-emerald-400 font-medium mt-1.5 flex items-center gap-1">
                  <span>{formData.departure_date ? new Date(formData.departure_date).toLocaleDateString('en-US', { weekday: 'long' }) : 'Sunday'}</span>
                  <span>•</span>
                  <span>Cheaper day</span>
                </div>
              </div>

              {/* Return Date */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-300">
                    Return (Optional)
                  </label>
                  <button
                    type="button"
                    onClick={handleAdd7DaysReturn}
                    className="text-[11px] font-bold text-slate-400 hover:text-indigo-300 transition-colors"
                  >
                    + Add +7d trip
                  </button>
                </div>
                <div className="relative">
                  <input
                    type="date"
                    name="return_date"
                    min={formData.departure_date || getTodayDate()}
                    value={formData.return_date}
                    onChange={(e) => {
                      handleChange(e);
                      if (e.target.value) setTripType('round_trip');
                    }}
                    className="w-full bg-black/40 backdrop-blur-xl border border-white/15 hover:border-white/25 focus:border-indigo-400 rounded-2xl px-3.5 py-3 text-white text-sm font-semibold focus:ring-2 focus:ring-indigo-500 transition-all cursor-pointer"
                  />
                </div>
                <div className="text-[11px] text-slate-400 mt-1.5 truncate">
                  Flexible return yields 22% lower fares
                </div>
              </div>
            </div>

            {/* Row 2: Adults, Children, Cabin Class, Luggage Note, Search Button */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1.4fr_1.5fr_1.4fr] gap-4 items-end pt-1">
              {/* Adults (12+) */}
              <div>
                <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-300 mb-1.5">
                  Adults (12+)
                </label>
                <div className="bg-black/40 backdrop-blur-xl border border-white/15 rounded-2xl px-2 py-1.5 flex items-center justify-between h-[48px]">
                  <button
                    type="button"
                    onClick={() => updateAdults(-1)}
                    disabled={formData.adult_count <= 1}
                    className="w-8 h-8 rounded-xl bg-white/10 hover:bg-white/20 disabled:opacity-20 text-white flex items-center justify-center transition-colors font-bold"
                  >
                    <Minus className="w-3.5 h-3.5" />
                  </button>
                  <span className="font-bold text-white text-sm">
                    {formData.adult_count}
                  </span>
                  <button
                    type="button"
                    onClick={() => updateAdults(1)}
                    disabled={formData.adult_count >= 9}
                    className="w-8 h-8 rounded-xl bg-white/10 hover:bg-white/20 disabled:opacity-20 text-white flex items-center justify-center transition-colors font-bold"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Children (2-11) */}
              <div>
                <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-300 mb-1.5">
                  Children (2-11)
                </label>
                <div className="bg-black/40 backdrop-blur-xl border border-white/15 rounded-2xl px-2 py-1.5 flex items-center justify-between h-[48px]">
                  <button
                    type="button"
                    onClick={() => updateChildren(-1)}
                    disabled={formData.child_count <= 0}
                    className="w-8 h-8 rounded-xl bg-white/10 hover:bg-white/20 disabled:opacity-20 text-white flex items-center justify-center transition-colors font-bold"
                  >
                    <Minus className="w-3.5 h-3.5" />
                  </button>
                  <span className="font-bold text-white text-sm">
                    {formData.child_count}
                  </span>
                  <button
                    type="button"
                    onClick={() => updateChildren(1)}
                    disabled={formData.child_count >= 9}
                    className="w-8 h-8 rounded-xl bg-white/10 hover:bg-white/20 disabled:opacity-20 text-white flex items-center justify-center transition-colors font-bold"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Cabin Class */}
              <div>
                <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-300 mb-1.5">
                  Cabin Class
                </label>
                <div className="relative">
                  <select
                    name="cabin_class"
                    value={formData.cabin_class}
                    onChange={handleChange}
                    className="w-full bg-black/40 backdrop-blur-xl border border-white/15 hover:border-white/25 rounded-2xl px-3.5 py-3 text-white text-sm font-semibold focus:ring-2 focus:ring-indigo-500 transition-all cursor-pointer h-[48px] appearance-none pr-8"
                  >
                    <option value="economy" className="bg-slate-900 text-white">Economy</option>
                    <option value="premium_economy" className="bg-slate-900 text-white">Premium Economy</option>
                    <option value="business" className="bg-slate-900 text-white">Business</option>
                    <option value="first" className="bg-slate-900 text-white">First</option>
                  </select>
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-slate-400">
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </div>
              </div>

              {/* Carry-on bag pill */}
              <div className="h-[48px] bg-white/10 backdrop-blur-xl border border-white/15 rounded-2xl px-3.5 flex items-center gap-2 text-xs text-white/90 select-none">
                <div className="w-4 h-4 rounded-full border border-white/40 flex items-center justify-center text-white text-[10px]">
                  ✓
                </div>
                <span className="truncate">1 Carry-on bag (8kg included)</span>
              </div>

              {/* Search Button */}
              <div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-[#6b3ff1] via-[#7d48f7] to-[#9333ea] hover:from-[#5d32e0] hover:to-[#8326db] active:scale-[0.99] text-white font-bold px-5 rounded-2xl shadow-xl hover:shadow-purple-500/25 transition-all flex items-center justify-center gap-2.5 disabled:opacity-50 h-[48px]"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Search className="w-4 h-4" />
                  )}
                  <span className="text-sm sm:text-base font-bold">Search Flights</span>
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
      </div>

      <div ref={resultsRef} className="max-w-5xl mx-auto mt-12 mb-24 px-4 sm:px-0 scroll-mt-8">
        {/* Smooth Loading Indicator / Live Search Skeleton */}
        {loading && (
          <div className="space-y-4 animate-card-enter">
            <div className="bg-white/50 backdrop-blur-2xl rounded-3xl p-6 sm:p-7 border border-white/70 shadow-xl shadow-indigo-950/5 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3.5">
                <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 text-indigo-600 flex items-center justify-center border border-indigo-200/50 shrink-0">
                  <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
                </div>
                <div>
                  <h4 className="font-extrabold text-slate-900 text-base">
                    Searching 400+ Airlines & Rail Systems...
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Querying live GDS inventory, pricing matrices, and best connections
                  </p>
                </div>
              </div>
              <div className="w-full sm:w-48 h-2.5 bg-slate-200/70 rounded-full overflow-hidden relative">
                <div className="h-full w-2/3 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full animate-progress-slide"></div>
              </div>
            </div>

            {/* Skeleton Cards with pulsing shimmer */}
            {[1, 2, 3].map((skeletonId) => (
              <div
                key={skeletonId}
                className="bg-white/40 backdrop-blur-xl rounded-3xl p-6 border border-white/60 shadow-sm animate-pulse space-y-4"
              >
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-slate-200/70"></div>
                    <div className="space-y-2">
                      <div className="w-32 h-4 bg-slate-200/70 rounded-md"></div>
                      <div className="w-20 h-3 bg-slate-200/50 rounded-md"></div>
                    </div>
                  </div>
                  <div className="w-44 h-8 bg-slate-200/60 rounded-xl"></div>
                  <div className="w-28 h-10 bg-slate-200/70 rounded-full"></div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error Notification */}
        {error && (
          <div className="bg-red-50 text-red-700 p-5 rounded-2xl font-medium border border-red-200 shadow-sm flex items-start gap-3 mb-6 animate-card-enter">
            <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold">Search Issue</p>
              <p className="text-sm mt-0.5">{formatErrorMessage(error)}</p>
            </div>
          </div>
        )}

        {/* Clean Empty State with Helpful Recommendations */}
        {offers && offers.length === 0 && (
          <div className="text-center py-16 glass rounded-3xl p-8 border border-slate-200 animate-card-enter">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-amber-50 flex items-center justify-center text-amber-600 border border-amber-200">
              <Plane className="w-8 h-8 rotate-45" />
            </div>
            <h3 className="text-2xl font-bold text-slate-900 mb-2">No flights found for this route</h3>
            <p className="text-slate-600 max-w-md mx-auto mb-6 text-sm">
              Airlines may not operate flights between these cities on your selected date, or all available seats are sold out.
            </p>
            <div className="bg-slate-50/80 rounded-2xl p-5 max-w-lg mx-auto text-left text-xs text-slate-600 space-y-2 border border-slate-200">
              <p className="font-bold text-slate-800 text-sm">Travel Tips:</p>
              <p>• Try searching with major international hubs (e.g. Frankfurt, London, Istanbul, Dubai, New York, Erbil).</p>
              <p>• Adjust your departure date by 1 to 3 days to find alternative scheduled departures.</p>
              <p>• Try switching your cabin class to Economy for the widest range of airline availability.</p>
            </div>
          </div>
        )}

        {/* Results with Interactive Filter Sidebar / Header */}
        {offers && offers.length > 0 && (
          <div className="space-y-6">
            {/* Search Route Summary Header */}
            {searchMetadata && (
              <div className="bg-white/45 backdrop-blur-2xl rounded-2xl px-6 py-4 border border-white/60 shadow-lg shadow-indigo-950/5 flex flex-wrap items-center justify-between gap-4 animate-card-enter">
                <div>
                  <div className="flex items-center gap-2.5">
                    <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
                      <span>{searchMetadata.originLabel || formData.origin}</span>
                      <span className="text-indigo-600">→</span>
                      <span>{searchMetadata.destinationLabel || formData.destination}</span>
                    </h2>
                    {searchMetadata.isCountrySearch && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100/80 text-emerald-800 border border-emerald-300/80 backdrop-blur-xs">
                        <Globe className="w-3 h-3 text-emerald-600" /> Country-wide Search
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Showing all flights on {formatFlightDate(formData.departure_date)} across all available airport hubs.
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-black text-indigo-600">{offers.length}</span>
                  <span className="text-xs text-slate-500 font-semibold block">Total Flights Found</span>
                </div>
              </div>
            )}

            {/* Filters Card */}
            <div className="relative animate-card-enter">
              {/* Soft ambient aura to enhance transparency and blur depth */}
              <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 rounded-[32px] blur-xl opacity-75 -z-10"></div>
              
              <div className="bg-white/40 backdrop-blur-2xl rounded-3xl p-6 border border-indigo-400/70 shadow-xl shadow-indigo-950/5">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-5 border-b border-slate-200/60">
                  <div className="flex items-center gap-2">
                    <SlidersHorizontal className="w-5 h-5 text-indigo-600" />
                    <h3 className="font-extrabold text-slate-900 text-lg">Filter & Sort Flights</h3>
                    <span className="text-xs font-semibold bg-indigo-50 text-indigo-700 px-2.5 py-0.5 rounded-full ml-1">
                      {filteredOffers.length} of {offers.length} shown
                    </span>
                  </div>

                  <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
                    {hasActiveFilters && (
                      <button
                        type="button"
                        onClick={resetFilters}
                        className="text-xs font-bold text-red-600 hover:text-red-700 flex items-center gap-1 transition-colors"
                      >
                        <RotateCcw className="w-3.5 h-3.5" /> Reset Filters
                      </button>
                    )}

                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-slate-500">Sort by:</span>
                      <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="bg-white/60 backdrop-blur-md border border-slate-200 rounded-xl px-3 py-1.5 text-xs font-semibold text-slate-800 shadow-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                      >
                        <option value="cheapest">Cheapest First</option>
                        <option value="fastest">Fastest Duration</option>
                        <option value="earliest">Earliest Departure</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Filter Controls Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-5">
                  {/* 1. Price Slider */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Max Price</label>
                      <span className="text-sm font-extrabold text-indigo-700">
                        Up to {currency} {selectedMaxPrice !== null ? selectedMaxPrice : maxPrice}
                      </span>
                    </div>
                    <input
                      type="range"
                      min={minPrice}
                      max={maxPrice}
                      value={selectedMaxPrice !== null ? selectedMaxPrice : maxPrice}
                      onChange={(e) => setSelectedMaxPrice(Number(e.target.value))}
                      className="w-full h-2 bg-slate-200/70 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                    />
                    <div className="flex justify-between text-xs text-slate-400 mt-1">
                      <span>{currency} {minPrice}</span>
                      <span>{currency} {maxPrice}</span>
                    </div>
                  </div>

                  {/* 2. Flight Time of Day */}
                  <div className="md:col-span-2">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                      Departure Time
                    </label>
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                      {[
                        { id: 'all', label: 'Any Time', icon: Clock, color: 'text-indigo-500', activeColor: 'text-indigo-200' },
                        { id: 'morning', label: 'Morning (06-12)', icon: Sunrise, color: 'text-amber-500', activeColor: 'text-amber-300' },
                        { id: 'afternoon', label: 'Afternoon (12-18)', icon: Sun, color: 'text-yellow-500', activeColor: 'text-yellow-300' },
                        { id: 'evening', label: 'Evening (18-24)', icon: Sunset, color: 'text-orange-500', activeColor: 'text-orange-300' },
                        { id: 'night', label: 'Night (00-06)', icon: Moon, color: 'text-purple-500', activeColor: 'text-purple-300' },
                      ].map((t) => {
                        const Icon = t.icon;
                        const active = selectedTimeOfDay === t.id;
                        return (
                          <button
                            key={t.id}
                            type="button"
                            onClick={() => setSelectedTimeOfDay(t.id)}
                            className={`flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all ${
                              active
                                ? 'bg-indigo-600 text-white shadow-md'
                                : 'bg-white/50 hover:bg-white/80 backdrop-blur-sm text-slate-700 border border-slate-200/80 shadow-xs'
                            }`}
                          >
                            <Icon className={`w-3.5 h-3.5 shrink-0 ${active ? t.activeColor : t.color}`} />
                            <span className="truncate">{t.label}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Departure Airport Filter (when country search returns multiple departure airports) */}
                {originAirports.length > 1 && (
                  <div className="pt-5 mt-5 border-t border-slate-200/60">
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                        <Plane className="w-3.5 h-3.5 text-indigo-500" />
                        Departure Airport {searchMetadata?.originLabel ? `(${searchMetadata.originLabel})` : ''}
                      </label>
                      <span className="text-[11px] text-slate-400">
                        {originAirports.length} departure hubs available
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => setSelectedOriginAirport('all')}
                        className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                          selectedOriginAirport === 'all'
                            ? 'bg-indigo-600 text-white shadow-sm'
                            : 'bg-white/50 hover:bg-white/80 backdrop-blur-sm text-slate-700 border border-slate-200/80 shadow-xs'
                        }`}
                      >
                        All Departure Hubs ({offers.length})
                      </button>
                      {originAirports.map((item) => {
                        const active = selectedOriginAirport === item.code;
                        return (
                          <button
                            key={item.code}
                            type="button"
                            onClick={() => setSelectedOriginAirport(item.code)}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                              active
                                ? 'bg-indigo-600 text-white shadow-sm'
                                : 'bg-white/50 hover:bg-white/80 backdrop-blur-sm text-slate-700 border border-slate-200/80 shadow-xs'
                            }`}
                          >
                            <span>{item.name}</span>
                            <span className={`px-1.5 py-0.5 rounded font-mono text-[10px] ${active ? 'bg-indigo-700 text-white' : 'bg-slate-100 text-slate-600'}`}>
                              {item.code}
                            </span>
                            <span className="opacity-75 text-[11px]">({item.count})</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* 3. Airlines & Stops Row */}
                <div className="pt-5 mt-5 border-t border-slate-200/60 flex flex-col md:flex-row gap-6">
                  {/* Stops Filter */}
                  <div className="md:w-1/3">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                      Stops
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {[
                        { id: 'all', label: 'All' },
                        { id: 'direct', label: 'Direct Only' },
                        { id: '1_stop', label: '1 Stop' },
                        { id: 'multi_stop', label: '2+ Stops' },
                      ].map((s) => {
                        const active = selectedStops === s.id;
                        return (
                          <button
                            key={s.id}
                            type="button"
                            onClick={() => setSelectedStops(s.id)}
                            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                              active
                                ? 'bg-indigo-600 text-white shadow-sm'
                                : 'bg-white/50 hover:bg-white/80 backdrop-blur-sm text-slate-700 border border-slate-200/80 shadow-xs'
                            }`}
                          >
                            {s.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Airlines Filter */}
                  <div className="md:w-2/3">
                    <div className="flex justify-between items-center mb-2">
                      <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">
                        Airlines
                      </label>
                      <button
                        type="button"
                        onClick={() => setAirlineSortType(prev => prev === 'count' ? 'alpha' : 'count')}
                        className="text-[10px] font-bold text-indigo-500 hover:text-indigo-700 transition-colors uppercase tracking-wider border border-indigo-200 bg-indigo-50/50 hover:bg-indigo-100 px-2 py-0.5 rounded-full"
                        title="Airline Liste sortieren"
                      >
                        {airlineSortType === 'count' ? 'A-Z ↓' : 'Flights ↓'}
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto pr-1">
                      <button
                        type="button"
                        onClick={() => setSelectedAirlines([])}
                        className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${
                          selectedAirlines.length === 0
                            ? 'bg-slate-900 text-white'
                            : 'bg-white/50 hover:bg-white/80 backdrop-blur-sm text-slate-700 border border-slate-200/80 shadow-xs'
                        }`}
                      >
                        All Airlines ({offers.length})
                      </button>
                      {airlinesList.map((a) => {
                        const active = selectedAirlines.includes(a.name);
                        return (
                          <button
                            key={a.name}
                            type="button"
                            onClick={() => toggleAirline(a.name)}
                            className={`flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold transition-all ${
                              active
                                ? 'bg-indigo-600 text-white shadow-sm'
                                : 'bg-white/50 hover:bg-white/80 backdrop-blur-sm text-slate-700 border border-slate-200/80 shadow-xs'
                            }`}
                          >
                            {active && <Check className="w-3 h-3" />}
                            <span>{a.name}</span>
                            <span className={`text-[10px] ml-0.5 opacity-80 ${active ? 'text-white' : 'text-slate-400'}`}>
                              ({a.count})
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* If Filters returned 0 matches */}
            {filteredOffers.length === 0 && (
              <div className="text-center py-12 glass rounded-3xl p-6 border border-slate-200">
                <p className="text-base font-bold text-slate-800">No flights match your filter selection.</p>
                <p className="text-xs text-slate-500 mt-1">Try raising the maximum price or selecting "Any Time".</p>
                <button
                  type="button"
                  onClick={resetFilters}
                  className="mt-4 bg-indigo-600 text-white px-5 py-2 rounded-full text-xs font-bold hover:bg-indigo-700 transition-colors shadow-sm"
                >
                  Reset All Filters
                </button>
              </div>
            )}

            {/* Flight Cards List */}
            {filteredOffers.map((offer, index) => {
              const isExpanded = expandedOfferId === offer.id;
              const segmentsData = offer.segments_details || [];
              const firstSlice = offer.raw_offer?.slices?.[0];
              const rawSegments = firstSlice?.segments || [];
              const firstSegment = segmentsData[0] || rawSegments[0];
              const lastSegment = segmentsData[segmentsData.length - 1] || rawSegments[rawSegments.length - 1] || firstSegment;

              const originIata = firstSegment?.origin_iata || firstSegment?.origin?.iata_code || firstSlice?.origin?.iata_code || '';
              const originCity = firstSegment?.origin_city || firstSegment?.origin?.city_name || firstSlice?.origin?.city_name || originIata;
              const destIata = lastSegment?.destination_iata || lastSegment?.destination?.iata_code || firstSlice?.destination?.iata_code || '';
              const destCity = lastSegment?.destination_city || lastSegment?.destination?.city_name || firstSlice?.destination?.city_name || destIata;

              return (
                <div
                  key={offer.id}
                  style={{ animationDelay: `${Math.min(index * 60, 480)}ms` }}
                  className="glass rounded-3xl overflow-hidden border border-slate-200 transition-all duration-300 hover:shadow-xl animate-card-enter"
                >
                  {/* Card Header & Summary */}
                  <div className="p-6">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                      {/* Airline Brand */}
                      <div className="flex items-center gap-4 w-full md:w-1/4">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg shadow-md shrink-0">
                          {offer.airline_iata}
                        </div>
                        <div className="truncate">
                          <h3 className="font-bold text-slate-900 text-lg truncate">
                            {offer.airline_name}
                          </h3>
                          <div className="flex flex-wrap items-center gap-1.5 mt-0.5">
                            <span className="inline-block text-xs font-medium text-slate-600 capitalize bg-slate-100 px-2 py-0.5 rounded-md">
                              {offer.cabin_class || 'Economy'}
                            </span>
                            {offer.baggage_allowance?.checked_included ? (
                              <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200/80 px-2 py-0.5 rounded-md">
                                <Luggage className="w-3 h-3 text-emerald-600" />
                                {offer.baggage_allowance.checked_qty}x {offer.baggage_allowance.checked_weight ? offer.baggage_allowance.checked_weight.split(' ')[0] : '23'}kg Included
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-700 bg-amber-50 border border-amber-200/80 px-2 py-0.5 rounded-md">
                                <Luggage className="w-3 h-3 text-amber-600" />
                                Cabin Bag Only ({offer.baggage_allowance?.carry_on_weight ? offer.baggage_allowance.carry_on_weight.split(' ')[0] : '8'}kg)
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Journey Schedule & Stops */}
                      <div className="flex items-center justify-between w-full md:w-2/4">
                        <div className="text-left md:text-right">
                          <div className="flex items-center md:justify-end gap-1.5 mb-1">
                            <span className="text-xs font-black text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-100">
                              {originIata}
                            </span>
                            <span className="text-xs font-semibold text-slate-700 truncate max-w-[120px]">
                              {originCity}
                            </span>
                          </div>
                          <p className="text-2xl font-extrabold text-slate-900">
                            {formatFlightTime(offer.departure_time)}
                          </p>
                          <p className="text-xs text-slate-500 font-medium">
                            {formatFlightDate(offer.departure_time)}
                          </p>
                        </div>

                        <div className="flex-grow mx-6 relative flex flex-col items-center">
                          <span className="text-xs text-slate-500 mb-1 font-semibold flex items-center gap-1">
                            <Clock className="w-3 h-3 text-slate-400" />
                            {offer.duration_minutes
                              ? `${Math.floor(offer.duration_minutes / 60)}h ${offer.duration_minutes % 60}m`
                              : offer.duration || '--'}
                          </span>

                          <div className="w-full h-1 bg-slate-200 rounded-full relative my-1">
                            <div
                              className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-3 h-3 rounded-full border-2 border-white shadow ${
                                offer.stops === 0 ? 'bg-emerald-500' : 'bg-amber-500'
                              }`}
                            ></div>
                          </div>

                          {/* Human-readable stop details with city names */}
                          <div className="mt-1 text-center">
                            {offer.stops === 0 ? (
                              <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-0.5 rounded-full">
                                Direct (Non-stop)
                              </span>
                            ) : (
                              <span className="text-xs font-bold text-amber-700 bg-amber-50 px-2.5 py-0.5 rounded-full">
                                {offer.stops_description || `${offer.stops} Stop${offer.stops > 1 ? 's' : ''}`}
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="text-right md:text-left">
                          <div className="flex items-center md:justify-start justify-end gap-1.5 mb-1">
                            <span className="text-xs font-semibold text-slate-700 truncate max-w-[120px]">
                              {destCity}
                            </span>
                            <span className="text-xs font-black text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-100">
                              {destIata}
                            </span>
                          </div>
                          <p className="text-2xl font-extrabold text-slate-900">
                            {formatFlightTime(offer.arrival_time)}
                          </p>
                          <p className="text-xs text-slate-500 font-medium">
                            {formatFlightDate(offer.arrival_time)}
                          </p>
                        </div>
                      </div>

                      {/* Price & Action */}
                      <div className="flex flex-row md:flex-col items-center justify-between md:justify-center md:items-end w-full md:w-1/4 border-t md:border-t-0 md:border-l border-slate-200 pt-4 md:pt-0 md:pl-6">
                        <div className="text-left md:text-right mb-0 md:mb-3">
                          <p className="text-3xl font-extrabold text-slate-900">
                            {parseFloat(offer.total_amount).toFixed(2)}
                          </p>
                          <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                            {offer.total_currency}
                          </p>
                        </div>
                        <Link
                          to={`/checkout/${offer.id}`}
                          className="bg-slate-900 hover:bg-indigo-600 text-white px-7 py-2.5 rounded-full font-bold transition-all shadow-md hover-lift text-sm"
                        >
                          Select
                        </Link>
                      </div>
                    </div>

                    {/* Expand/Collapse Details Toggle & Quick Perks Preview */}
                    <div className="mt-5 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
                      <button
                        type="button"
                        onClick={() => toggleExpand(offer.id)}
                        className="font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1.5 transition-colors group bg-indigo-50/80 hover:bg-indigo-100 px-3.5 py-1.5 rounded-xl border border-indigo-100"
                      >
                        <span>{isExpanded ? 'Hide Flight Details & Amenities' : 'View Baggage (kg), Services & Details'}</span>
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4 transition-transform group-hover:-translate-y-0.5" />
                        ) : (
                          <ChevronDown className="w-4 h-4 transition-transform group-hover:translate-y-0.5" />
                        )}
                      </button>

                      {/* Quick perks preview badges */}
                      <div className="flex items-center flex-wrap gap-2 text-[11px] text-slate-600">
                        {offer.amenities_details?.wifi_text && (
                          <span className="inline-flex items-center gap-1 bg-slate-100 hover:bg-slate-200/70 px-2 py-0.5 rounded-md transition-colors" title={offer.amenities_details.wifi_text}>
                            <Wifi className="w-3 h-3 text-indigo-500" />
                            <span>Wi-Fi</span>
                          </span>
                        )}
                        {offer.amenities_details?.power_text && (
                          <span className="inline-flex items-center gap-1 bg-slate-100 hover:bg-slate-200/70 px-2 py-0.5 rounded-md transition-colors" title={offer.amenities_details.power_text}>
                            <Zap className="w-3 h-3 text-amber-500" />
                            <span>In-seat Power</span>
                          </span>
                        )}
                        {offer.amenities_details?.meal_text && (
                          <span className="inline-flex items-center gap-1 bg-slate-100 hover:bg-slate-200/70 px-2 py-0.5 rounded-md transition-colors" title={offer.amenities_details.meal_text}>
                            <Utensils className="w-3 h-3 text-emerald-500" />
                            <span>Meals & Drinks</span>
                          </span>
                        )}
                        <span className="text-slate-400 pl-1 border-l border-slate-200">
                          {offer.requires_instant_payment ? 'Instant Card Settlement' : 'Card or Cash Hold'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Expandable Flight Itinerary & Airport Details */}
                  {isExpanded && (
                    <div className="bg-[#07111e] text-slate-100 p-6 sm:p-8 border-t border-slate-800 animate-in fade-in duration-200">
                      {/* Top Header with Confirmed badge and Actions */}
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 pb-5 border-b border-slate-800/90">
                        <div className="flex items-start gap-3.5">
                          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 flex items-center justify-center shrink-0 mt-0.5">
                            <Plane className="w-5 h-5 -rotate-45" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2.5">
                              <h4 className="text-base font-black uppercase tracking-wider text-white">
                                Detailed Flight Itinerary
                              </h4>
                              <span className="inline-flex items-center gap-1.5 text-[11px] font-bold text-emerald-400 bg-emerald-950/70 border border-emerald-600/40 px-2.5 py-0.5 rounded-full">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                                Confirmed
                              </span>
                            </div>
                            <p className="text-xs text-slate-400 mt-1">
                              Outbound leg • Booking Reference:{' '}
                              <span className="font-mono text-cyan-400 font-bold">
                                DFL-{offer.id ? offer.id.replace(/[^0-9]/g, '').slice(0, 5) || '89429' : '89429'}
                              </span>
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          <button
                            type="button"
                            onClick={() => window.print()}
                            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 px-4 py-2 rounded-xl border border-slate-700 transition-colors"
                          >
                            <Printer className="w-3.5 h-3.5 text-slate-400" />
                            <span>Print Boarding Card</span>
                          </button>
                          <Link
                            to={`/checkout/${offer.id}`}
                            className="inline-flex items-center gap-2 text-xs font-bold text-white bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 px-4 py-2 rounded-xl shadow-md transition-all hover-lift"
                          >
                            <Download className="w-3.5 h-3.5" />
                            <span>Download e-Ticket</span>
                          </Link>
                        </div>
                      </div>

                      {/* Segments Loop */}
                      <div className="space-y-6">
                        {segmentsData.map((slice, sIdx) => (
                          <div key={sIdx} className="space-y-6">
                            {slice.segments &&
                              slice.segments.map((seg, segIdx) => {
                                const diffDay = isDifferentDay(seg.departing_at, seg.arriving_at);
                                return (
                                  <div key={segIdx} className="bg-slate-900/60 rounded-3xl p-6 border border-slate-800/80 shadow-lg">
                                    {/* Segment Origin */}
                                    <div className="flex items-start justify-between gap-4">
                                      <div className="flex items-start gap-4">
                                        <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-sm shrink-0">
                                          <Building2 className="w-5 h-5" />
                                        </div>
                                        <div>
                                          <div className="flex flex-wrap items-baseline gap-2.5">
                                            <span className="text-3xl sm:text-4xl font-black text-white tracking-tight">
                                              {formatFlightTime(seg.departing_at)}
                                            </span>
                                            <span className="text-xs font-black text-cyan-300 bg-cyan-950/90 border border-cyan-600/50 px-2.5 py-0.5 rounded-md">
                                              {seg.origin_iata}
                                            </span>
                                            <span className="text-xs text-slate-400 font-medium">
                                              UTC+1 • Central European Time
                                            </span>
                                          </div>
                                          <p className="text-sm font-bold text-slate-100 mt-1">
                                            {seg.origin_name} • Terminal {seg.origin_terminal || '2'}
                                          </p>
                                          <p className="text-xs text-slate-400 mt-0.5">
                                            {seg.origin_city}, {seg.origin_country || 'DE'} • Gate G14 (Boarding closes 30m prior)
                                          </p>
                                        </div>
                                      </div>

                                      <div className="text-right text-xs sm:text-sm font-semibold text-slate-300">
                                        {formatFlightDateWithDay(seg.departing_at)}
                                      </div>
                                    </div>

                                    {/* Flight Transit Bar & In-Flight Amenities (Directly from Screenshot) */}
                                    <div className="my-6 pl-8 border-l-2 border-dashed border-cyan-500/40 ml-6 py-2 space-y-5">
                                      {/* Transit Specs Row */}
                                      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs">
                                        <span className="text-cyan-400 text-sm font-bold flex items-center gap-2">
                                          <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-sm shadow-cyan-500"></span>
                                          {seg.airline_name} • {seg.flight_number}
                                        </span>
                                        <span className="text-cyan-300 bg-cyan-950/40 border border-cyan-800/40 px-2.5 py-1 rounded-lg font-semibold flex items-center gap-1.5">
                                          <Clock className="w-3.5 h-3.5 text-cyan-400" />
                                          {formatDurationString(seg.duration)} ({offer.stops === 0 ? 'Non-stop' : `${offer.stops} Stop`})
                                        </span>
                                        <span className="text-purple-300 bg-purple-950/70 border border-purple-800/60 px-3 py-1 rounded-full font-bold">
                                          Basic Economy (Light)
                                        </span>
                                        <span className="text-slate-400">
                                          {seg.aircraft || 'Airbus A321neo'} • 198 Seats
                                        </span>
                                      </div>

                                      {/* IN-FLIGHT AMENITIES Section (Pixel-matched with Screenshot) */}
                                      <div className="pt-3 pb-1 border-t border-slate-800/80">
                                        <div className="flex items-center justify-between gap-2 mb-3.5">
                                          <div className="flex items-center gap-2">
                                            <Star className="w-3.5 h-3.5 text-cyan-400 fill-cyan-400" />
                                            <span className="text-xs font-black uppercase tracking-wider text-cyan-400">
                                              IN-FLIGHT AMENITIES
                                            </span>
                                            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                                              {seg.airline_name.toUpperCase()} {seg.aircraft ? seg.aircraft.toUpperCase() : 'A321NEO'}
                                            </span>
                                          </div>
                                          <button
                                            type="button"
                                            onClick={() => alert(`Seat Map for ${seg.airline_name} ${seg.flight_number}: Standard 3-3 configuration with ergonomic reclining seats and USB power outlets.`)}
                                            className="text-cyan-400 hover:text-cyan-300 text-xs font-bold flex items-center gap-1 transition-colors"
                                          >
                                            <span>View Seat Map</span>
                                            <span>&gt;</span>
                                          </button>
                                        </div>

                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                          {/* Wi-Fi */}
                                          <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-800/60 flex items-center justify-center text-cyan-400 shrink-0 shadow-inner">
                                              <Wifi className="w-4 h-4" />
                                            </div>
                                            <div>
                                              <p className="text-xs font-bold text-white leading-tight">
                                                Wi-Fi Available
                                              </p>
                                              <p className="text-xs font-semibold text-cyan-400 mt-0.5">
                                                Free Messaging
                                              </p>
                                            </div>
                                          </div>

                                          {/* In-seat Power */}
                                          <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-xl bg-amber-950/80 border border-amber-800/60 flex items-center justify-center text-amber-400 shrink-0 shadow-inner">
                                              <Zap className="w-4 h-4" />
                                            </div>
                                            <div>
                                              <p className="text-xs font-bold text-white leading-tight">
                                                In-seat Power
                                              </p>
                                              <p className="text-xs font-semibold text-slate-400 mt-0.5">
                                                110V AC & USB
                                              </p>
                                            </div>
                                          </div>

                                          {/* Complimentary Meal */}
                                          <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-xl bg-emerald-950/80 border border-emerald-800/60 flex items-center justify-center text-emerald-400 shrink-0 shadow-inner">
                                              <Utensils className="w-4 h-4" />
                                            </div>
                                            <div>
                                              <p className="text-xs font-bold text-white leading-tight">
                                                Complimentary Meal
                                              </p>
                                              <p className="text-xs font-semibold text-slate-400 mt-0.5">
                                                Snacks & Drinks
                                              </p>
                                            </div>
                                          </div>

                                          {/* 30"-32" Pitch */}
                                          <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-xl bg-purple-950/80 border border-purple-800/60 flex items-center justify-center text-purple-400 shrink-0 shadow-inner">
                                              <Check className="w-4 h-4" />
                                            </div>
                                            <div>
                                              <p className="text-xs font-bold text-white leading-tight">
                                                30"-32" Pitch
                                              </p>
                                              <p className="text-xs font-semibold text-slate-400 mt-0.5">
                                                Recliner Seat
                                              </p>
                                            </div>
                                          </div>
                                        </div>
                                      </div>
                                    </div>

                                    {/* Segment Destination */}
                                    <div className="flex items-start justify-between gap-4">
                                      <div className="flex items-start gap-4">
                                        <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-sm shrink-0">
                                          <MapPin className="w-5 h-5" />
                                        </div>
                                        <div>
                                          <div className="flex flex-wrap items-baseline gap-2.5">
                                            <span className="text-3xl sm:text-4xl font-black text-white tracking-tight">
                                              {formatFlightTime(seg.arriving_at)}
                                            </span>
                                            <span className="text-xs font-black text-cyan-300 bg-cyan-950/90 border border-cyan-600/50 px-2.5 py-0.5 rounded-md">
                                              {seg.destination_iata}
                                            </span>
                                            {diffDay && (
                                              <span className="bg-amber-500/20 border border-amber-500/40 text-amber-300 text-[10px] px-2 py-0.5 rounded font-bold">
                                                +1 Day
                                              </span>
                                            )}
                                            <span className="text-xs text-slate-400 font-medium">
                                              UTC+3 • Arabia Standard Time
                                            </span>
                                          </div>
                                          <p className="text-sm font-bold text-slate-100 mt-1">
                                            {seg.destination_name} • Terminal {seg.destination_terminal || '1'}
                                          </p>
                                          <p className="text-xs text-slate-400 mt-0.5">
                                            {seg.destination_city}, {seg.destination_country || 'IQ'} • Baggage Belt 3
                                          </p>
                                        </div>
                                      </div>

                                      <div className="text-right text-xs sm:text-sm font-semibold text-slate-300">
                                        {formatFlightDateWithDay(seg.arriving_at)}
                                      </div>
                                    </div>

                                    {/* Layover Banner if next segment exists */}
                                    {seg.layover_after && (
                                      <div className="mt-5 p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-2xl text-amber-300 text-xs font-semibold flex items-center gap-2.5">
                                        <Clock className="w-4 h-4 text-amber-400 shrink-0" />
                                        <span>{seg.layover_after} • Connection / Plane Change</span>
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                          </div>
                        ))}
                      </div>

                      {/* Section 2: Baggage Allowance & Weight Breakdown (Kg) */}
                      <div className="mt-8 pt-6 border-t border-slate-700/80">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-4">
                          <h4 className="text-sm font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-2">
                            <Luggage className="w-4 h-4" /> Baggage Allowance & Weight Limits
                          </h4>
                          <span className="text-xs text-slate-400 font-medium">
                            Standard IATA airline baggage allowances apply
                          </span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          {/* Personal Item */}
                          <div className="bg-slate-800/90 rounded-2xl p-4 border border-slate-700 flex flex-col justify-between hover:border-slate-600 transition-colors">
                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <div className="p-2 bg-indigo-500/20 text-indigo-400 rounded-xl">
                                  <Briefcase className="w-4 h-4" />
                                </div>
                                <span className="text-[11px] font-bold text-emerald-400 bg-emerald-950/70 border border-emerald-700/50 px-2 py-0.5 rounded-full">
                                  Included Free
                                </span>
                              </div>
                              <h5 className="font-bold text-white text-sm">Small Personal Item</h5>
                              <p className="text-xs text-indigo-300 font-semibold mt-1">
                                {offer.baggage_allowance?.personal_item_text || '1x Personal Item (up to 4 kg)'}
                              </p>
                              <p className="text-xs text-slate-400 mt-2">
                                Fits under seat in front (laptop bag, handbag, or small daypack).
                              </p>
                            </div>
                            <div className="mt-4 pt-2.5 border-t border-slate-700/60 flex items-center justify-between text-[11px] text-slate-400">
                              <span>Max Weight:</span>
                              <span className="font-bold text-slate-200">4 kg (8.8 lbs)</span>
                            </div>
                          </div>

                          {/* Cabin Baggage */}
                          <div className="bg-slate-800/90 rounded-2xl p-4 border border-slate-700 flex flex-col justify-between hover:border-slate-600 transition-colors">
                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <div className="p-2 bg-purple-500/20 text-purple-400 rounded-xl">
                                  <Luggage className="w-4 h-4" />
                                </div>
                                <span className="text-[11px] font-bold text-emerald-400 bg-emerald-950/70 border border-emerald-700/50 px-2 py-0.5 rounded-full">
                                  Included Free
                                </span>
                              </div>
                              <h5 className="font-bold text-white text-sm">Cabin / Overhead Bag</h5>
                              <p className="text-xs text-purple-300 font-semibold mt-1">
                                {offer.baggage_allowance?.carry_on_text || '1x Cabin Bag (up to 8 kg)'}
                              </p>
                              <p className="text-xs text-slate-400 mt-2">
                                Fits in overhead locker. Dimensions max {offer.baggage_allowance?.carry_on_dimensions || '55 x 40 x 23 cm'}.
                              </p>
                            </div>
                            <div className="mt-4 pt-2.5 border-t border-slate-700/60 flex items-center justify-between text-[11px] text-slate-400">
                              <span>Max Weight:</span>
                              <span className="font-bold text-slate-200">{offer.baggage_allowance?.carry_on_weight || '8 kg (17.6 lbs)'}</span>
                            </div>
                          </div>

                          {/* Checked Baggage */}
                          <div className={`rounded-2xl p-4 border flex flex-col justify-between transition-colors ${
                            offer.baggage_allowance?.checked_included
                              ? 'bg-slate-800/90 border-slate-700 hover:border-slate-600'
                              : 'bg-amber-950/20 border-amber-700/40 hover:border-amber-600/50'
                          }`}>
                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <div className={`p-2 rounded-xl ${
                                  offer.baggage_allowance?.checked_included
                                    ? 'bg-emerald-500/20 text-emerald-400'
                                    : 'bg-amber-500/20 text-amber-400'
                                }`}>
                                  <Luggage className="w-4 h-4" />
                                </div>
                                {offer.baggage_allowance?.checked_included ? (
                                  <span className="text-[11px] font-bold text-emerald-400 bg-emerald-950/70 border border-emerald-700/50 px-2 py-0.5 rounded-full">
                                    Included in Fare
                                  </span>
                                ) : (
                                  <span className="text-[11px] font-bold text-amber-300 bg-amber-950/70 border border-amber-700/50 px-2 py-0.5 rounded-full">
                                    Add at Checkout
                                  </span>
                                )}
                              </div>
                              <h5 className="font-bold text-white text-sm">Checked Baggage (Hold)</h5>
                              <p className={`text-xs font-semibold mt-1 ${
                                offer.baggage_allowance?.checked_included ? 'text-emerald-300' : 'text-amber-300'
                              }`}>
                                {offer.baggage_allowance?.checked_text || 'No checked bag included'}
                              </p>
                              <p className="text-xs text-slate-400 mt-2">
                                {offer.baggage_allowance?.checked_included
                                  ? 'Drop at check-in desk before security. Standard combined size max 158 cm.'
                                  : 'Economy Light fare. You can add checked bags during checkout or at airport.'}
                              </p>
                            </div>
                            <div className="mt-4 pt-2.5 border-t border-slate-700/60 flex items-center justify-between text-[11px] text-slate-400">
                              <span>Weight Allowance:</span>
                              <span className="font-bold text-slate-200">
                                {offer.baggage_allowance?.checked_included
                                  ? offer.baggage_allowance?.checked_weight
                                  : `Up to ${offer.baggage_allowance?.checked_weight || '23 kg'} (Optional)`}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Section 3: Ticket Conditions & Environment */}
                      <div className="mt-8 pt-6 border-t border-slate-700/80 flex flex-wrap items-center justify-between gap-4 text-xs">
                        <div className="flex flex-wrap items-center gap-4">
                          <div className="flex items-center gap-2">
                            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                            <span className="text-slate-300">
                              Changes: <strong className="text-white">{offer.fare_rules?.change_text || 'Subject to airline fare rules'}</strong>
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                            <span className="text-slate-300">
                              Cancellations: <strong className="text-white">{offer.fare_rules?.refund_text || 'Subject to airline fare rules'}</strong>
                            </span>
                          </div>
                        </div>

                        {offer.emissions_kg && (
                          <div className="flex items-center gap-1.5 text-emerald-400 bg-emerald-950/60 border border-emerald-800/50 px-3 py-1 rounded-full">
                            <Leaf className="w-3.5 h-3.5" />
                            <span>CO₂ Footprint: <strong>{offer.emissions_kg} kg</strong> per passenger</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;
