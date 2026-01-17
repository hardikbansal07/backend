import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api';

async function fetchPlanetFlags(requestId:string){
  const res = await api.get('/api/flags/planets',{ params:{ request_id: requestId }} as any);
  return res.data as { requestId:string; combustion:string[]; vargottama:string[] };
}

export function PlanetFlagsBadge({ requestId }:{ requestId:string }){
  const { data } = useQuery({ queryKey:['planetFlags',requestId], queryFn: ()=> fetchPlanetFlags(requestId), enabled: !!requestId, staleTime:15000 });
  React.useEffect(()=> { if(data){ try { (window as any).__planetFlags = data; } catch{} } },[data]);
  if(!data) return <div className="text-[10px] px-2 py-0.5 rounded bg-gray-100 border border-gray-300">Flags: loading...</div>;
  const combustCnt = data.combustion.length;
  const vargCnt = data.vargottama.length;
  return <div className="flex flex-wrap gap-2 text-[10px]">
    <span className="px-1.5 py-0.5 rounded bg-red-50 text-red-700 border border-red-300" title={combustCnt? data.combustion.join(', '):'No combust planets'}>Combust({combustCnt}){combustCnt? ':'+data.combustion.join(','):''}</span>
    <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-300" title={vargCnt? data.vargottama.join(', '):'No vargottama planets'}>Vargottama({vargCnt}){vargCnt? ':'+data.vargottama.join(','):''}</span>
  </div>;
}
