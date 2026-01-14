import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchVaiseshikamsa, fetchSphuta, fetchBhavaBala, fetchShadbala, fetchAshtakavarga } from '../api';

export function AnalysisPanel({ requestId }: { requestId: string }) {
  const [activeTab, setActiveTab] = React.useState<'shadbala'|'bhavabala'|'ashtakavarga'|'vaiseshikamsa'|'sphuta'>('shadbala');

  return (
    <div className="p-4 bg-white rounded shadow space-y-4">
      <div className="flex flex-wrap gap-2 border-b pb-2">
        {(['shadbala', 'bhavabala', 'ashtakavarga', 'vaiseshikamsa', 'sphuta'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1 rounded text-sm font-medium capitalize ${activeTab === tab ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="min-h-[300px]">
        {activeTab === 'shadbala' && <ShadbalaView requestId={requestId} />}
        {activeTab === 'bhavabala' && <BhavaBalaView requestId={requestId} />}
        {activeTab === 'ashtakavarga' && <AshtakavargaView requestId={requestId} />}
        {activeTab === 'vaiseshikamsa' && <VaiseshikamsaView requestId={requestId} />}
        {activeTab === 'sphuta' && <SphutaView requestId={requestId} />}
      </div>
    </div>
  );
}

function ShadbalaView({ requestId }: { requestId: string }) {
  const { data } = useQuery({ queryKey: ['shadbala', requestId], queryFn: () => fetchShadbala(requestId) });
  if (!data) return <div>Loading Shadbala...</div>;
  
  const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
  
  return (
    <div className="space-y-4">
      <h3 className="font-semibold">Shadbala Analysis</h3>
      <div className="overflow-auto">
        <table className="min-w-full text-xs border">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-2 py-1 text-left">Component</th>
              {planets.map(p => <th key={p} className="px-2 py-1">{p}</th>)}
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.components || {}).map(([key, vals]: any) => (
              <tr key={key} className="border-t">
                <td className="px-2 py-1 font-medium capitalize">{key}</td>
                {Array.isArray(vals) && vals.map((v: number, i: number) => (
                  <td key={i} className="px-2 py-1 text-center">{v.toFixed(2)}</td>
                ))}
              </tr>
            ))}
            <tr className="border-t bg-gray-50 font-bold">
              <td className="px-2 py-1">Total</td>
              {data.total && data.total.map((v: number, i: number) => (
                <td key={i} className="px-2 py-1 text-center">{v.toFixed(2)}</td>
              ))}
            </tr>
            <tr className="border-t">
              <td className="px-2 py-1 font-medium">Rupas</td>
              {data.rupas && data.rupas.map((v: number, i: number) => (
                <td key={i} className="px-2 py-1 text-center">{v.toFixed(2)}</td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
      {data.ishta_kashta && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium text-sm mb-1">Ishta Phala</h4>
            <div className="flex gap-2 text-xs">
              {data.ishta_kashta.ishta.map((v: number, i: number) => (
                <div key={i} className="bg-green-50 border border-green-200 px-1 rounded">
                  {planets[i].slice(0,2)}: {v.toFixed(2)}
                </div>
              ))}
            </div>
          </div>
          <div>
            <h4 className="font-medium text-sm mb-1">Kashta Phala</h4>
            <div className="flex gap-2 text-xs">
              {data.ishta_kashta.kashta.map((v: number, i: number) => (
                <div key={i} className="bg-red-50 border border-red-200 px-1 rounded">
                  {planets[i].slice(0,2)}: {v.toFixed(2)}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function BhavaBalaView({ requestId }: { requestId: string }) {
  const { data } = useQuery({ queryKey: ['bhavabala', requestId], queryFn: () => fetchBhavaBala(requestId) });
  if (!data) return <div>Loading Bhava Bala...</div>;

  return (
    <div className="space-y-4">
      <h3 className="font-semibold">Bhava Bala</h3>
      <div className="grid grid-cols-12 gap-1">
        {data.total && data.total.map((v: number, i: number) => (
          <div key={i} className="flex flex-col items-center border rounded p-1 bg-gray-50">
            <span className="text-[10px] font-bold text-gray-500">H{i+1}</span>
            <span className="text-xs font-medium">{v.toFixed(1)}</span>
            <div className="w-full bg-gray-200 h-1 mt-1 rounded-full overflow-hidden">
              <div className="bg-blue-500 h-full" style={{ width: `${Math.min(100, (v/10)*100)}%` }} />
            </div>
          </div>
        ))}
      </div>
      <div className="text-xs text-gray-500 mt-2">
        Values in Rupas (approx). Higher is stronger.
      </div>
    </div>
  );
}

function AshtakavargaView({ requestId }: { requestId: string }) {
  const { data } = useQuery({ queryKey: ['ashtakavarga', requestId], queryFn: () => fetchAshtakavarga(requestId) });
  if (!data) return <div>Loading Ashtakavarga...</div>;

  const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];

  return (
    <div className="space-y-4">
      <h3 className="font-semibold">Ashtakavarga (SAV & BAV)</h3>
      
      <div className="mb-4">
        <h4 className="font-medium text-sm mb-2">Sarva Ashtakavarga (SAV)</h4>
        <div className="grid grid-cols-12 gap-1">
          {data.sav && data.sav.map((v: number, i: number) => (
            <div key={i} className={`flex flex-col items-center border rounded p-1 ${v >= 28 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
              <span className="text-[10px] font-bold text-gray-500">H{i+1}</span>
              <span className="text-sm font-bold">{v}</span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h4 className="font-medium text-sm mb-2">Bhinna Ashtakavarga (BAV)</h4>
        <div className="overflow-auto">
          <table className="min-w-full text-xs border">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-2 py-1">Planet</th>
                {Array.from({length:12}).map((_, i) => <th key={i} className="px-2 py-1">H{i+1}</th>)}
              </tr>
            </thead>
            <tbody>
              {planets.map((p, i) => {
                const row = data.bav ? data.bav[p] || data.bav[p.toLowerCase()] : null;
                if (!row) return null;
                return (
                  <tr key={p} className="border-t">
                    <td className="px-2 py-1 font-medium">{p}</td>
                    {row.map((v: number, idx: number) => (
                      <td key={idx} className={`px-2 py-1 text-center ${v >= 4 ? 'text-green-700 font-medium' : 'text-gray-500'}`}>{v}</td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      
      {data.sodhita && (
        <div className="mt-4">
          <h4 className="font-medium text-sm mb-2">Sodhita (Purified)</h4>
          <div className="grid grid-cols-12 gap-1">
             {data.sodhita.map((v: number, i: number) => (
              <div key={i} className="flex flex-col items-center border rounded p-1 bg-gray-50">
                <span className="text-[10px] font-bold text-gray-500">H{i+1}</span>
                <span className="text-xs">{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function VaiseshikamsaView({ requestId }: { requestId: string }) {
  const { data } = useQuery({ queryKey: ['vaiseshikamsa', requestId], queryFn: () => fetchVaiseshikamsa(requestId) });
  if (!data) return <div>Loading Vaiseshikamsa...</div>;

  return (
    <div className="space-y-4">
      <h3 className="font-semibold">Vaiseshikamsa (Dasa Varga)</h3>
      <div className="overflow-auto">
        <table className="min-w-full text-xs border">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-2 py-1 text-left">Planet</th>
              <th className="px-2 py-1 text-left">Count</th>
              <th className="px-2 py-1 text-left">Yoga</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data).map(([planet, info]: any) => (
              <tr key={planet} className="border-t">
                <td className="px-2 py-1 font-medium capitalize">{planet}</td>
                <td className="px-2 py-1">{info.count}</td>
                <td className="px-2 py-1 font-medium text-indigo-700">{info.yoga}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="text-xs text-gray-500 mt-2">
        Based on Dasa Varga (10 divisional charts). Shows count of own/exalted/moolatrikona signs.
      </div>
    </div>
  );
}

function SphutaView({ requestId }: { requestId: string }) {
  const { data } = useQuery({ queryKey: ['sphuta', requestId], queryFn: () => fetchSphuta(requestId) });
  if (!data) return <div>Loading Sphuta...</div>;

  return (
    <div className="space-y-4">
      <h3 className="font-semibold">Sphuta (Special Points)</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {Object.entries(data).map(([key, val]: any) => (
          <div key={key} className="border rounded p-2 bg-gray-50">
            <div className="text-xs font-medium text-gray-500 capitalize">{key.replace(/_/g, ' ')}</div>
            <div className="text-sm font-semibold">{val}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
