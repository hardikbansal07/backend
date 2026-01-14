import React from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { createHoroscope, fetchHouseSystems, fetchLanguages, fetchTimezone, searchPlaces } from '../api';

export function HoroscopeForm({ onResult }:{ onResult:(d:any)=>void }) {
  const initialState = React.useMemo(()=> {
    const base = { birthDateTime:'2000-01-01T06:30:00', place:'Chennai,IN', tzOffset:5.5, lat:'', lon:'', sendToAgent:false, sendToAgentMode:'summary', ayanamsaMode:'TRUE_CITRA', houseSystem:'DEFAULT', calcType: 'drik', language:'en' };
    try {
      const saved = localStorage.getItem('horoForm');
      if(saved){
        const parsed = JSON.parse(saved);
        return { ...base, ...parsed };
      }
    } catch {}
    return base;
  },[]);
  const [state,setState] = React.useState(initialState);
  const [detectedTz,setDetectedTz] = React.useState<string>('');
  const [placeQuery,setPlaceQuery] = React.useState('');
  const [placeResults,setPlaceResults] = React.useState<any[]>([]);
  const [houseSystems,setHouseSystems] = React.useState<{key:string|number;label:string}[]|null>(null);
  const [showAllHouse,setShowAllHouse] = React.useState(false);
  const [tzGuess,setTzGuess] = React.useState<string>('');
  const [geoBusy,setGeoBusy] = React.useState(false);
  const { data: languagesData } = useQuery({ queryKey:['languages'], queryFn: fetchLanguages, staleTime: 86400000, initialData: [{ label:'English', code:'en' }] });
  const languageOptions = (languagesData && languagesData.length>0 ? languagesData : [{ label:'English', code:'en' }]);
  
  React.useEffect(()=>{ let active=true; const run= async()=>{ if(placeQuery.length<2){ setPlaceResults([]); return; } try{ const r= await searchPlaces(placeQuery); if(active) setPlaceResults(r);}catch{} }; run(); return ()=>{active=false}; },[placeQuery]);
  
  const applyPlace = (p:any)=> { setState((s:any)=> ({...s, place: p.label, lat: String(p.latitude), lon: String(p.longitude), tzOffset: p.tzOffsetHours })); setPlaceQuery(''); setPlaceResults([]); };
  const [errors,setErrors] = React.useState<string[]>([]);
  
  const validate = React.useCallback((s=state)=>{
    const e:string[] = [];
    if(!s.birthDateTime || s.birthDateTime.length < 16) e.push('Birth datetime required');
    if(isNaN(Number(s.tzOffset)) || s.tzOffset < -14 || s.tzOffset > 14) e.push('TZ offset must be between -14 and 14');
    if(s.lat){ const v = parseFloat(s.lat); if(isNaN(v) || v<-90 || v>90) e.push('Latitude must be -90..90'); }
    if(s.lon){ const v = parseFloat(s.lon); if(isNaN(v) || v<-180 || v>180) e.push('Longitude must be -180..180'); }
    setErrors(e); return e;
  },[state]);
  
  React.useEffect(()=>{ validate(); },[state,validate]);
  React.useEffect(()=> { try { localStorage.setItem('horoForm', JSON.stringify(state)); } catch {} },[state]);
  
  const mut = useMutation({ mutationFn: async ()=> {
    const e = validate(); if(e.length) throw new Error('Invalid form');
    const loc:any = { place: state.place, tzOffset: state.tzOffset };
    if(state.lat) loc.latitude = parseFloat(state.lat);
    if(state.lon) loc.longitude = parseFloat(state.lon);
    return createHoroscope({ birthDateTime: state.birthDateTime, location: loc, sendToAgent: state.sendToAgent, sendToAgentMode: state.sendToAgentMode, language: state.language || 'en', ayanamsaMode: state.ayanamsaMode, houseSystem: state.houseSystem, calcType: state.calcType });
  }, onSuccess: async (result) => {
    onResult(result);
    
    // Auto-save for authenticated users
    try {
      const storedUser = localStorage.getItem('astro_user');
      if (storedUser && result?.meta?.requestId) {
        const userData = JSON.parse(storedUser);
        if (userData.token) {
          const { api } = await import('../api');
          await api.post('/calc/api/horoscope/store', null, {
            params: { request_id: result.meta.requestId }
          });
          console.log('Horoscope saved to database for user:', userData.email);
        }
      }
    } catch (err) {
      console.warn('Failed to auto-save horoscope:', err);
    }
  } });
  
  const haveErrors = errors.length>0;
  
  return (
    <form onSubmit={e=> {e.preventDefault(); if(!haveErrors) mut.mutate();}} className="space-y-4 bg-white p-6 rounded-lg shadow-md text-sm border border-gray-100">
      <div className="grid md:grid-cols-3 gap-4">
        <label className="flex flex-col font-medium text-gray-700">Birth DateTime
          <div className="flex gap-2 mt-1">
            <input type="datetime-local" value={state.birthDateTime.slice(0,16)} onChange={e=> setState({...state,birthDateTime:e.target.value+':00'})} className="border border-gray-300 rounded px-3 py-2 flex-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" />
            <button type="button" onClick={()=> { const d=new Date(); const pad=(n:number)=> String(n).padStart(2,'0'); const val = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:00`; setState((s:any)=> ({...s,birthDateTime:val})); }} className="text-xs bg-gray-800 hover:bg-gray-900 text-white px-3 rounded transition-colors">Now</button>
          </div>
        </label>
        <label className="flex flex-col relative font-medium text-gray-700">Place
          <input value={placeQuery || state.place} onChange={e=> { setPlaceQuery(e.target.value); setState({...state,place:e.target.value}); }} className="border border-gray-300 rounded px-3 py-2 mt-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" placeholder="Search city..." />
          {placeResults.length>0 && <div className="absolute top-full left-0 right-0 z-20 bg-white border shadow-lg rounded-b-lg text-xs max-h-60 overflow-auto mt-1">
            {placeResults.map(p=> <button type="button" key={p.label+String(p.latitude)} onClick={()=> applyPlace(p)} className="block w-full text-left px-4 py-2 hover:bg-indigo-50 transition-colors border-b last:border-0">
              <div className="font-medium text-gray-900">{p.label}</div>
              <div className="text-gray-500">({p.latitude.toFixed(2)}, {p.longitude.toFixed(2)}) GMT{p.tzOffsetHours>=0?'+':''}{p.tzOffsetHours}</div>
            </button>)}
          </div>}
        </label>
        <label className="flex flex-col font-medium text-gray-700">TZ Offset (hrs)<input type="number" step="0.25" value={state.tzOffset} onChange={e=> setState({...state,tzOffset:parseFloat(e.target.value)})} className="border border-gray-300 rounded px-3 py-2 mt-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" /></label>
        <label className="flex flex-col font-medium text-gray-700">Language
          <select value={state.language || 'en'} onChange={e=> setState({...state, language: e.target.value})} className="border border-gray-300 rounded px-3 py-2 mt-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all bg-white">
            {languageOptions.map(opt=> <option key={opt.code} value={opt.code}>{opt.label}</option>)}
          </select>
        </label>
        <label className="flex flex-col font-medium text-gray-700">Latitude<input placeholder="(optional)" value={state.lat} onChange={e=> setState({...state,lat:e.target.value})} className="border border-gray-300 rounded px-3 py-2 mt-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" /></label>
        <label className="flex flex-col font-medium text-gray-700">Longitude<input placeholder="(optional)" value={state.lon} onChange={e=> setState({...state,lon:e.target.value})} className="border border-gray-300 rounded px-3 py-2 mt-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" /></label>
        <label className="flex flex-col font-medium text-gray-700">Ayanamsa
          <select value={state.ayanamsaMode} onChange={e=> setState({...state, ayanamsaMode:e.target.value})} className="border border-gray-300 rounded px-3 py-2 mt-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all bg-white">
            <option value="TRUE_CITRA">Lahiri (Chitra)</option>
            <option value="LAHIRI">Lahiri (Legacy)</option>
            <option value="RAMAN">Raman</option>
            <option value="KP">KP</option>
            <option value="SURYASIDDHANTA">Surya Siddhanta</option>
          </select>
        </label>
        <label className="flex flex-col font-medium text-gray-700">Calculation
          <select value={state.calcType} onChange={e=> setState({...state, calcType: e.target.value})} className="border border-gray-300 rounded px-3 py-2 mt-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all bg-white">
            <option value="drik">Drik (default)</option>
            <option value="ss">Surya Siddhanta</option>
          </select>
        </label>
        <label className="flex flex-col font-medium text-gray-700">House System
          <div className="flex gap-2 items-center mt-1">
            <select value={state.houseSystem} onChange={e=> setState({...state, houseSystem:e.target.value})} onFocus={async()=> { if(!houseSystems){ try { const r = await fetchHouseSystems(); setHouseSystems(r.items); } catch{} } }} className="border border-gray-300 rounded px-3 py-2 flex-1 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all bg-white">
              <option value="DEFAULT">Default</option>
              <option value="equal">Equal</option>
              <option value="sripati">Sripati</option>
              <option value="placidus">Placidus</option>
              {showAllHouse && houseSystems && houseSystems.filter(h=> !['1','2','3','4'].includes(String(h.key))).map(h=> <option key={h.key} value={String(h.key)}>{h.label}</option>)}
            </select>
            <button type="button" onClick={()=> setShowAllHouse(s=> !s)} className="text-xs px-2 py-1 border rounded bg-gray-50 hover:bg-gray-100 transition-colors" title="Toggle extended systems">{showAllHouse? 'Less':'More'}</button>
          </div>
        </label>
      </div>
      <div className="flex flex-wrap items-center gap-4 pt-2">
        <label className="inline-flex items-center gap-2 cursor-pointer"><input type="checkbox" checked={state.sendToAgent} onChange={e=> setState({...state,sendToAgent:e.target.checked})} className="rounded text-indigo-600 focus:ring-indigo-500" /><span className="text-gray-700">Send To Agent</span></label>
        {state.sendToAgent && <select value={state.sendToAgentMode} onChange={e=> setState({...state, sendToAgentMode: e.target.value})} className="border border-gray-300 px-2 py-1 rounded text-xs bg-white">
          <option value="summary">Agent:Summary</option>
          <option value="bundle">Agent:Bundle</option>
          <option value="full">Agent:Full</option>
        </select>}
        <button type="button" onClick={()=> { const off = -new Date().getTimezoneOffset()/60; const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; setState((s:any)=> ({...s, tzOffset: parseFloat(off.toFixed(2)) })); setDetectedTz(tz + ' (GMT'+(off>=0?'+':'')+off+')'); }} className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1.5 rounded transition-colors">Use My Timezone</button>
        <button type="button" disabled={geoBusy} onClick={async()=> {
          try {
            setGeoBusy(true); setTzGuess('');
            await new Promise<void>((resolve,reject)=> {
              if(!navigator.geolocation){ reject('geolocation unsupported'); return; }
              navigator.geolocation.getCurrentPosition(pos=> { resolve(); const { latitude, longitude } = pos.coords; (async()=> {
                try {
                  const guess = await fetchTimezone(latitude, longitude, state.birthDateTime);
                  setTzGuess(`${guess.timezone||''} GMT${guess.offsetHours>=0?'+':''}${guess.offsetHours}`);
                  setDetectedTz(`Auto: ${guess.timezone||''}`);
                  setState((s:any)=> ({...s, lat: latitude.toFixed(4), lon: longitude.toFixed(4), tzOffset: guess.offsetHours }));
                } catch(e){ setTzGuess('Failed'); }
              })(); }, err=> { reject(err.message); });
            });
          } catch(e:any){ setTzGuess('Geo blocked'); }
          finally { setGeoBusy(false); }
        }} className="text-xs bg-teal-600 hover:bg-teal-700 text-white px-3 py-1.5 rounded disabled:opacity-50 transition-colors" title="Geolocate & guess timezone">{geoBusy? 'Locating...':'Auto TZ'}</button>
        {detectedTz && <span className="text-xs text-indigo-700 font-medium">{detectedTz}</span>}
        {tzGuess && <span className="text-[10px] px-2 py-0.5 bg-teal-50 border border-teal-300 rounded text-teal-800">{tzGuess}</span>}
      </div>
      {haveErrors && <ul className="text-xs text-red-600 list-disc ml-4">{errors.map(er=> <li key={er}>{er}</li>)}</ul>}
      {mut.error && !haveErrors && <div className="text-xs text-red-600 bg-red-50 p-2 rounded">{(mut.error as any).message || 'Error'}</div>}
      <button disabled={mut.isPending || haveErrors} className="w-full md:w-auto bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded font-medium text-sm disabled:opacity-50 transition-colors shadow-sm">{mut.isPending?'Computing...':'Generate Horoscope'}</button>
    </form>
  );
}
