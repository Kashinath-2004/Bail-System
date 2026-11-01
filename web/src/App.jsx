import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import CaseAnalysis from './pages/CaseAnalysis';
import Predict from './pages/Predict';
import HowItWorks from './pages/HowItWorks';
import Results from './pages/Results';
import Robustness from './pages/Robustness';

export default function App() {
  const [activePage, setActivePage] = useState('analyze');
  const [darkMode, setDarkMode] = useState(() => {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 dark:bg-navy-950 transition-colors">
      <Navbar 
        activePage={activePage} 
        setActivePage={setActivePage} 
        darkMode={darkMode} 
        setDarkMode={setDarkMode} 
      />

      <main className="flex-grow">
        {activePage === 'home' && <Home setActivePage={setActivePage} />}
        {activePage === 'analyze' && <CaseAnalysis />}
        {activePage === 'predict' && <Predict />}
        {activePage === 'how-it-works' && <HowItWorks />}
        {activePage === 'results' && <Results />}
        {activePage === 'robustness' && <Robustness />}
      </main>

      <Footer />
    </div>
  );
}

