import React from 'react';

export function BhavaChakraPanel({ data }:{ data:{ houses?: { house:number; start:string; mid:string; end:string; planets:string[] }[] } }){
  if(!data?.houses) return null;
  return <div className="mt-3 text-[11px] bg-fuchsia-50 border border-fuchsia-300 rounded p-2">
    <div className="font-semibold mb-1">Bhava Chakra</div>
    <div className="overflow-auto max-h-72">
      <table className="text-[10px] min-w-full">
        <thead><tr className="bg-fuchsia-100"><th className="px-1 text-left">House</th><th className="px-1 text-left">Start</th><th className="px-1 text-left">Mid</th><th className="px-1 text-left">End</th><th className="px-1 text-left">Planets</th></tr></thead>
        <tbody>
          {data.houses.map(h=> <tr key={h.house} className="border-t"><td className="px-1 py-0.5 font-semibold">{h.house}</td><td className="px-1 py-0.5 whitespace-nowrap">{h.start}</td><td className="px-1 py-0.5 whitespace-nowrap">{h.mid}</td><td className="px-1 py-0.5 whitespace-nowrap">{h.end}</td><td className="px-1 py-0.5">{h.planets.join(', ')}</td></tr>)}
        </tbody>
      </table>
    </div>
  </div>;
}
