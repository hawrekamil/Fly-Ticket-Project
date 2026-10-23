import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Checkout from './pages/Checkout';
import MyOrders from './pages/MyOrders';
import AgentDashboard from './pages/AgentDashboard';
import Airlines from './pages/Airlines';

const PrivateRoute = ({ children, agentOnly = false }) => {
  const { user, loading } = useAuth();

  if (loading) return <div className="p-12 text-center">Loading...</div>;
  if (!user) return <Navigate to="/login" />;
  if (agentOnly && !user.is_agent && !user.is_admin_role) return <Navigate to="/" />;
  
  return children;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen flex flex-col bg-dot-grid relative overflow-x-hidden">
          {/* Dot Grid Canvas & Ambient Light */}
          <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
            <div className="absolute inset-0 bg-dot-grid"></div>
            <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-300/30 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse"></div>
            <div className="absolute top-0 right-1/4 w-96 h-96 bg-pink-300/30 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse" style={{ animationDelay: '2s' }}></div>
            <div className="absolute -bottom-8 left-1/3 w-96 h-96 bg-purple-300/30 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse" style={{ animationDelay: '4s' }}></div>
          </div>

          <Navbar />
          
          <main className="flex-grow relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-page-enter">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/airlines" element={<Airlines />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              
              <Route path="/checkout/:offerId" element={
                <PrivateRoute>
                  <Checkout />
                </PrivateRoute>
              } />
              
              <Route path="/my-orders" element={
                <PrivateRoute>
                  <MyOrders />
                </PrivateRoute>
              } />

              <Route path="/agent-dashboard" element={
                <PrivateRoute agentOnly={true}>
                  <AgentDashboard />
                </PrivateRoute>
              } />
            </Routes>
          </main>

          <footer className="relative z-10 glass mt-auto py-8 border-t border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-slate-500">
              &copy; {new Date().getFullYear()} BookingSoft SPA. Engineered for high-performance travel.
            </div>
          </footer>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
