import React from 'react';
import { BookOpen, ExternalLink, Shield } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 dark:border-navy-800 bg-white dark:bg-navy-950 py-8 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
        <div className="text-center md:text-left">
          <p className="text-sm font-semibold text-navy-900 dark:text-slate-200">
            Justice AI · Hybrid Case Pendency & Duration Prediction System
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Replication of research published in <em>Springer / Journal of Big Data</em> (2025). Indian e-Courts Subordinate Judiciary.
          </p>
        </div>
        
        <div className="flex items-center space-x-6 text-xs text-slate-500 dark:text-slate-400">
          <a 
            href="https://doi.org/10.1186/s40537-025-01340-1" 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center space-x-1 hover:text-gold-600 dark:hover:text-gold-400 transition-colors"
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Paper DOI</span>
            <ExternalLink className="w-3 h-3 ml-0.5" />
          </a>
          <a 
            href="https://doi.org/10.5281/zenodo.17421604" 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center space-x-1 hover:text-gold-600 dark:hover:text-gold-400 transition-colors"
          >
            <Shield className="w-3.5 h-3.5" />
            <span>Zenodo Dataset</span>
            <ExternalLink className="w-3 h-3 ml-0.5" />
          </a>
        </div>
      </div>
    </footer>
  );
}

