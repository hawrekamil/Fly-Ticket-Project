"""
Country and Airport Mapping Directory
====================================
Provides comprehensive country-to-airports mapping with multilingual aliases
(English, German, native), city lookup, and resolver logic for flight searches.
"""

from typing import Any

COUNTRIES_DATA: list[dict[str, Any]] = [
    {
        "country_code": "DE",
        "name": "Germany",
        "native_name": "Deutschland",
        "flag": "🇩🇪",
        "aliases": ["germany", "deutschland", "de", "allemagne", "ger", "almanya"],
        "primary_airports": ["FRA", "MUC", "BER"],
        "airports": [
            {"iata_code": "FRA", "name": "Frankfurt Airport", "city_name": "Frankfurt"},
            {"iata_code": "MUC", "name": "Munich Airport", "city_name": "Munich"},
            {"iata_code": "BER", "name": "Berlin Brandenburg Airport", "city_name": "Berlin"},
            {"iata_code": "DUS", "name": "Dusseldorf Airport", "city_name": "Dusseldorf"},
            {"iata_code": "HAM", "name": "Hamburg Airport", "city_name": "Hamburg"},
            {"iata_code": "STR", "name": "Stuttgart Airport", "city_name": "Stuttgart"},
            {"iata_code": "CGN", "name": "Cologne Bonn Airport", "city_name": "Cologne"},
        ],
    },
    {
        "country_code": "GB",
        "name": "United Kingdom",
        "native_name": "England / UK",
        "flag": "🇬🇧",
        "aliases": [
            "england", "united kingdom", "uk", "great britain", "gb", "großbritannien",
            "grossbritannien", "britain", "scotland", "wales"
        ],
        "primary_airports": ["LON", "MAN", "EDI"],
        "airports": [
            {"iata_code": "LON", "name": "London All Airports (Heathrow, Gatwick, Stansted, Luton)", "city_name": "London"},
            {"iata_code": "LHR", "name": "Heathrow Airport", "city_name": "London"},
            {"iata_code": "LGW", "name": "Gatwick Airport", "city_name": "London"},
            {"iata_code": "STN", "name": "Stansted Airport", "city_name": "London"},
            {"iata_code": "MAN", "name": "Manchester Airport", "city_name": "Manchester"},
            {"iata_code": "EDI", "name": "Edinburgh Airport", "city_name": "Edinburgh"},
            {"iata_code": "BHX", "name": "Birmingham Airport", "city_name": "Birmingham"},
        ],
    },
    {
        "country_code": "TR",
        "name": "Turkey",
        "native_name": "Türkiye",
        "flag": "🇹🇷",
        "aliases": ["turkey", "türkiye", "turkiye", "türkei", "turkei", "tr"],
        "primary_airports": ["IST", "SAW", "AYT"],
        "airports": [
            {"iata_code": "IST", "name": "Istanbul Airport", "city_name": "Istanbul"},
            {"iata_code": "SAW", "name": "Sabiha Gokcen Airport", "city_name": "Istanbul"},
            {"iata_code": "AYT", "name": "Antalya Airport", "city_name": "Antalya"},
            {"iata_code": "ESB", "name": "Ankara Esenboga Airport", "city_name": "Ankara"},
            {"iata_code": "ADB", "name": "Izmir Adnan Menderes Airport", "city_name": "Izmir"},
        ],
    },
    {
        "country_code": "IQ",
        "name": "Iraq",
        "native_name": "العراق / Irak",
        "flag": "🇮🇶",
        "aliases": ["iraq", "irak", "iq", "erbil", "baghdad", "kurdistan"],
        "primary_airports": ["EBL", "BGW", "ISU"],
        "airports": [
            {"iata_code": "EBL", "name": "Erbil International Airport", "city_name": "Erbil"},
            {"iata_code": "BGW", "name": "Baghdad International Airport", "city_name": "Baghdad"},
            {"iata_code": "ISU", "name": "Sulaimaniyah International Airport", "city_name": "Sulaimaniyah"},
            {"iata_code": "BSR", "name": "Basra International Airport", "city_name": "Basra"},
        ],
    },
    {
        "country_code": "US",
        "name": "United States",
        "native_name": "USA",
        "flag": "🇺🇸",
        "aliases": ["united states", "usa", "us", "america", "vereinigte staaten"],
        "primary_airports": ["NYC", "LAX", "ORD", "MIA"],
        "airports": [
            {"iata_code": "NYC", "name": "New York All Airports (JFK, EWR, LGA)", "city_name": "New York"},
            {"iata_code": "JFK", "name": "John F. Kennedy International Airport", "city_name": "New York"},
            {"iata_code": "LAX", "name": "Los Angeles International Airport", "city_name": "Los Angeles"},
            {"iata_code": "ORD", "name": "O'Hare International Airport", "city_name": "Chicago"},
            {"iata_code": "MIA", "name": "Miami International Airport", "city_name": "Miami"},
            {"iata_code": "SFO", "name": "San Francisco International Airport", "city_name": "San Francisco"},
        ],
    },
    {
        "country_code": "FR",
        "name": "France",
        "native_name": "Frankreich",
        "flag": "🇫🇷",
        "aliases": ["france", "frankreich", "fr"],
        "primary_airports": ["PAR", "NCE", "LYS"],
        "airports": [
            {"iata_code": "PAR", "name": "Paris All Airports (CDG, ORY)", "city_name": "Paris"},
            {"iata_code": "CDG", "name": "Charles de Gaulle Airport", "city_name": "Paris"},
            {"iata_code": "ORY", "name": "Orly Airport", "city_name": "Paris"},
            {"iata_code": "NCE", "name": "Nice Cote d'Azur Airport", "city_name": "Nice"},
            {"iata_code": "LYS", "name": "Lyon-Saint Exupery Airport", "city_name": "Lyon"},
            {"iata_code": "MRS", "name": "Marseille Provence Airport", "city_name": "Marseille"},
        ],
    },
    {
        "country_code": "ES",
        "name": "Spain",
        "native_name": "España / Spanien",
        "flag": "🇪🇸",
        "aliases": ["spain", "spanien", "españa", "espana", "es"],
        "primary_airports": ["MAD", "BCN", "AGP"],
        "airports": [
            {"iata_code": "MAD", "name": "Adolfo Suarez Madrid-Barajas Airport", "city_name": "Madrid"},
            {"iata_code": "BCN", "name": "Barcelona-El Prat Airport", "city_name": "Barcelona"},
            {"iata_code": "AGP", "name": "Malaga-Costa del Sol Airport", "city_name": "Malaga"},
            {"iata_code": "PMI", "name": "Palma de Mallorca Airport", "city_name": "Palma de Mallorca"},
        ],
    },
    {
        "country_code": "IT",
        "name": "Italy",
        "native_name": "Italia / Italien",
        "flag": "🇮🇹",
        "aliases": ["italy", "italien", "italia", "it"],
        "primary_airports": ["ROM", "MIL", "VCE"],
        "airports": [
            {"iata_code": "ROM", "name": "Rome All Airports (FCO, CIA)", "city_name": "Rome"},
            {"iata_code": "FCO", "name": "Leonardo da Vinci Fiumicino Airport", "city_name": "Rome"},
            {"iata_code": "MIL", "name": "Milan All Airports (MXP, LIN, BGY)", "city_name": "Milan"},
            {"iata_code": "MXP", "name": "Milan Malpensa Airport", "city_name": "Milan"},
            {"iata_code": "VCE", "name": "Venice Marco Polo Airport", "city_name": "Venice"},
            {"iata_code": "NAP", "name": "Naples International Airport", "city_name": "Naples"},
        ],
    },
    {
        "country_code": "NL",
        "name": "Netherlands",
        "native_name": "Nederland / Niederlande",
        "flag": "🇳🇱",
        "aliases": ["netherlands", "niederlande", "holland", "nl", "amsterdam"],
        "primary_airports": ["AMS"],
        "airports": [
            {"iata_code": "AMS", "name": "Schiphol Airport", "city_name": "Amsterdam"},
            {"iata_code": "EIN", "name": "Eindhoven Airport", "city_name": "Eindhoven"},
        ],
    },
    {
        "country_code": "AT",
        "name": "Austria",
        "native_name": "Österreich",
        "flag": "🇦🇹",
        "aliases": ["austria", "österreich", "oesterreich", "at", "vienna"],
        "primary_airports": ["VIE"],
        "airports": [
            {"iata_code": "VIE", "name": "Vienna International Airport", "city_name": "Vienna"},
            {"iata_code": "SZG", "name": "Salzburg Airport", "city_name": "Salzburg"},
        ],
    },
    {
        "country_code": "CH",
        "name": "Switzerland",
        "native_name": "Schweiz / Suisse",
        "flag": "🇨🇭",
        "aliases": ["switzerland", "schweiz", "suisse", "svizzera", "ch", "zurich"],
        "primary_airports": ["ZRH", "GVA"],
        "airports": [
            {"iata_code": "ZRH", "name": "Zurich Airport", "city_name": "Zurich"},
            {"iata_code": "GVA", "name": "Geneva Airport", "city_name": "Geneva"},
            {"iata_code": "BSL", "name": "EuroAirport Basel Mulhouse Freiburg", "city_name": "Basel"},
        ],
    },
    {
        "country_code": "AE",
        "name": "United Arab Emirates",
        "native_name": "الإمارات / VAE",
        "flag": "🇦🇪",
        "aliases": ["united arab emirates", "uae", "vae", "dubai", "emirates", "ae"],
        "primary_airports": ["DXB", "AUH"],
        "airports": [
            {"iata_code": "DXB", "name": "Dubai International Airport", "city_name": "Dubai"},
            {"iata_code": "AUH", "name": "Zayed International Airport", "city_name": "Abu Dhabi"},
            {"iata_code": "SHJ", "name": "Sharjah International Airport", "city_name": "Sharjah"},
        ],
    },
    {
        "country_code": "EG",
        "name": "Egypt",
        "native_name": "مصر / Ägypten",
        "flag": "🇪🇬",
        "aliases": ["egypt", "ägypten", "aegypten", "cairo", "eg"],
        "primary_airports": ["CAI", "HRG"],
        "airports": [
            {"iata_code": "CAI", "name": "Cairo International Airport", "city_name": "Cairo"},
            {"iata_code": "HRG", "name": "Hurghada International Airport", "city_name": "Hurghada"},
            {"iata_code": "SSH", "name": "Sharm El Sheikh Airport", "city_name": "Sharm El Sheikh"},
        ],
    },
    {
        "country_code": "GR",
        "name": "Greece",
        "native_name": "Griechenland / Ελλάδα",
        "flag": "🇬🇷",
        "aliases": ["greece", "griechenland", "hellas", "gr", "athens"],
        "primary_airports": ["ATH", "HER"],
        "airports": [
            {"iata_code": "ATH", "name": "Athens International Airport", "city_name": "Athens"},
            {"iata_code": "HER", "name": "Heraklion International Airport", "city_name": "Crete / Heraklion"},
            {"iata_code": "SKG", "name": "Thessaloniki Airport", "city_name": "Thessaloniki"},
        ],
    },
    {
        "country_code": "PT",
        "name": "Portugal",
        "native_name": "Portugal",
        "flag": "🇵🇹",
        "aliases": ["portugal", "pt", "lisbon"],
        "primary_airports": ["LIS", "OPO"],
        "airports": [
            {"iata_code": "LIS", "name": "Humberto Delgado Airport", "city_name": "Lisbon"},
            {"iata_code": "OPO", "name": "Francisco Sa Carneiro Airport", "city_name": "Porto"},
        ],
    },
    {
        "country_code": "PL",
        "name": "Poland",
        "native_name": "Polska / Polen",
        "flag": "🇵🇱",
        "aliases": ["poland", "polen", "polska", "pl", "warsaw"],
        "primary_airports": ["WAW", "KRK"],
        "airports": [
            {"iata_code": "WAW", "name": "Warsaw Chopin Airport", "city_name": "Warsaw"},
            {"iata_code": "KRK", "name": "Krakow John Paul II Airport", "city_name": "Krakow"},
        ],
    },
    {
        "country_code": "SE",
        "name": "Sweden",
        "native_name": "Sverige / Schweden",
        "flag": "🇸🇪",
        "aliases": ["sweden", "schweden", "sverige", "se", "stockholm"],
        "primary_airports": ["ARN"],
        "airports": [
            {"iata_code": "ARN", "name": "Stockholm Arlanda Airport", "city_name": "Stockholm"},
            {"iata_code": "GOT", "name": "Gothenburg Landvetter Airport", "city_name": "Gothenburg"},
        ],
    },
    {
        "country_code": "NO",
        "name": "Norway",
        "native_name": "Norge / Norwegen",
        "flag": "🇳🇴",
        "aliases": ["norway", "norwegen", "norge", "no", "oslo"],
        "primary_airports": ["OSL"],
        "airports": [
            {"iata_code": "OSL", "name": "Oslo Airport Gardermoen", "city_name": "Oslo"},
            {"iata_code": "BGO", "name": "Bergen Airport Flesland", "city_name": "Bergen"},
        ],
    },
    {
        "country_code": "DK",
        "name": "Denmark",
        "native_name": "Danmark / Dänemark",
        "flag": "🇩🇰",
        "aliases": ["denmark", "dänemark", "daenemark", "danmark", "dk", "copenhagen"],
        "primary_airports": ["CPH"],
        "airports": [
            {"iata_code": "CPH", "name": "Copenhagen Airport", "city_name": "Copenhagen"},
        ],
    },
    {
        "country_code": "CA",
        "name": "Canada",
        "native_name": "Canada / Kanada",
        "flag": "🇨🇦",
        "aliases": ["canada", "kanada", "ca", "toronto", "vancouver"],
        "primary_airports": ["YYZ", "YVR"],
        "airports": [
            {"iata_code": "YYZ", "name": "Toronto Pearson International Airport", "city_name": "Toronto"},
            {"iata_code": "YVR", "name": "Vancouver International Airport", "city_name": "Vancouver"},
            {"iata_code": "YUL", "name": "Montreal-Trudeau International Airport", "city_name": "Montreal"},
        ],
    },
    {
        "country_code": "QA",
        "name": "Qatar",
        "native_name": "قطر / Katar",
        "flag": "🇶🇦",
        "aliases": ["qatar", "katar", "doha", "qa"],
        "primary_airports": ["DOH"],
        "airports": [
            {"iata_code": "DOH", "name": "Hamad International Airport", "city_name": "Doha"},
        ],
    },
    {
        "country_code": "SA",
        "name": "Saudi Arabia",
        "native_name": "السعودية / Saudi-Arabien",
        "flag": "🇸🇦",
        "aliases": ["saudi arabia", "saudi", "saudi-arabien", "sa", "riyadh", "jeddah"],
        "primary_airports": ["JED", "RUH"],
        "airports": [
            {"iata_code": "JED", "name": "King Abdulaziz International Airport", "city_name": "Jeddah"},
            {"iata_code": "RUH", "name": "King Khalid International Airport", "city_name": "Riyadh"},
        ],
    },
    {
        "country_code": "JO",
        "name": "Jordan",
        "native_name": "الأردن / Jordanien",
        "flag": "🇯🇴",
        "aliases": ["jordan", "jordanien", "amman", "jo"],
        "primary_airports": ["AMM"],
        "airports": [
            {"iata_code": "AMM", "name": "Queen Alia International Airport", "city_name": "Amman"},
        ],
    },
    {
        "country_code": "LB",
        "name": "Lebanon",
        "native_name": "لبنان / Libanon",
        "flag": "🇱🇧",
        "aliases": ["lebanon", "libanon", "beirut", "lb"],
        "primary_airports": ["BEY"],
        "airports": [
            {"iata_code": "BEY", "name": "Beirut-Rafic Hariri International Airport", "city_name": "Beirut"},
        ],
    },
    {
        "country_code": "MA",
        "name": "Morocco",
        "native_name": "المغرب / Marokko",
        "flag": "🇲🇦",
        "aliases": ["morocco", "marokko", "casablanca", "marrakech", "ma"],
        "primary_airports": ["CMN", "RAK"],
        "airports": [
            {"iata_code": "CMN", "name": "Mohammed V International Airport", "city_name": "Casablanca"},
            {"iata_code": "RAK", "name": "Marrakech Menara Airport", "city_name": "Marrakech"},
        ],
    },
    {
        "country_code": "JP",
        "name": "Japan",
        "native_name": "日本",
        "flag": "🇯🇵",
        "aliases": ["japan", "tokyo", "jp"],
        "primary_airports": ["HND", "NRT"],
        "airports": [
            {"iata_code": "HND", "name": "Tokyo Haneda Airport", "city_name": "Tokyo"},
            {"iata_code": "NRT", "name": "Tokyo Narita Airport", "city_name": "Tokyo"},
            {"iata_code": "KIX", "name": "Kansai International Airport", "city_name": "Osaka"},
        ],
    },
    {
        "country_code": "TH",
        "name": "Thailand",
        "native_name": "ประเทศไทย",
        "flag": "🇹🇭",
        "aliases": ["thailand", "bangkok", "phuket", "th"],
        "primary_airports": ["BKK", "HKT"],
        "airports": [
            {"iata_code": "BKK", "name": "Suvarnabhumi Airport", "city_name": "Bangkok"},
            {"iata_code": "HKT", "name": "Phuket International Airport", "city_name": "Phuket"},
        ],
    },
]

