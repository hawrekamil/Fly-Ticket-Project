# Frontend Implementation Details (React SPA)

The BookingSoft frontend has been fully decoupled into a **React.js Single Page Application (SPA)** using Vite.

## Architecture

- **Framework**: React.js (Bootstrapped with Vite for instant server start and optimal HMR).
- **Styling**: Tailwind CSS, configured with a custom brand palette (Indigo/Pink gradients) and a premium "Glassmorphism" utility class (`.glass`).
- **Routing**: `react-router-dom` v7.
- **API Client**: Axios (`src/api.js`) configured to hit the Django backend at `http://localhost:8000/api/v1/` and automatically attach JWT tokens to the `Authorization` header.
- **State Management**: React Context (`src/context/AuthContext.jsx`) for global authentication state.

## Core Pages

1. **`Home.jsx`**: The flight search interface. Features a hero section with gradient backgrounds, airport & city autocomplete (`AirportAutocomplete.jsx`), real-time flight filters (price range slider, airline selector, time-of-day buttons: Morning/Afternoon/Evening/Night, stops filter, and sorting: Cheapest/Fastest/Earliest), and expandable flight itineraries. All flight times are accurately preserved in local airport time without browser timezone distortion.
2. **`AirportAutocomplete.jsx`**: Real-time city & airport search dropdown. Connects to the Duffel places suggestions API (`/api/v1/flights/airports/suggestions/`) with instant local fallbacks, allowing customers to type full city names (e.g. "Frankfurt", "London", "Dubai") with automatic IATA code resolution.
3. **`Login.jsx` & `Register.jsx`**: Authentication forms that interact with the Django JWT endpoints. Tokens are stored in `localStorage`.
4. **`Checkout.jsx`**: The payment portal. Integrates `@stripe/react-stripe-js` for immediate credit card settlements, and offers an alternative Cash Hold workflow.
5. **`MyOrders.jsx`**: A protected route showing the customer's active and past bookings, displaying the order reference, status, and cash hold expiration dates.
6. **`AgentDashboard.jsx`**: An admin-only route that fetches all system-wide pending cash holds, allowing agents to confirm payments with a single click.

## Running the Application

Ensure you are in the `frontend/` directory.

```powershell
# Install dependencies (only needed once)
npm install

# Start the development server
npm run dev
```

The application will be accessible at `http://localhost:5173`.
