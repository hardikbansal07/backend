import React from 'react';

export type ThemeVars = {
  exalted: string;
  debilitated: string;
  own: string;
  mt: string;
  neutral: string;
};

const DEFAULT_THEME: ThemeVars = {
  exalted: '#059669',
  debilitated: '#dc2626',
  own: '#0d9488',
  mt: '#2563eb',
  neutral: '#374151'
};

const STORAGE_KEY = 'customThemeVars';

function applyTheme(vars: ThemeVars){
  const root = document.documentElement;
  root.style.setProperty('--dignity-exalted', vars.exalted);
  root.style.setProperty('--dignity-debilitated', vars.debilitated);
  root.style.setProperty('--dignity-own', vars.own);
  root.style.setProperty('--dignity-mt', vars.mt);
  root.style.setProperty('--dignity-neutral', vars.neutral);
}

export const loadStoredTheme = (): ThemeVars | null => {
  try { const raw = localStorage.getItem(STORAGE_KEY); if(!raw) return null; const parsed = JSON.parse(raw); return { ...DEFAULT_THEME, ...parsed }; } catch { return null; }
};

export const ThemeEditor = ({ onClose }:{ onClose:()=>void }) => {
  const [vars,setVars] = React.useState<ThemeVars>(()=> loadStoredTheme() || DEFAULT_THEME);
  const [exportStr,setExportStr] = React.useState('');
  const PRESETS: Record<string,ThemeVars> = {
    Default: DEFAULT_THEME,
    Solar: { exalted:'#f59e0b', debilitated:'#b91c1c', own:'#d97706', mt:'#2563eb', neutral:'#1f2937' },
    Emerald: { exalted:'#047857', debilitated:'#dc2626', own:'#059669', mt:'#0d9488', neutral:'#064e3b' },
    Vintage: { exalted:'#b45309', debilitated:'#7f1d1d', own:'#92400e', mt:'#6d28d9', neutral:'#44403c' },
    HighContrast: { exalted:'#16a34a', debilitated:'#ef4444', own:'#0ea5e9', mt:'#6366f1', neutral:'#000000' }
  };
  React.useEffect(()=> { applyTheme(vars); },[vars]);
  const save = ()=> { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(vars)); } catch{} onClose(); };
  const reset = ()=> { setVars(DEFAULT_THEME); try { localStorage.removeItem(STORAGE_KEY); } catch{} applyTheme(DEFAULT_THEME); };
  const exportTheme = ()=> { setExportStr(JSON.stringify(vars,null,2)); };
  const importTheme = ()=> { try { if(!exportStr.trim()) return; const parsed = JSON.parse(exportStr); setVars(v=> ({...v, ...parsed})); } catch(e){ alert('Invalid JSON'); } };
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white w-full max-w-md rounded shadow-lg p-4 text-sm relative">
        <button onClick={onClose} className="absolute top-2 right-2 text-xs bg-red-600 text-white px-2 py-0.5 rounded">X</button>
        <h3 className="text-lg font-semibold mb-2">Theme Editor</h3>
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2 mb-1">
            {Object.keys(PRESETS).map(p=> <button key={p} type="button" onClick={()=> setVars(PRESETS[p])} className="px-2 py-0.5 rounded text-[10px] border bg-gray-50 hover:bg-gray-100">
              {p}
            </button>)}
          </div>
          {([
            ['exalted','Exalted'],
            ['debilitated','Debilitated'],
            ['own','Own'],
            ['mt','Moolatrikona'],
            ['neutral','Neutral']
          ] as [keyof ThemeVars,string][]).map(([k,label])=> (
            <label key={k} className="flex items-center justify-between gap-2">
              <span className="w-32">{label}</span>
              <input type="color" value={vars[k]} onChange={e=> setVars(v=> ({...v, [k]: e.target.value}))} className="w-16 h-8 p-0 border" />
              <input value={vars[k]} onChange={e=> setVars(v=> ({...v, [k]: e.target.value}))} className="flex-1 border px-2 py-1 text-xs" />
            </label>
          ))}
          <div className="flex flex-wrap gap-2 mt-2">
            <button onClick={save} className="bg-blue-600 text-white px-3 py-1 rounded text-xs">Save</button>
            <button onClick={reset} className="bg-gray-600 text-white px-3 py-1 rounded text-xs" type="button">Reset</button>
            <button onClick={exportTheme} className="bg-emerald-600 text-white px-3 py-1 rounded text-xs" type="button">Export</button>
            <button onClick={importTheme} className="bg-indigo-600 text-white px-3 py-1 rounded text-xs" type="button">Import</button>
          </div>
          <textarea placeholder="Theme JSON here (for import)" value={exportStr} onChange={e=> setExportStr(e.target.value)} className="w-full h-32 border rounded p-2 text-xs font-mono" />
          <p className="text-[11px] text-gray-500">Changes apply live. Save to persist in local storage. Reset returns to defaults. Export/Import lets you copy themes across devices.</p>
        </div>
      </div>
    </div>
  );
};

// Auto-apply stored theme on module load
try { const stored = loadStoredTheme(); if(stored) applyTheme(stored); } catch {}
