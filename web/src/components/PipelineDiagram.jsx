import React, { useState } from 'react';
import { ArrowRight, CheckCircle2, AlertTriangle, ShieldCheck, Database, GitBranch } from 'lucide-react';

export default function PipelineDiagram() {
  const [activeStage, setActiveStage] = useState('router');

  const stageDetails = {
    input: {
      title: "Stage 0: Leak-Free Case Filing Input",
      desc: "Raw case attributes captured strictly at time of filing. To prevent data leakage, all post-filing events (judge transfers, subsequent hearings, decision dates) are strictly removed.",
      features: "Jurisdiction (State, District, Court), IPC Acts & Sections, Bailable status, Judge tenure at filing."
    },
    classifier: {
      title: "Stage 1: Model 1c Delay Classifier (DRF)",
      desc: "Distributed Random Forest model trained on millions of historical e-Courts filings. Outputs calibrated probability p(on-time) for whether the case will be disposed within 24 months.",
      features: "Benchmark: ~80.0% Accuracy, ~84.1% F1-Score. Grid search over ntrees=[50,70], max_depth=[20,30]."
    },
    router: {
      title: "Consensus Routing Mechanism (Threshold = 0.85)",
      desc: "Directs each case to the optimal regression specialist. If classifier confidence exceeds 85%, routes to the corresponding specialist. If there is model disagreement or ambiguity, falls back to the monolithic baseline.",
      features: "Prevents high-variance edge cases from skewing specialized duration models."
    },
    regressor2a: {
      title: "Stage 2a: Specialist Regressor (On-Time Cases)",
      desc: "AutoML regressor optimized specifically on cases disposed within 24 months. Specializes in granular month-by-month duration forecasts for expedited cases.",
      features: "Paper Benchmark RMSE: ~4.90 months (vs 14.85 mo monolithic baseline error)."
    },
    regressor2b: {
      title: "Stage 2b: Specialist Regressor (Delayed Cases)",
      desc: "AutoML regressor optimized specifically on multi-year delayed cases (> 24 months). Accurately models long-tail backlogs and complex procedural delays.",
      features: "Paper Benchmark RMSE: ~13.79 months."
    },
    baseline: {
      title: "Monolithic Baseline (Fallback)",
      desc: "Global regressor trained indiscriminately on all case durations. Acts as the safety fallback when classifier certainty is below 85%.",
      features: "Ablation benchmark showing that splitting into specialists reduces system-wide RMSE by over 18%."
    }
  };

  const curr = stageDetails[activeStage];

  return (
    <div className="bg-white dark:bg-navy-900 rounded-3xl border border-slate-200 dark:border-navy-800 p-6 md:p-8 shadow-sm transition-colors">
      <div className="text-center max-w-2xl mx-auto mb-8">
        <span className="text-xs font-bold uppercase tracking-wider text-gold-600 dark:text-gold-400 bg-gold-50 dark:bg-gold-500/10 px-3 py-1 rounded-full border border-gold-200 dark:border-gold-500/20">
          Hybrid Architecture
        </span>
        <h3 className="serif-heading text-xl md:text-2xl font-bold text-navy-950 dark:text-white mt-3">
          Two-Stage Intelligent Decision Routing
        </h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
          Click on any node below to inspect its operational role, data inputs, and paper benchmarks.
        </p>
      </div>

      {/* Visual Workflow */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 items-center">
        {/* Node 1: Input */}
        <div 
          onClick={() => setActiveStage('input')}
          className={`cursor-pointer p-5 rounded-2xl border transition-all text-center ${
            activeStage === 'input' 
              ? 'border-gold-500 bg-gold-50/50 dark:bg-gold-500/10 shadow-md ring-2 ring-gold-500/20' 
              : 'border-slate-200 dark:border-navy-800 bg-slate-50 dark:bg-navy-950 hover:border-slate-300'
          }`}
        >
          <div className="w-10 h-10 rounded-xl bg-navy-800 text-gold-400 flex items-center justify-center mx-auto mb-3">
            <Database className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-sm text-navy-900 dark:text-white">Case Filing</h4>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Leak-free features</p>
        </div>

        {/* Node 2: Stage 1 Classifier */}
        <div 
          onClick={() => setActiveStage('classifier')}
          className={`cursor-pointer p-5 rounded-2xl border transition-all text-center ${
            activeStage === 'classifier' 
              ? 'border-gold-500 bg-gold-50/50 dark:bg-gold-500/10 shadow-md ring-2 ring-gold-500/20' 
              : 'border-slate-200 dark:border-navy-800 bg-slate-50 dark:bg-navy-950 hover:border-slate-300'
          }`}
        >
          <div className="w-10 h-10 rounded-xl bg-blue-700 text-white flex items-center justify-center mx-auto mb-3">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-sm text-navy-900 dark:text-white">Stage 1 Classifier</h4>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Model 1c DRF (~80% Acc)</p>
        </div>

        {/* Node 3: Router */}
        <div 
          onClick={() => setActiveStage('router')}
          className={`cursor-pointer p-5 rounded-2xl border transition-all text-center ${
            activeStage === 'router' 
              ? 'border-gold-500 bg-gold-50/50 dark:bg-gold-500/10 shadow-md ring-2 ring-gold-500/20' 
              : 'border-slate-200 dark:border-navy-800 bg-slate-50 dark:bg-navy-950 hover:border-slate-300'
          }`}
        >
          <div className="w-10 h-10 rounded-xl bg-amber-600 text-white flex items-center justify-center mx-auto mb-3">
            <GitBranch className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-sm text-navy-900 dark:text-white">Consensus Router</h4>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Threshold p ≥ 0.85</p>
        </div>

        {/* Node 4: Specialists */}
        <div className="space-y-2">
          <div 
            onClick={() => setActiveStage('regressor2a')}
            className={`cursor-pointer p-3 rounded-xl border transition-all text-left ${
              activeStage === 'regressor2a' 
                ? 'border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/30' 
                : 'border-slate-200 dark:border-navy-800 bg-slate-50 dark:bg-navy-950'
            }`}
          >
            <div className="text-xs font-bold text-emerald-700 dark:text-emerald-400">Model 2a (On-Time)</div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400">Target RMSE: ~4.90 mo</div>
          </div>
          <div 
            onClick={() => setActiveStage('regressor2b')}
            className={`cursor-pointer p-3 rounded-xl border transition-all text-left ${
              activeStage === 'regressor2b' 
                ? 'border-rose-500 bg-rose-50/50 dark:bg-rose-950/30' 
                : 'border-slate-200 dark:border-navy-800 bg-slate-50 dark:bg-navy-950'
            }`}
          >
            <div className="text-xs font-bold text-rose-700 dark:text-rose-400">Model 2b (Delayed)</div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400">Target RMSE: ~13.79 mo</div>
          </div>
          <div 
            onClick={() => setActiveStage('baseline')}
            className={`cursor-pointer p-2.5 rounded-xl border transition-all text-left ${
              activeStage === 'baseline' 
                ? 'border-slate-500 bg-slate-100 dark:bg-navy-800' 
                : 'border-slate-200 dark:border-navy-800/60 bg-slate-50/60 dark:bg-navy-950/60'
            }`}
          >
            <div className="text-[11px] font-bold text-slate-600 dark:text-slate-300">Baseline Fallback</div>
            <div className="text-[10px] text-slate-400">Low-confidence safety net</div>
          </div>
        </div>
      </div>

      {/* Active Stage Detail Panel */}
      <div className="mt-8 p-6 rounded-2xl bg-slate-50 dark:bg-navy-950/80 border border-slate-200 dark:border-navy-800">
        <h4 className="serif-heading font-bold text-base text-navy-950 dark:text-white flex items-center space-x-2">
          <span>{curr.title}</span>
        </h4>
        <p className="text-sm text-slate-600 dark:text-slate-300 mt-2 leading-relaxed">
          {curr.desc}
        </p>
        <div className="mt-4 pt-3 border-t border-slate-200/80 dark:border-navy-800 text-xs font-medium text-slate-500 dark:text-slate-400">
          <strong className="text-navy-900 dark:text-slate-200 font-semibold">Technical Highlights:</strong> {curr.features}
        </div>
      </div>
    </div>
  );
}
