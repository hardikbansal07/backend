import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchSpecialPoints } from '../api';

export function SpecialPointsPanel({ requestId, initialData }:{ requestId?:string; initialData?: any }){
  // Prefer initialData if supplied (e.g., from rasiChart.sphuta) to avoid extra fetch
  const { data, isLoading, error, refetch } = useQuery({ queryKey:['specialPoints',requestId], queryFn: ()=> fetchSpecialPoints(requestId as string), enabled: !!requestId && !initialData });
  if(!requestId && !initialData) return null;
  const dataSource = initialData ?? data;
  if(!dataSource) return null;
  const pointKeys = ['dhuma','vyatipaata','parivesha','indrachaapa','upaketu','kaala','mrityu','artha_praharaka','yama_ghantaka','gulika','maandi'];
  const zodiac = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'];
  const nakshatras = [
    'Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra','Punarvasu','Pushya','Ashlesha',
    'Magha','Purva Phalguni','Uttara Phalguni','Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha',
    'Mula','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishta','Shatabhisha','Purva Bhadrapada','Uttara Bhadrapada','Revati'
  ];

  const formatDeg = (value:number)=> {
    const d = Math.floor(value);
    const mFloat = (value - d) * 60;
    const m = Math.floor(mFloat);
    const s = Math.round((mFloat - m) * 60);
    return `${d}° ${m}' ${s}\"`;
  };

  return <div className="mb-4 text-[11px] bg-amber-50 border border-amber-300 rounded p-2">
    <div className="flex items-center justify-between mb-1">
      <div className="font-semibold">Special Points / Upagrahas</div>
      <button onClick={()=> refetch()} className="text-[10px] px-2 py-0.5 rounded bg-amber-600 text-white">Reload</button>
    </div>
    {isLoading && <div>Loading...</div>}
    {error && <div className="text-red-600">Error</div>}
    <div className="overflow-auto mb-2">
      <table className="min-w-full text-[11px] bg-white border border-amber-200 rounded">
        <thead className="bg-amber-100">
          <tr>
            <th className="px-2 py-1 text-left">Name</th>
            <th className="px-2 py-1 text-left">Sign</th>
            <th className="px-2 py-1 text-left">Deg</th>
            <th className="px-2 py-1 text-left">Nakshatra</th>
            <th className="px-2 py-1 text-left">Pada</th>
          </tr>
        </thead>
        <tbody>
          {pointKeys.map(k=> {
            const v = (dataSource as any)[k]; if(!v) return null;
            const label = k.replace(/_/g,' ');
            const constIdx = typeof v==='object' && (v as any).constellation!==undefined ? (v as any).constellation as number : undefined;
            const sign = constIdx!==undefined? (zodiac[(constIdx+12)%12] || constIdx) : '';
            const posNum = typeof v==='object' && (v as any).position!==undefined ? Number((v as any).position) : NaN;
            const deg = isNaN(posNum)? '' : formatDeg(posNum);
            let nak = '';
            let pada = '';
            if(constIdx!==undefined && !isNaN(posNum)){
              const absDeg = constIdx*30 + posNum; // 0-360
              const nakIndex = Math.floor(absDeg / (360/27));
              nak = nakshatras[(nakIndex+27)%27] || '';
              const padaIndex = Math.floor((absDeg % (360/27)) / (360/27/4));
              pada = String(padaIndex+1);
            }
            return (
              <tr key={k} className="border-t border-amber-100">
                <td className="px-2 py-1 whitespace-nowrap">{label}</td>
                <td className="px-2 py-1">{sign}</td>
                <td className="px-2 py-1 text-[10px]">{deg}</td>
                <td className="px-2 py-1 text-[10px]">{nak}</td>
                <td className="px-2 py-1 text-[10px]">{pada}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
    {/* Dagdha Rasi formatted */}
  {dataSource.dagdhaRasi && (()=> {
          const zodiac = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'];
          const raw = dataSource.dagdhaRasi;
          let names: string[] = [];
            if(Array.isArray(raw)){
              names = raw.map((n:any)=> typeof n==='number'? zodiac[(n-1+12)%12] || String(n): String(n));
            } else if(typeof raw==='string') {
              const nums = raw.split(/[,\s]+/).filter(Boolean);
              names = nums.map(x=> { const n=parseInt(x,10); return isNaN(n)? x: (zodiac[(n-1+12)%12]||x); });
            } else if(typeof raw==='object') {
              names = Object.values(raw).map((v:any)=> String(v));
            }
          return <span className="px-1.5 py-0.5 rounded bg-amber-200 border border-amber-500 text-[10px]" title={JSON.stringify(raw)}>dagdha:{names.join('/')}</span>;
        })()}
      {dataSource.yogiAvayogi && <div className="text-[10px] mb-1">
        <span className="font-semibold">Yogi:</span> {dataSource.yogiAvayogi.yogi} <span className="font-semibold ml-2">Avayogi:</span> {dataSource.yogiAvayogi.avayogi}
      </div>}
  {dataSource.yogam && <div className="text-[10px] mb-1">Yogam Index: {dataSource.yogam.index}</div>}
  {dataSource.dagdhaRasi && <div className="text-[10px] mb-1">Dagdha Rasi: {Array.isArray(dataSource.dagdhaRasi)? dataSource.dagdhaRasi.join(', '): String(dataSource.dagdhaRasi)}</div>}
      <details className="mt-1">
        <summary className="cursor-pointer text-amber-700">Raw JSON</summary>
  <pre className="bg-gray-900 text-green-200 p-2 rounded max-h-60 overflow-auto text-[10px]">{JSON.stringify(dataSource,null,2)}</pre>
      </details>
  </div>;
}