# Quick lookup index by country code and alias
COUNTRY_BY_CODE: dict[str, dict[str, Any]] = {c["country_code"]: c for c in COUNTRIES_DATA}
COUNTRY_BY_ALIAS: dict[str, dict[str, Any]] = {}
for country in COUNTRIES_DATA:
    for alias in country["aliases"]:
        COUNTRY_BY_ALIAS[alias.lower()] = country


def find_country(identifier: str) -> dict[str, Any] | None:
    """
    Look up a country by code ('DE', 'COUNTRY:DE'), name ('Germany'), or alias ('deutschland', 'england').
    """
    if not identifier:
        return None

    clean = identifier.strip()

    # Explicit prefix
    if clean.upper().startswith("COUNTRY:"):
        code = clean.upper().replace("COUNTRY:", "").strip()
        return COUNTRY_BY_CODE.get(code)

    # 2-letter ISO country code (e.g. 'DE', 'GB', 'TR', 'US')
    if len(clean) == 2 and clean.upper() in COUNTRY_BY_CODE:
        return COUNTRY_BY_CODE[clean.upper()]

    lower = clean.lower()

    # Exact alias match (e.g. 'germany', 'deutschland', 'england', 'united kingdom')
    if lower in COUNTRY_BY_ALIAS:
        return COUNTRY_BY_ALIAS[lower]

    # Exact country name match
    for c in COUNTRIES_DATA:
        if lower == c["name"].lower() or lower == c["native_name"].lower():
            return c

    # Prefix match on longer aliases (minimum 4 chars typed) e.g. "germ" -> "germany", "engl" -> "england"
    if len(lower) >= 4:
        for alias, c in COUNTRY_BY_ALIAS.items():
            if len(alias) >= 4 and alias.startswith(lower):
                return c
        for c in COUNTRIES_DATA:
            if lower in c["name"].lower() or lower in c["native_name"].lower():
                return c

    return None


