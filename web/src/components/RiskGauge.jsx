import React from 'react';

export default function RiskGauge({ riskPct = 50, predictedClass = 'delayed' }) {
  const normalized = Math.min(100, Math.max(0, riskPct));
  const strokeDashoffset = 440 - (440 * (normalized / 100) * 0.75); // 270 degree arc

  let riskColor = 'text-emerald-500';
  let badgeBg = 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800';
  let riskLevel = 'Low Delay Risk';

  if (normalized >= 70) {
    riskColor = 'text-rose-500';
    badgeBg = 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800';
    riskLevel = 'High Delay Risk';
  } else if (normalized >= 40) {
    riskColor = 'text-amber-500';
    badgeBg = 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800';
    riskLevel = 'Moderate Delay Risk';
  }

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-navy-800 shadow-sm transition-colors">
      <div className="relative w-44 h-44 flex items-center justify-center">
        <svg className="w-full h-full transform -rotate-135" viewBox="0 0 160 160">
          {/* Background circle arc */}
          <circle
            cx="80"
            cy="80"
            r="70"
            stroke="currentColor"
            strokeWidth="12"
            fill="transparent"
            strokeDasharray="440"
            strokeDashoffset="110"
            className="text-slate-100 dark:text-navy-800"
            strokeLinecap="round"
          />
          {/* Active progress arc */}
          <circle
            cx="80"
            cy="80"
            r="70"
            stroke="currentColor"
            strokeWidth="12"
            fill="transparent"
            strokeDasharray="440"
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className={`${riskColor} transition-all duration-1000 ease-out`}
          />
        </svg>

        <div className="absolute flex flex-col items-center">
          <span className="text-3xl font-extrabold text-navy-950 dark:text-white tracking-tight">
            {normalized.toFixed(1)}%
          </span>
          <span className="text-[11px] uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold mt-0.5">
            Delay Risk
          </span>
        </div>
      </div>

      <div className="mt-4 flex flex-col items-center space-y-1.5">
        <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${badgeBg}`}>
          {predictedClass === 'ontime' ? 'Predicted: On-Time (<= 24 mo)' : 'Predicted: Delayed (> 24 mo)'}
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
          {riskLevel}
        </p>
      </div>
    </div>
  );
}
