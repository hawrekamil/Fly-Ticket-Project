import React, { useState } from 'react';
import { Plane, Search, Globe } from 'lucide-react';

const AIRLINES = [
  { code: 'AA', name: 'American Airlines', country: 'US', region: 'North America' },
  { code: 'DL', name: 'Delta Air Lines', country: 'US', region: 'North America' },
  { code: 'UA', name: 'United Airlines', country: 'US', region: 'North America' },
  { code: 'SW', name: 'Southwest Airlines', country: 'US', region: 'North America' },
  { code: 'AC', name: 'Air Canada', country: 'CA', region: 'North America' },
  { code: 'BA', name: 'British Airways', country: 'GB', region: 'Europe' },
  { code: 'LH', name: 'Lufthansa', country: 'DE', region: 'Europe' },
  { code: 'AF', name: 'Air France', country: 'FR', region: 'Europe' },
  { code: 'KL', name: 'KLM Royal Dutch Airlines', country: 'NL', region: 'Europe' },
  { code: 'IB', name: 'Iberia', country: 'ES', region: 'Europe' },
  { code: 'U2', name: 'easyJet', country: 'GB', region: 'Europe' },
  { code: 'FR', name: 'Ryanair', country: 'IE', region: 'Europe' },
  { code: 'EK', name: 'Emirates', country: 'AE', region: 'Middle East' },
  { code: 'QR', name: 'Qatar Airways', country: 'QA', region: 'Middle East' },
  { code: 'EY', name: 'Etihad Airways', country: 'AE', region: 'Middle East' },
  { code: 'TK', name: 'Turkish Airlines', country: 'TR', region: 'Europe / Middle East' },
  { code: 'SQ', name: 'Singapore Airlines', country: 'SG', region: 'Asia' },
  { code: 'CX', name: 'Cathay Pacific', country: 'HK', region: 'Asia' },
  { code: 'NH', name: 'All Nippon Airways (ANA)', country: 'JP', region: 'Asia' },
  { code: 'JL', name: 'Japan Airlines (JAL)', country: 'JP', region: 'Asia' },
  { code: 'KE', name: 'Korean Air', country: 'KR', region: 'Asia' },
  { code: 'QF', name: 'Qantas', country: 'AU', region: 'Oceania' },
  { code: 'NZ', name: 'Air New Zealand', country: 'NZ', region: 'Oceania' },
  { code: 'LA', name: 'LATAM Airlines', country: 'CL', region: 'South America' },
  { code: 'CM', name: 'Copa Airlines', country: 'PA', region: 'Central America' },
  { code: 'SA', name: 'South African Airways', country: 'ZA', region: 'Africa' },
  { code: 'ET', name: 'Ethiopian Airlines', country: 'ET', region: 'Africa' },
  { code: 'MS', name: 'EgyptAir', country: 'EG', region: 'Africa' },
  { code: 'AI', name: 'Air India', country: 'IN', region: 'Asia' },
  { code: 'TG', name: 'Thai Airways', country: 'TH', region: 'Asia' },
  { code: 'MH', name: 'Malaysia Airlines', country: 'MY', region: 'Asia' },
  { code: 'SU', name: 'Aeroflot', country: 'RU', region: 'Europe / Asia' },
  { code: 'AY', name: 'Finnair', country: 'FI', region: 'Europe' },
  { code: 'SK', name: 'SAS Scandinavian Airlines', country: 'SE', region: 'Europe' },
  { code: 'LX', name: 'Swiss International Air Lines', country: 'CH', region: 'Europe' },
  { code: 'OS', name: 'Austrian Airlines', country: 'AT', region: 'Europe' },
  { code: 'TP', name: 'TAP Air Portugal', country: 'PT', region: 'Europe' },
  { code: 'EI', name: 'Aer Lingus', country: 'IE', region: 'Europe' },
  { code: 'AZ', name: 'ITA Airways', country: 'IT', region: 'Europe' },
  { code: 'LO', name: 'LOT Polish Airlines', country: 'PL', region: 'Europe' },
].sort((a, b) => a.name.localeCompare(b.name));

const Airlines = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredAirlines = AIRLINES.filter((airline) =>
    airline.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    airline.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="w-full max-w-7xl mx-auto animate-page-enter">
      {/* Header Section */}
      <div className="mb-10 text-center space-y-4">
        <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">
          Global Airline <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-indigo-400">Directory</span>
        </h1>
        <p className="text-slate-400 max-w-2xl mx-auto text-lg">
          Explore our network of over {AIRLINES.length}+ major carriers connecting you to thousands of destinations worldwide.
        </p>
      </div>

      {/* Search Bar */}
      <div className="relative max-w-2xl mx-auto mb-12">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-slate-400" />
        </div>
        <input
          type="text"
          placeholder="Search by airline name or IATA code..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-12 pr-4 py-4 bg-slate-900/60 border border-slate-700/80 rounded-2xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 shadow-xl backdrop-blur-md transition-all"
        />
      </div>

      {/* Airlines Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {filteredAirlines.length > 0 ? (
          filteredAirlines.map((airline) => (
            <div
              key={airline.code}
              className="bg-slate-900/40 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 hover:bg-slate-800/60 hover:border-cyan-500/30 transition-all hover:-translate-y-1 hover:shadow-2xl hover:shadow-cyan-900/20 group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-slate-800/80 border border-slate-700 flex items-center justify-center group-hover:bg-cyan-950/30 group-hover:border-cyan-500/30 transition-colors">
                  <Plane className="h-6 w-6 text-cyan-400 -rotate-45" />
                </div>
                <span className="px-3 py-1 bg-slate-800/80 text-slate-300 text-xs font-bold rounded-full border border-slate-700">
                  {airline.code}
                </span>
              </div>
              
              <h3 className="text-xl font-bold text-white mb-1 group-hover:text-cyan-300 transition-colors">
                {airline.name}
              </h3>
              
              <div className="flex items-center gap-1.5 text-sm font-medium text-slate-400 mt-3">
                <Globe className="h-4 w-4" />
                <span>{airline.region}</span>
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-full py-12 text-center text-slate-400">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-800/50 mb-4">
              <Search className="h-8 w-8 text-slate-500" />
            </div>
            <p className="text-lg">No airlines found matching "{searchTerm}"</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Airlines;
