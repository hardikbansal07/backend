import React from 'react';
import { useState } from 'react';

export function ArudhaPanel({ data }:{ data:{ bhavaArudhas:Record<string,string>; bhavaArudhasD9?:Record<string,string>|null; menu?:Record<string,string[]> } }){
  const [showMenu,setShowMenu] = useState(false);
  if(!data) return null;
  const keys = Object.keys(data.bhavaArudhas||{});
  const keysD9 = data.bhavaArudhasD9? Object.keys(data.bhavaArudhasD9):[];
  return <div className="mt-3 text-[11px] bg-amber-50 border border-amber-300 rounded p-2">
    <div className="flex items-center justify-between mb-1">
      <div className="font-semibold">Arudha Padas</div>
      <div className="flex items-center gap-2">
        {data.menu && <button type="button" onClick={()=> setShowMenu(s=> !s)} className={`px-1.5 py-0.5 rounded text-[10px] ${showMenu?'bg-amber-600 text-white':'bg-amber-200 text-amber-800'}`}>{showMenu? 'Hide Grid':'Grid'}</button>}
      </div>
    </div>
    <div className="flex flex-wrap gap-2">
      {keys.map(k=> <span key={k} className="px-1 py-0.5 bg-white border border-amber-300 rounded" title={k}>{k.split('-').slice(-1)}: {data.bhavaArudhas[k]}</span>)}
    </div>
    {keysD9.length>0 && <div className="mt-2"><div className="font-medium mb-1">D9</div><div className="flex flex-wrap gap-2">{keysD9.map(k=> <span key={k} className="px-1 py-0.5 bg-white border border-amber-300 rounded" title={k}>{k.split('-').slice(-1)}: {data.bhavaArudhasD9?.[k]}</span>)}</div></div>}
    {showMenu && data.menu && <details open className="mt-2">
      <summary className="cursor-pointer text-amber-700">Menu Grid</summary>
      <div className="overflow-auto max-h-64 mt-1">
        <table className="text-[10px] border min-w-full">
          <tbody>
            {Object.entries(data.menu).map(([k,v])=> <tr key={k} className="border-t"><th className="text-left px-1 py-0.5 bg-amber-100 sticky left-0">{k}</th>{v.map((cell,i)=><td key={i} className="px-1 py-0.5 border-l align-top whitespace-pre leading-tight">{cell||''}</td>)}</tr>)}
          </tbody>
        </table>
      </div>
    </details>}
  </div>;
}
