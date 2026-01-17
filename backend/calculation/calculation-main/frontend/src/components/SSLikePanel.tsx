import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchSSLikeView, fetchSSLikeFlat } from '../api';

function TableSixCols({ rows, title }:{ rows: any[]; title?: string }){
  if(!rows || rows.length===0) return <div className="text-xs text-gray-500">No rows</div>;
  return (
    <div>
      {title && <div className="text-sm font-semibold mb-1">{title}</div>}
      <div className="overflow-auto border rounded max-h-64">
        <table className="min-w-full text-[11px]">
          <thead className="bg-gray-100 sticky top-0"><tr>
            <th className="px-2 py-1 text-left">Body</th>
            <th className="px-2 py-1 text-left">Longitude</th>
            <th className="px-2 py-1 text-left">Nakshatra</th>
            <th className="px-2 py-1 text-left">Pada</th>
            <th className="px-2 py-1 text-left">Rasi</th>
            <th className="px-2 py-1 text-left">Navamsa</th>
          </tr></thead>
          <tbody>
            {rows.map((r:any,i:number)=> (
              <tr key={i} className="border-t">
                <td className="px-2 py-1 whitespace-nowrap">{r.Body}</td>
                <td className="px-2 py-1 whitespace-nowrap font-mono">{r.Longitude}</td>
                <td className="px-2 py-1">{r.Nakshatra}</td>
                <td className="px-2 py-1">{r.Pada}</td>
                <td className="px-2 py-1">{r.Rasi}</td>
                <td className="px-2 py-1">{r.Navamsa || ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function SSLikePanel({ requestId }:{ requestId: string }){
  const [factor, setFactor] = React.useState<number>(1);
  const { data: viewData, isLoading: viewLoading, error: viewError, refetch: refetchView } = useQuery({
    queryKey: ['sslike-view', requestId],
    queryFn: ()=> fetchSSLikeView(requestId),
    enabled: !!requestId
  });
  const { data: flatData, isLoading: flatLoading, error: flatError, refetch: refetchFlat } = useQuery({
    queryKey: ['sslike-flat', requestId, factor],
    queryFn: ()=> fetchSSLikeFlat(requestId, factor),
    enabled: !!requestId
  });

  return (
    <div className="mb-4 text-[11px] bg-indigo-50 border border-indigo-300 rounded p-2">
      <div className="flex items-center justify-between mb-2">
        <div className="font-semibold">SS-like Table</div>
        <div className="flex items-center gap-2">
          <label className="text-[10px]">Factor</label>
          <select value={factor} onChange={e=> setFactor(parseInt(e.target.value,10)||1)} className="border px-1 py-0.5 rounded text-[10px]">
            {[1,2,3,4,5,6,7,8,9,10,12,16,20,24,27,30,36,40,45,60,72,81,108,144].map(f=> <option key={f} value={f}>D{f}</option>)}
          </select>
          <button onClick={()=> { refetchView(); refetchFlat(); }} className="text-[10px] px-2 py-0.5 rounded bg-indigo-600 text-white">Reload</button>
        </div>
      </div>

      {viewLoading && <div>Loading view…</div>}
      {viewError && <div className="text-red-600">Failed to load view</div>}
      {viewData?.panelRows && <div className="mb-3"><TableSixCols rows={viewData.panelRows} title="D1 Panel"/></div>}

      {flatLoading && <div>Loading flat…</div>}
      {flatError && <div className="text-red-600">Failed to load flat rows</div>}
      {flatData?.rows && <div className=""><TableSixCols rows={flatData.rows} title={`Flat D${flatData.factor}`}/></div>}

      {Array.isArray(viewData?.extendedPoints) && viewData.extendedPoints.length>0 && (
        <details className="mt-2">
          <summary className="cursor-pointer text-indigo-700">Extended Points</summary>
          <div className="mt-1 flex flex-wrap gap-1">
            {viewData.extendedPoints.map((p:any, i:number)=> (
              <span key={i} className="px-1.5 py-0.5 rounded bg-white border border-indigo-300" title={JSON.stringify(p)}>
                {p.name}{p.longitudeDMS? `: ${p.longitudeDMS}`:''}{p.nakshatra? ` (${p.nakshatra}-${p.pada||''})`:''}
              </span>
            ))}
          </div>
        </details>
      )}

      {viewData?.vargas && viewData.vargas.length>0 && (
        <details className="mt-2">
          <summary className="cursor-pointer text-indigo-700">More Vargas (view rows)</summary>
          <div className="mt-2 grid md:grid-cols-2 gap-3">
            {viewData.vargas.map((v:any)=> (
              <TableSixCols key={v.factor} rows={v.rows} title={`D${v.factor}`}/>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
