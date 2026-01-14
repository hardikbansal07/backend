import React from 'react';

const STANDARD_VARGAS: { key: string; label: string; desc: string }[] = [
  { key: 'D1', label: 'Rasi (D-1)', desc: 'Main chart, overall life' },
  { key: 'D2', label: 'Hora (D-2)', desc: 'Wealth, finance, prosperity' },
  { key: 'D3', label: 'Drekkana (D-3)', desc: 'Siblings, courage, initiatives' },
  { key: 'D4', label: 'Chaturthamsa (D-4)', desc: 'Property, assets, mother' },
  { key: 'D5', label: 'Panchamsa (D-5)', desc: 'Power, fame, intelligence' },
  { key: 'D6', label: 'Shashthamsa (D-6)', desc: 'Diseases, debts, enemies' },
  { key: 'D7', label: 'Saptamsa (D-7)', desc: 'Children, fertility, progeny' },
  { key: 'D8', label: 'Ashtamsa (D-8)', desc: 'Longevity, death, obstacles' },
  { key: 'D9', label: 'Navamsa (D-9)', desc: 'Marriage, spouse, dharma' },
  { key: 'D10', label: 'Dasamsa (D-10)', desc: 'Career, profession, status' },
  { key: 'D11', label: 'Rudramsa (D-11)', desc: 'Strength, destruction, calamities' },
  { key: 'D12', label: 'Dwadashamsa (D-12)', desc: 'Parents, lineage, ancestors' },
  { key: 'D16', label: 'Shodashamsa (D-16)', desc: 'Comforts, luxuries, vehicles' },
  { key: 'D20', label: 'Vimsamsa (D-20)', desc: 'Spiritual life, devotion' },
  { key: 'D24', label: 'Siddhamsa (D-24)', desc: 'Education, learning, knowledge' },
  { key: 'D27', label: 'Nakshatramsa (D-27)', desc: 'Strengths, weaknesses, vitality' },
  { key: 'D30', label: 'Trimsamsa (D-30)', desc: 'Misfortunes, evils, sins' }
];

const EXTENDED_VARGAS: { key: string; label: string; desc: string }[] = [
  { key: 'D40', label: 'Khavedamsa (D-40)', desc: 'Maternal luck, prosperity' },
  { key: 'D45', label: 'Akshavedamsa (D-45)', desc: 'Spiritual merit, high morals' },
  { key: 'D60', label: 'Shashtyamsa (D-60)', desc: 'Past life karma, destiny' }
];

const RARE_VARGAS: { key: string; label: string; desc: string }[] = [
  { key: 'D81', label: 'Navanavamsa (D-81)', desc: 'Subtle spiritual strength' },
  { key: 'D108', label: 'Ashtottaramsa (D-108)', desc: 'Extreme karmic results' },
  { key: 'D144', label: 'Dwadwadamsa (D-144)', desc: 'Super-fine karmic detailing' }
];

type Props = { result?: any };

function simplePlanetList(planets: any[] | undefined) {
  if(!planets || planets.length===0) return <div className="text-xs text-gray-500">No planet data</div>;
  return (
    <table className="min-w-full text-xs border rounded">
      <thead className="bg-gray-100"><tr>
        <th className="px-2 py-1 text-left">Planet</th>
        <th className="px-2 py-1 text-left">Sign</th>
        <th className="px-2 py-1 text-left">House</th>
        <th className="px-2 py-1 text-left">Deg</th>
      </tr></thead>
      <tbody>
        {planets.map((p:any)=> (
          <tr key={p.name} className="border-t">
            <td className="px-2 py-1 font-medium">{p.name}</td>
            <td className="px-2 py-1">{p.sign||''}</td>
            <td className="px-2 py-1">{p.house||''}</td>
            <td className="px-2 py-1">{p.longitudeDMS||p.longitude||''}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function DivisionalChartsPage({ result }: Props){
  // exclude D1 (Rasi) because D1 is shown in the main Rasi panel
  const divisional = (result?.divisionalCharts || []).filter((c:any)=> (c.factor || 0) !== 1);
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Divisional Charts (Vargas)</h2>
      <p className="text-sm text-gray-600">Standard / Core and extended divisional charts supported by JHora. Below is a quick reference plus any computed divisional charts returned from the backend.</p>

      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <h3 className="font-semibold">Standard / Core</h3>
          <ul className="text-sm list-disc ml-5 mt-2">
            {STANDARD_VARGAS.map(v=> <li key={v.key}><strong>{v.label}</strong> — {v.desc}</li>)}
          </ul>
        </div>
        <div>
          <h3 className="font-semibold">Extended / Rare</h3>
          <ul className="text-sm list-disc ml-5 mt-2">
            {EXTENDED_VARGAS.map(v=> <li key={v.key}><strong>{v.label}</strong> — {v.desc}</li>)}
            {RARE_VARGAS.map(v=> <li key={v.key}><strong>{v.label}</strong> — {v.desc}</li>)}
          </ul>
        </div>
      </div>

      <div>
        <h3 className="font-semibold mt-4">Backend-computed Divisional Charts</h3>
        {divisional.length===0 && <div className="text-xs text-gray-500">No divisional charts present in the loaded horoscope.</div>}
        <div className="space-y-3 mt-2">
          {divisional.map((d:any)=> (
            <div key={d.factor || d.key} className="p-3 border rounded bg-white">
              <div className="flex items-center justify-between">
                <div><strong>{d.key || ('D'+d.factor)}</strong> <span className="text-xs text-gray-500">(factor: {d.factor})</span></div>
                <div className="text-xs text-gray-500">Planets: {Array.isArray(d.planets)? d.planets.length : '—'}</div>
              </div>
              <div className="mt-2 grid md:grid-cols-3 gap-4">
                <div className="md:col-span-2">{simplePlanetList(d.planets)}</div>
                <div className="md:col-span-1 text-xs">
                  <div className="font-semibold mb-1">Special Lagnas</div>
                  {d.specialLagna && Object.keys(d.specialLagna).length>0 ? (
                    <div className="flex flex-col gap-1">
                      {Object.entries(d.specialLagna).map(([k,v])=> (
                        <div key={k} className="px-2 py-1 bg-gray-50 border rounded text-[12px]" title={String(v)}>
                          <strong className="capitalize">{k.replace(/([A-Z])/g, ' $1').trim()}</strong>: <span className="ml-1">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  ) : <div className="text-gray-500">No special lagnas</div>}

                  <div className="font-semibold mt-3 mb-1">Sphuta / Points</div>
                  {d.sphuta && Object.keys(d.sphuta).length>0 ? (
                    <div className="flex flex-col gap-1 max-h-56 overflow-auto">
                      {Object.entries(d.sphuta).map(([k,v])=> (
                        <div key={k} className="px-2 py-0.5 bg-white border rounded text-[12px]" title={String(v)}>
                          <strong>{k}</strong>: <span className="ml-1">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  ) : <div className="text-gray-500">No sphuta data</div>}

                  <details className="mt-3 text-xs"><summary className="cursor-pointer text-blue-700">Raw JSON</summary>
                    <pre className="text-xs bg-gray-100 p-2 rounded max-h-40 overflow-auto">{JSON.stringify({ planets: d.planets, specialLagna: d.specialLagna, sphuta: d.sphuta },null,2)}</pre>
                  </details>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
