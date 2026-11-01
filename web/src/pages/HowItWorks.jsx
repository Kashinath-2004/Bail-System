import React from 'react';
import { Database, Filter, GitBranch, Cpu, ShieldCheck, ArrowRight } from 'lucide-react';

export default function HowItWorks() {
  const steps = [
    {
      num: "01",
      icon: Database,
      title: "Data Sourcing & e-Courts Preprocessing",
      subtitle: "e-Courts Subordinate Judiciary Records (2010–2018)",
      desc: "Historical records from India's district and lower judiciary are parsed across 10 years of criminal filings. Each case is mapped to standardized Indian Penal Code (IPC) acts, judicial positions, and district venues."
    },
    {
      num: "02",
      icon: Filter,
      title: "Strict Leakage Elimination Protocol",
      subtitle: "Filing-Time Only Information",
      desc: "A common flaw in judicial ML is data leakage (using judge transfer dates or intermediate hearing records that occur after filing). The pipeline strictly strips all post-filing events, ensuring models evaluate only what is known on day zero."
    },
    {
      num: "03",
      icon: ShieldCheck,
      title: "Stage 1: Delay Classification (Model 1c DRF)",
      subtitle: "Distributed Random Forest Classifier",
      desc: "Rather than predicting duration directly, the case first enters a high-capacity DRF classifier. The model achieves ~80% accuracy and 84.1% F1 in determining whether a case will resolve on-time (<= 24 months) or face multi-year delay."
    },
    {
      num: "04",
      icon: GitBranch,
      title: "Consensus Routing Mechanism",
      subtitle: "Confidence Thresholding at p >= 0.85",
      desc: "To prevent prediction error on borderline cases, a consensus rule is enforced. High-confidence on-time cases route to Specialist 2a; high-confidence delayed cases route to Specialist 2b; ambiguous cases fall back to a monolithic baseline."
    },
    {
      num: "05",
      icon: Cpu,
      title: "Stage 2: Specialist Duration Regression",
      subtitle: "Targeted Regressors for Expedited vs Delayed Cases",
      desc: "Because the distribution of court timelines is highly bimodal, specialist regressors achieve drastically lower error. Model 2a achieves ~4.90 months RMSE on on-time cases, cutting monolithic error by over 60%."
    }
  ];

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 space-y-12">
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <span className="text-xs font-bold uppercase tracking-wider text-gold-600 dark:text-gold-400 bg-gold-50 dark:bg-gold-500/10 px-3 py-1 rounded-full border border-gold-200 dark:border-gold-500/20">
          Methodological Framework
        </span>
        <h2 className="serif-heading text-3xl sm:text-4xl font-bold text-navy-950 dark:text-white">
          How the Two-Stage Hybrid Engine Operates
        </h2>
        <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400">
          A systematic breakdown of the research methodology replicating the paper's empirical pipeline.
        </p>
      </div>

      <div className="space-y-6">
        {steps.map((s, idx) => {
          const Icon = s.icon;
          return (
            <div 
              key={idx}
              className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 shadow-sm flex flex-col md:flex-row gap-6 items-start transition-all hover:border-slate-300 dark:hover:border-navy-700"
            >
              <div className="flex items-center space-x-4 md:flex-col md:space-x-0 md:space-y-2 flex-shrink-0">
                <span className="serif-heading text-2xl font-black text-gold-600 dark:text-gold-400">
                  {s.num}
                </span>
                <div className="w-12 h-12 rounded-2xl bg-navy-800 text-gold-400 flex items-center justify-center">
                  <Icon className="w-6 h-6" />
                </div>
              </div>

              <div className="space-y-2 flex-grow">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                  {s.subtitle}
                </div>
                <h3 className="serif-heading text-xl font-bold text-navy-950 dark:text-white">
                  {s.title}
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed pt-1">
                  {s.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

