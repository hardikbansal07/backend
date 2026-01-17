import React from 'react';

export function AltChartsPanel({ data }:{ data:{ chandra?:any; surya?:any } }){
  if(!data) return null;
  const charts = [ ['Chandra', data.chandra], ['Surya', data.surya] ].filter(([_,c])=> !!c) as [string,any][];
  if(charts.length===0) return null;
  return <div className="mt-3 text-[11px] bg-cyan-50 border border-cyan-300 rounded p-2">
    <div className="font-semibold mb-1">Alternative Lagna Charts</div>
    <div className="grid md:grid-cols-2 gap-3">
      {charts.map(([label,c])=> <div key={label} className="border rounded bg-white">
        <div className="px-2 py-1 font-medium bg-cyan-100">{label}</div>
        <table className="text-[10px] w-full">
          <thead><tr><th className="text-left px-1">House</th><th className="text-left px-1">Items</th></tr></thead>
          <tbody>
            {c.houses?.map((h:any)=> <tr key={h.index} className="border-t"><td className="px-1 py-0.5 align-top font-semibold">{h.index}</td><td className="px-1 py-0.5 whitespace-pre leading-tight">{h.items.join(', ')}</td></tr>)}
          </tbody>
        </table>
      </div>)}
    </div>
  </div>;
}