def search_country_suggestions(query: str) -> list[dict[str, Any]]:
    """
    Search for country-level suggestions matching a query string.
    Returns suggestion objects with type='country' for the autocomplete dropdown.
    """
    if not query or len(query.strip()) < 2:
        return []

    q = query.strip().lower()
    matched_countries = []
    seen_codes = set()

    for c in COUNTRIES_DATA:
        code = c["country_code"]
        if code in seen_codes:
            continue

        matches = False
        if q == code.lower():
            matches = True
        elif q == c["name"].lower() or q == c["native_name"].lower():
            matches = True
        elif len(q) >= 4 and (q in c["name"].lower() or q in c["native_name"].lower()):
            matches = True
        else:
            for alias in c["aliases"]:
                if q == alias or (len(q) >= 4 and q in alias):
                    matches = True
                    break

        if matches:
            seen_codes.add(code)
            airports_summary = ", ".join(a["iata_code"] for a in c["airports"][:4])
            matched_countries.append({
                "iata_code": f"COUNTRY:{code}",
                "name": f"All Major Airports ({airports_summary})",
                "city_name": f"{c['name']} (All Airports)",
                "country": c["name"],
                "country_code": code,
                "type": "country",
                "flag": c["flag"],
            })

    return matched_countries


def resolve_location_airports(location_str: str) -> tuple[list[str], str, bool]:
    """
    Resolve a user input (IATA code, country name, country code, or city)
    into a list of operational IATA codes for Duffel search slices.

    Returns:
        tuple (airports_list, display_name, is_country)
    """
    if not location_str:
        return (["LHR"], "London", False)

    clean = location_str.strip()

    # 1. Explicit country prefix or 2-letter ISO code
    if clean.upper().startswith("COUNTRY:") or (len(clean) == 2 and clean.upper() in COUNTRY_BY_CODE):
        country = find_country(clean)
        if country:
            return (country["primary_airports"], f"{country['name']} (All Airports)", True)

    # 2. Check 3-letter IATA codes first before fuzzy country matching
    if len(clean) == 3 and clean.isalpha():
        upper = clean.upper()
        # Find if this IATA belongs to our airport list to get a nice display name
        for c in COUNTRIES_DATA:
            for a in c["airports"]:
                if a["iata_code"].upper() == upper:
                    return ([upper], f"{a['city_name']} ({upper})", False)
        return ([upper], upper, False)

    # 3. Check if clean matches any known city in our directory first
    for c in COUNTRIES_DATA:
        for a in c["airports"]:
            if a["city_name"].lower() == clean.lower():
                return ([a["iata_code"]], a["city_name"], False)

    # 4. Check country by name or alias
    country = find_country(clean)
    if country:
        return (country["primary_airports"], f"{country['name']} (All Airports)", True)

    # 5. Check airport name match
    for c in COUNTRIES_DATA:
        for a in c["airports"]:
            if a["name"].lower() == clean.lower():
                return ([a["iata_code"]], a["city_name"], False)

    # 6. Fallback: treat as 3-letter code
    return ([clean.upper()[:3]], clean.upper()[:3], False)
