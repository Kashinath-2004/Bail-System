import React, { useState, useEffect } from 'react';

export default function CaseAnalysis() {
  const [step, setStep] = useState(1); // 1: Ingest, 2: Review, 3: Results
  const [file, setFile] = useState(null);
  const [caseText, setCaseText] = useState('');
  const [redactPii, setRedactPii] = useState(true);
  const [loading, setLoading] = useState(false);
  const [sampleCases, setSampleCases] = useState([]);
  const [reviewData, setReviewData] = useState({
    case_title: 'State vs Accused',
    case_number: 'FIR 102/2023',
    filing_year: 2024,
    state: 'Maharashtra',
    state_code: 1,
    district: 'Pune',
    dist_code: 1,
    court_name: 'Pune District Court',
    court_no: 1,
    act: 'The Indian Penal Code',
    sections: ['379'],
    case_type: 'Criminal Case',
    judge_position: 'Civil Judge Junior Division',
    judge_tenure_months: 14.0,
    accused_count: 1,
    custody_status: 'Not Arrested',
    case_summary: '',
    provenance: {},
  });
  const [resultsData, setResultsData] = useState(null);

  useEffect(() => {
    fetch('/case/sample')
      .then(res => res.json())
      .then(data => setSampleCases(data))
      .catch(err => console.warn('Sample fetch err:', err));
  }, []);

  const handleFileDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const loadSample = (idx) => {
    if (sampleCases[idx]) {
      setReviewData(sampleCases[idx]);
      setStep(2);
    }
  };

  const handleExtract = async () => {
    setLoading(true);
    try {
      let respData = null;
      if (file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('redact_pii', redactPii);
        const res = await fetch('/case/extract', { method: 'POST', body: formData });
        if (!res.ok) throw new Error('File extraction failed');
        respData = await res.json();
      } else if (caseText.trim()) {
        const res = await fetch('/case/extract-text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ raw_text: caseText, redact_pii: redactPii })
        });
        if (!res.ok) throw new Error('Text extraction failed');
        respData = await res.json();
      } else {
        alert('Please upload a file or paste case text.');
        setLoading(false);
        return;
      }

      setReviewData(respData);
      setStep(2);
    } catch (err) {
      alert('Extraction failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const res = await fetch('/case/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reviewData)
      });
      if (!res.ok) throw new Error('Analysis failed');
      const data = await res.json();
      setResultsData(data);
      setStep(3);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      alert('Analysis error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-navy-900/5 dark:bg-gold-500/10 border border-navy-900/10 dark:border-gold-500/20 text-xs font-semibold text-navy-800 dark:text-gold-400">
          <span>⚖️ Full Case Document Analysis · Indian Subordinate Courts</span>
        </div>
        <h1 className="serif-heading text-3xl sm:text-4xl font-extrabold text-navy-950 dark:text-white tracking-tight">
          Upload a Case File — Get Full AI & Legal Analysis
        </h1>
        <p className="text-slate-600 dark:text-slate-300 text-sm sm:text-base leading-relaxed">
          Upload an FIR, chargesheet, or petition. Get two-stage hybrid ML delay predictions, similar cases from DDL e-Courts records, and statutory bailability advisory.
        </p>
      </div>

      {/* Quick Sample Selector */}
      {step === 1 && (
        <div className="max-w-4xl mx-auto p-4 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <span>⚡</span> Quick Sample Cases:
          </span>
          <div className="flex flex-wrap gap-2">
            <button onClick={() => loadSample(0)} className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 hover:bg-emerald-100 transition">
              1. Simple Theft (Bailable)
            </button>
            <button onClick={() => loadSample(1)} className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-50 dark:bg-rose-950/50 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 hover:bg-rose-100 transition">
              2. Murder Attempt (Non-Bailable)
            </button>
            <button onClick={() => loadSample(2)} className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 hover:bg-amber-100 transition">
              3. Cheating (New BNS 2024)
            </button>
          </div>
        </div>
      )}

      {/* STEP 1: INGESTION */}
      {step === 1 && (
        <div className="max-w-4xl mx-auto bg-white dark:bg-navy-900 rounded-3xl border border-slate-200 dark:border-navy-800 p-6 sm:p-8 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-navy-800 pb-4">
            <div>
              <h3 className="serif-heading text-xl font-bold text-navy-950 dark:text-white">Step 1: Provide Case Document or Text</h3>
              <p className="text-xs text-slate-500 mt-0.5">Processed strictly in-memory; never stored on disk or shared with external parties.</p>
            </div>
            <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-slate-100 dark:bg-navy-800 text-slate-600 dark:text-slate-300">
              🔒 In-Memory Privacy
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">Option A: Upload Document (PDF, DOCX, TXT)</label>
              <div 
                onDragOver={(e) => e.preventDefault()} 
                onDrop={handleFileDrop}
                className="border-2 border-dashed border-slate-300 dark:border-navy-700 hover:border-gold-500 rounded-2xl p-6 text-center cursor-pointer transition bg-slate-50 dark:bg-navy-950 flex flex-col items-center justify-center min-h-[160px]"
                onClick={() => document.getElementById('react-file-input').click()}
              >
                <input 
                  type="file" 
                  id="react-file-input" 
                  className="hidden" 
                  accept=".pdf,.docx,.txt" 
                  onChange={(e) => e.target.files.length > 0 && setFile(e.target.files[0])} 
                />
                <div className="text-3xl mb-2">📄</div>
                <p className="text-xs font-semibold text-navy-950 dark:text-white">
                  {file ? `Selected: ${file.name}` : 'Click or drag & drop document here'}
                </p>
                <p className="text-[11px] text-slate-400 mt-1">Supports PDF, Word DOCX, TXT</p>
              </div>
            </div>

            <div className="space-y-3">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">Option B: Or Paste Case Text / FIR Details</label>
              <textarea 
                rows="6" 
                value={caseText}
                onChange={(e) => setCaseText(e.target.value)}
                className="w-full text-xs rounded-2xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 p-3.5 dark:text-white focus:ring-2 focus:ring-gold-500 font-mono" 
                placeholder="Paste FIR or case text here..."
              />
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 flex items-center justify-between">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input 
                type="checkbox" 
                checked={redactPii} 
                onChange={(e) => setRedactPii(e.target.checked)} 
                className="w-4 h-4 rounded text-gold-600 focus:ring-gold-500" 
              />
              <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                🔒 <strong>Redact Personal Identifiers in Memory:</strong> Masks names, phone numbers, and Aadhaar before processing.
              </span>
            </label>
          </div>

          <div className="flex justify-end pt-2">
            <button 
              onClick={handleExtract} 
              disabled={loading}
              className="px-6 py-3 rounded-xl bg-navy-900 hover:bg-navy-800 dark:bg-gold-500 dark:hover:bg-gold-400 text-white dark:text-navy-950 font-bold shadow-md transition flex items-center gap-2"
            >
              <span>{loading ? 'Extracting Details... ⏳' : 'Extract Case Details →'}</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: REVIEW & CONFIRM */}
      {step === 2 && (
        <div className="max-w-4xl mx-auto bg-white dark:bg-navy-900 rounded-3xl border border-slate-200 dark:border-navy-800 p-6 sm:p-8 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-navy-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="serif-heading text-xl font-bold text-navy-950 dark:text-white">Step 2: Review & Confirm Extracted Parameters</h3>
                <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">Human in the Loop</span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">Please check and correct any field before running the predictive model.</p>
            </div>
            <button onClick={() => setStep(1)} className="text-xs text-slate-500 hover:text-navy-950 dark:hover:text-white underline">← Re-upload</button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Case Title / Parties</label>
              <input 
                type="text" 
                value={reviewData.case_title || ''} 
                onChange={(e) => setReviewData({ ...reviewData, case_title: e.target.value })}
                className="w-full text-xs rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 px-3 py-2.5 dark:text-white" 
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Case / FIR Number</label>
              <input 
                type="text" 
                value={reviewData.case_number || ''} 
                onChange={(e) => setReviewData({ ...reviewData, case_number: e.target.value })}
                className="w-full text-xs rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 px-3 py-2.5 dark:text-white" 
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">State Jurisdiction</label>
              <select 
                value={reviewData.state_code || 1} 
                onChange={(e) => setReviewData({ ...reviewData, state_code: parseInt(e.target.value) })}
                className="w-full text-xs rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 px-3 py-2.5 dark:text-white"
              >
                <option value="1">Maharashtra (Subordinate Courts)</option>
                <option value="2">Uttar Pradesh (District Courts)</option>
                <option value="3">Karnataka (District Judiciary)</option>
                <option value="4">Gujarat (Lower Courts)</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">District</label>
              <input 
                type="text" 
                value={reviewData.district || ''} 
                onChange={(e) => setReviewData({ ...reviewData, district: e.target.value })}
                className="w-full text-xs rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 px-3 py-2.5 dark:text-white" 
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Governing Act</label>
              <select 
                value={reviewData.act || 'The Indian Penal Code'} 
                onChange={(e) => setReviewData({ ...reviewData, act: e.target.value })}
                className="w-full text-xs rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 px-3 py-2.5 dark:text-white"
              >
                <option value="The Indian Penal Code">The Indian Penal Code (IPC 1860)</option>
                <option value="Bharatiya Nyaya Sanhita, 2023">Bharatiya Nyaya Sanhita, 2023 (BNS)</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Charged Section(s) (comma-separated)</label>
              <input 
                type="text" 
                value={(reviewData.sections || []).join(', ')} 
                onChange={(e) => setReviewData({ ...reviewData, sections: e.target.value.split(',').map(s => s.trim()).filter(s => s) })}
                className="w-full text-xs rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 px-3 py-2.5 dark:text-white font-mono" 
              />
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button 
              onClick={handleAnalyze} 
              disabled={loading}
              className="px-8 py-3.5 rounded-xl bg-navy-900 hover:bg-navy-800 dark:bg-gold-500 dark:hover:bg-gold-400 text-white dark:text-navy-950 font-bold shadow-lg transition flex items-center gap-2"
            >
              <span>{loading ? 'Running Analysis... ⚡' : 'Confirm & Run 7-Section Analysis ⚡'}</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: RESULTS (7 SECTIONS) */}
      {step === 3 && resultsData && (
        <div className="space-y-8 max-w-5xl mx-auto">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-navy-800 pb-3">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-gold-600 dark:text-gold-400">Analysis Completed</span>
              <h2 className="serif-heading text-2xl sm:text-3xl font-bold text-navy-950 dark:text-white mt-1">Complete Case Intelligence Report</h2>
            </div>
            <button onClick={() => setStep(2)} className="px-4 py-2 rounded-xl text-xs font-bold border border-slate-200 dark:border-navy-700 hover:bg-slate-100 dark:hover:bg-navy-800 transition">
              ✏️ Edit Parameters
            </button>
          </div>

          {/* Section 1: Glance */}
          <div className="p-6 rounded-3xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="serif-heading text-lg font-bold text-navy-950 dark:text-white flex items-center gap-2">
                <span>📋</span> 1. Case at a Glance
              </h3>
              <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 dark:bg-navy-800 dark:text-slate-300">
                Source: Document Extraction / User Confirmed
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              <div className="p-3.5 bg-slate-50 dark:bg-navy-950 rounded-2xl">
                <span className="text-slate-400 block font-semibold">PARTIES</span>
                <span className="font-bold text-navy-950 dark:text-white text-sm">{resultsData.glance.case_title}</span>
              </div>
              <div className="p-3.5 bg-slate-50 dark:bg-navy-950 rounded-2xl">
                <span className="text-slate-400 block font-semibold">CASE NUMBER</span>
                <span className="font-bold text-navy-950 dark:text-white text-sm font-mono">{resultsData.glance.case_number}</span>
              </div>
              <div className="p-3.5 bg-slate-50 dark:bg-navy-950 rounded-2xl">
                <span className="text-slate-400 block font-semibold">VENUE</span>
                <span className="font-bold text-navy-950 dark:text-white text-sm">{resultsData.glance.district}, {resultsData.glance.state}</span>
              </div>
              <div className="p-3.5 bg-slate-50 dark:bg-navy-950 rounded-2xl">
                <span className="text-slate-400 block font-semibold">SECTIONS</span>
                <span className="font-bold text-navy-950 dark:text-white text-sm font-mono">{(resultsData.glance.sections || []).join(', ')}</span>
              </div>
            </div>
          </div>

          {/* Section 2: Duration */}
          <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 shadow-sm space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="serif-heading text-lg font-bold text-navy-950 dark:text-white flex items-center gap-2">
                <span>⏱️</span> 2. How Long Will This Case Take?
              </h3>
              <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
                Source: Hybrid ML Pipeline
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
              <div className={`p-6 rounded-2xl text-center space-y-2 border ${resultsData.duration_prediction.predicted_class === 'ontime' ? 'border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300' : 'border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300'}`}>
                <div className="text-4xl">{resultsData.duration_prediction.predicted_class === 'ontime' ? '⚡' : '⏳'}</div>
                <div className="text-xl font-extrabold">{resultsData.duration_prediction.status_label}</div>
                <p className="text-[11px] text-slate-500">Predicted via two-stage hybrid decision architecture</p>
              </div>

              <div className="p-6 rounded-2xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 text-center space-y-1">
                <span className="text-xs uppercase tracking-wider text-slate-400 font-bold">Predicted Resolution Timeline</span>
                <div className="text-4xl font-extrabold text-navy-950 dark:text-gold-400">
                  {resultsData.duration_prediction.expected_duration_months.toFixed(1)} <span className="text-base font-medium text-slate-500">months</span>
                </div>
                <div className="text-xs text-slate-500 pt-1">
                  Estimated Range: <strong>{resultsData.duration_prediction.duration_range_months[0].toFixed(1)} – {resultsData.duration_prediction.duration_range_months[1].toFixed(1)} months</strong>
                </div>
              </div>

              <div className="p-6 rounded-2xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-navy-800 space-y-3">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-bold text-slate-500">Delay Risk Level:</span>
                  <span className="font-bold text-navy-950 dark:text-white">{resultsData.duration_prediction.delay_risk_pct.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-navy-800 rounded-full h-3 overflow-hidden">
                  <div className={`h-3 rounded-full ${resultsData.duration_prediction.predicted_class === 'ontime' ? 'bg-emerald-500' : 'bg-rose-500'}`} style={{ width: `${resultsData.duration_prediction.delay_risk_pct}%` }}></div>
                </div>
                <div className="p-2 rounded-xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 text-[11px] text-slate-500">
                  {resultsData.duration_prediction.routed_regressor}
                </div>
              </div>
            </div>
          </div>

          {/* Section 5: Bail */}
          <div className="p-6 rounded-3xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 shadow-sm space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="serif-heading text-lg font-bold text-navy-950 dark:text-white flex items-center gap-2">
                <span>⚖️</span> 5. Can I Get Bail? (Statutory Legal Classification)
              </h3>
              <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300">
                Source: First Schedule CrPC / BNSS Law Lookup
              </span>
            </div>

            <div className={`p-5 rounded-2xl flex items-start gap-4 border ${resultsData.bail_assessment.overall_bailable ? 'border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-200' : 'border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/40 text-rose-900 dark:text-rose-200'}`}>
              <div className="text-3xl">{resultsData.bail_assessment.overall_bailable ? '✅' : '⚠️'}</div>
              <div className="space-y-1">
                <h4 className="text-base font-bold">{resultsData.bail_assessment.status_label}</h4>
                <p className="text-xs leading-relaxed">{resultsData.bail_assessment.summary}</p>
              </div>
            </div>
          </div>

        </div>
      )}

    </div>
  );
}
