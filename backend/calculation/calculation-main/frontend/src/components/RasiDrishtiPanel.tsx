import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api';

async function fetchRasiDrishti(requestId:string){
  const res = await api.get('/api/rasi_drishti',{ params:{ request_id: requestId }} as any);
  return res.data as { requestId:string; rasiToRasi:string[][]; rasiToPlanets:string[][] };
}

export function RasiDrishtiPanel({ requestId }:{ requestId:string }){
  const { data, isLoading, error, refetch } = useQuery({ queryKey:['rasiDrishti',requestId], queryFn: ()=> fetchRasiDrishti(requestId), enabled: !!requestId });
  if(!requestId) return null;
  const hasBackendError = (data as any)?.error;
  const r2r = Array.isArray(data?.rasiToRasi) ? data!.rasiToRasi : [];
  const r2p = Array.isArray(data?.rasiToPlanets) ? data!.rasiToPlanets : [];
  return <div className="mb-4 text-[11px] bg-violet-50 border border-violet-300 rounded p-2">
    <div className="flex items-center justify-between mb-1">
      <div className="font-semibold">Rasi Drishti</div>
      <button onClick={()=> refetch()} className="px-2 py-0.5 text-[10px] rounded bg-violet-600 text-white">Reload</button>
    </div>
    {isLoading && <div>Loading...</div>}
    {error && <div className="text-red-600 text-xs">Request failed</div>}
    {hasBackendError && <div className="text-red-600 text-xs">Backend error: {(data as any).error}</div>}
    {!isLoading && !error && !hasBackendError && data && <div className="grid md:grid-cols-2 gap-3">
      <div>
        <div className="font-medium mb-1 text-xs">Rasi -&gt; Rasi</div>
        {r2r.length===0 && <div className="text-[10px] text-gray-500">No data</div>}
        {r2r.length>0 && <ul className="space-y-0.5 max-h-40 overflow-auto pr-1">
          {r2r.map((lst,i)=> <li key={i}><span className="font-semibold">{i+1}</span>: {Array.isArray(lst)&&lst.length? lst.join(', '):'-'}</li>)}
        </ul>}
      </div>
      <div>
        <div className="font-medium mb-1 text-xs">Rasi -&gt; Planets</div>
        {r2p.length===0 && <div className="text-[10px] text-gray-500">No data</div>}
        {r2p.length>0 && <ul className="space-y-0.5 max-h-40 overflow-auto pr-1">
          {r2p.map((lst,i)=> <li key={i}><span className="font-semibold">{i+1}</span>: {Array.isArray(lst)&&lst.length? lst.join(', '):'-'}</li>)}
        </ul>}
      </div>
    </div>}
  </div>;
}
