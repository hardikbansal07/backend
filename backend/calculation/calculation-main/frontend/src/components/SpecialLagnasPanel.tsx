import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api';

async function fetchSpecialLagnas(requestId: string){
  if(!requestId) throw new Error('requestId required');
  const res = await api.get('/api/special_lagnas',{ params:{ request_id: requestId }} as any);
  return res.data as any;
}

export function SpecialLagnasPanel({ requestId, initialData }:{ requestId:string; initialData?: any }){
  // If initialData provided (for example from the returned horoscope payload), prefer it and skip remote fetch.
  const { data, isLoading, error, refetch } = useQuery({ queryKey:['specialLagnas',requestId], queryFn: ()=> fetchSpecialLagnas(requestId), enabled: !!requestId && !initialData });
  if(!requestId && !initialData) return null;
  const dataSource = initialData ?? data;
  if(!dataSource) return null;
  const lagnaKeys = ['bhavaLagna','horaLagna','ghatiLagna','vighatiLagna','pranapadaLagna','sriLagna','induLagna','kundaLagna','varnadaLagna','bhriguBindu','gulika','maandi'];
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
    return `${d}° ${m}' ${s}"`;
  };

  return <div className="mb-4 text-xs bg-fuchsia-50 border border-fuchsia-300 rounded p-2">
    <div className="flex items-center justify-between mb-1">
      <div className="font-semibold">Special Lagnas</div>
      <button onClick={()=> refetch()} className="text-[10px] px-2 py-0.5 rounded bg-fuchsia-600 text-white">Reload</button>
    </div>
    {isLoading && <div>Loading...</div>}
    {error && <div className="text-red-600">Error</div>}
    <div className="overflow-auto">
      <table className="min-w-full text-[11px] bg-white border border-fuchsia-200 rounded">
        <thead className="bg-fuchsia-100">
          <tr>
            <th className="px-2 py-1 text-left">Name</th>
            <th className="px-2 py-1 text-left">Sign</th>
            <th className="px-2 py-1 text-left">Deg</th>
            <th className="px-2 py-1 text-left">Nakshatra</th>
            <th className="px-2 py-1 text-left">Pada</th>
            <th className="px-2 py-1 text-left">House</th>
          </tr>
        </thead>
        <tbody>
          {lagnaKeys.map(k=> {
            const v = (dataSource as any)[k];
            if(!v) return null;
            const label = k.replace(/Lagna$/,' Lagna').replace(/_/g,' ');
            let house: number | undefined = typeof v==='object' && v && ('house' in v)? (v as any).house: undefined;

            let sign = '';
            let deg = '';
            let nak = '';
            let pada = '';

            // Data comes as [signIndex, degreeInSign]
            if(typeof v === 'object' && v && Array.isArray((v as any).data)){
              const arr = (v as any).data as [number, number];
              const signIdx = Number(arr[0]);
              const degInSign = Number(arr[1]);
              if(!isNaN(signIdx) && !isNaN(degInSign)){
                if(house === undefined){
                  house = signIdx + 1; // 1-12 from sign index
                }
                const absLongitude = signIdx*30 + degInSign;
                const norm = ((absLongitude % 360) + 360) % 360;
                const sIdx = Math.floor(norm / 30);
                const degWithin = norm - sIdx*30;
                sign = zodiac[(sIdx+12)%12] || '';
                deg = formatDeg(degWithin);
                const nakIndex = Math.floor(norm / (360/27));
                nak = nakshatras[(nakIndex+27)%27] || '';
                const padaIndex = Math.floor((norm % (360/27)) / (360/27/4));
                pada = String(padaIndex+1);
              }
            }
            return (
              <tr key={k} className="border-t border-fuchsia-100">
                <td className="px-2 py-1 whitespace-nowrap">{label}</td>
                <td className="px-2 py-1">{sign}</td>
                <td className="px-2 py-1 text-[10px]">{deg}</td>
                <td className="px-2 py-1 text-[10px]">{nak}</td>
                <td className="px-2 py-1 text-[10px]">{pada}</td>
                <td className="px-2 py-1">{house!==undefined? house:''}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
    {dataSource?.bhavaCusps && <details className="mt-2"><summary className="cursor-pointer">Bhava Cusps</summary>
      <pre className="max-h-40 overflow-auto bg-gray-900 text-green-200 p-2 rounded">{JSON.stringify(dataSource.bhavaCusps,null,2)}</pre>
    </details>}

    <details className="mt-2">
      <summary className="cursor-pointer text-[11px] text-fuchsia-700">Raw JSON (Special Lagnas)</summary>
      <pre className="max-h-52 overflow-auto bg-gray-900 text-green-200 p-2 rounded text-[10px]">{JSON.stringify(dataSource,null,2)}</pre>
    </details>
  </div>;
}
