import { useEffect } from 'react'
import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom'
import ChatWidget from './components/ChatWidget'
import Footer from './components/Footer'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import { LanguageProvider } from './context/LanguageContext'
import Admin from './pages/Admin'
import Canteen from './pages/Canteen'
import Transport from './pages/Transport'
import Chat from './pages/Chat'
import Compare from './pages/Compare'
import Dashboard from './pages/Dashboard'
import EligibilityChecker from './pages/EligibilityChecker'
import FeeCalculator from './pages/FeeCalculator'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Profile from './pages/Profile'
import ProgramDetail from './pages/ProgramDetail'
import Programs from './pages/Programs'
import Register from './pages/Register'

// Every page change starts at the top — without this, opening a program
// from the long Programs grid landed halfway down the detail page.
function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo({ top: 0, left: 0, behavior: 'instant' }) }, [pathname])
  return null
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <LanguageProvider>
        <AuthProvider>
          <div className="flex min-h-screen flex-col">
            <Navbar />
            <main className="flex-1">
              <Routes>
                <Route path="/" element={<Landing />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/programs" element={<Programs />} />
                <Route path="/programs/:id" element={<ProgramDetail />} />
                <Route path="/compare" element={<Compare />} />
                <Route path="/fee-calculator" element={<FeeCalculator />} />
                <Route path="/eligibility" element={<EligibilityChecker />} />
                <Route path="/chat" element={<Chat />} />
                <Route path="/canteen" element={<Canteen />} />
                <Route path="/transport" element={<Transport />} />
                <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
                <Route path="/admin" element={<ProtectedRoute adminOnly><Admin /></ProtectedRoute>} />
                <Route path="*" element={<Landing />} />
              </Routes>
            </main>
            <Footer />
            <ChatWidget />
          </div>
        </AuthProvider>
      </LanguageProvider>
    </BrowserRouter>
  )
}
