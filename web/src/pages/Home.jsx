import React from 'react';
import { ArrowRight, Scale, Clock, ShieldAlert, Cpu, Award } from 'lucide-react';
import PipelineDiagram from '../components/PipelineDiagram';

export default function Home({ setActivePage }) {
  return (
    <div className="space-y-16 py-8">
      {/* Hero Section */}
      <section className="text-center max-w-4xl mx-auto space-y-6">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-navy-900/5 dark:bg-gold-500/10 border border-navy-900/10 dark:border-gold-500/20 text-xs font-semibold text-navy-800 dark:text-gold-400">
          <Scale className="w-3.5 h-3.5" />
          <span>Empirical Judicial Analytics · Indian Lower Courts</span>
        </div>

        <h1 className="serif-heading text-4xl sm:text-5xl lg:text-6xl font-extrabold text-navy-950 dark:text-white tracking-tight leading-[1.15]">
          Predicting Criminal Case Delays & Backlog Durations with <span className="text-gold-600 dark:text-gold-400">Explainable AI</span>
        </h1>

        <p className="text-lg sm:text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
          A production replication of the state-of-the-art two-stage hybrid machine learning pipeline that forecasts court resolution timelines at the exact moment of filing.
        </p>

        <div className="flex flex-wrap justify-center gap-4 pt-4">
          <button
            onClick={() => setActivePage('analyze')}
            className="px-6 py-3 rounded-xl bg-navy-900 hover:bg-navy-800 dark:bg-gold-500 dark:hover:bg-gold-400 text-white dark:text-navy-950 font-bold shadow-lg shadow-navy-900/10 dark:shadow-gold-500/20 flex items-center space-x-2 transition-all hover:scale-[1.02]"
          >
            <span>Upload Case File for Analysis</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => setActivePage('results')}
            className="px-6 py-3 rounded-xl bg-white hover:bg-slate-50 dark:bg-navy-900 dark:hover:bg-navy-800 text-navy-900 dark:text-white border border-slate-200 dark:border-navy-700 font-semibold shadow-sm transition-all"
          >
            <span>View Benchmark Results</span>
          </button>
        </div>
      </section>

      {/* Quick Metrics Bar */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-5xl mx-auto">
        <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 text-center shadow-sm">
          <div className="text-3xl font-extrabold text-navy-950 dark:text-gold-400">~80.0%</div>
          <div className="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold mt-1">Classification Accuracy</div>
        </div>
        <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 text-center shadow-sm">
          <div className="text-3xl font-extrabold text-navy-950 dark:text-gold-400">84.1%</div>
          <div className="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold mt-1">F1 Delay Score</div>
        </div>
        <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 text-center shadow-sm">
          <div className="text-3xl font-extrabold text-navy-950 dark:text-gold-400">4.90 mo</div>
          <div className="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold mt-1">On-Time RMSE</div>
        </div>
        <div className="p-5 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 text-center shadow-sm">
          <div className="text-3xl font-extrabold text-navy-950 dark:text-gold-400">18.2%</div>
          <div className="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold mt-1">Error Reduction vs Baseline</div>
        </div>
      </section>

      {/* Interactive Architecture Section */}
      <section className="max-w-6xl mx-auto">
        <PipelineDiagram />
      </section>

      {/* Key Innovation Highlights */}
      <section className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 flex items-center justify-center">
            <Clock className="w-5 h-5" />
          </div>
          <h4 className="serif-heading font-bold text-lg text-navy-950 dark:text-white">Strict Leakage Prevention</h4>
          <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
            Eliminates all future information available only after trial initiation (judge transfers, hearings, interim orders), ensuring true filing-time utility.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-amber-50 dark:bg-amber-950 text-amber-600 dark:text-amber-400 flex items-center justify-center">
            <Cpu className="w-5 h-5" />
          </div>
          <h4 className="serif-heading font-bold text-lg text-navy-950 dark:text-white">Consensus Thresholding</h4>
          <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
            Routes ambiguous cases to a robust monolithic safety net when classifier confidence is below 85%, achieving superior global stability.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <h4 className="serif-heading font-bold text-lg text-navy-950 dark:text-white">Statistical Fairness Auditing</h4>
          <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
            Audited using demographic reassignment and 10% gender flips with two-sample t-tests to ensure predictions are free of algorithmic disparity.
          </p>
        </div>
      </section>
    </div>
  );
}

