import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  fetchDhasa, fetchCharaDasha, fetchSthiraDasha, fetchNarayanaDasha, fetchDrigDasha,
  fetchYogardhaDasha, fetchParyaayaDasha, fetchBrahmaDasha, fetchMandookaDasha,
  fetchSudasaDasha, fetchKalachakraDasha, fetchNavamsaDasha, fetchTrikonaDasha,
  fetchChakraDasha, fetchKendraadhiRasiDasha, fetchRasiDhasaShoola, fetchGrahaDhasa
} from '../api';
import { api } from '../api'; // Need direct access for generic graha dhasas if not exported individually

// Helper to fetch generic graha dhasas since we added them to api.ts but maybe not as individual exports in the snippet I wrote?
// Wait, I added them to fetchAllDashas but not as individual exports in the previous edit.
// Let me check api.ts again. I added them to fetchAllDashas list, but I didn't add individual export functions for them.
// I should add a generic fetchGrahaDhasa function or individual ones.
// For now, I'll implement a generic fetcher here or use api.get directly.

async function fetchGenericGrahaDhasa(requestId: string, system: string, includeAntardhasa: boolean) {
  const res = await api.get(`/api/dhasa/graha/${system}`, { params: { request_id: requestId, limit: 120, include_antardhasa: includeAntardhasa } });
  return res.data;
}

async function fetchShoolaDhasa(requestId: string, includeAntardhasa: boolean) {
  const res = await api.get('/api/dhasa/rasi/shoola', { params: { request_id: requestId, include_antardhasa: includeAntardhasa } });
  return res.data;
}

export function DhasaPanel({ requestId }: { requestId: string }) {
  const [system, setSystem] = React.useState('vimsottari');

  // State for collapsible tree - always declare at top level (React Rules of Hooks)
  const [expandedMDs, setExpandedMDs] = React.useState<Set<number>>(new Set());
  const [expandedADs, setExpandedADs] = React.useState<Set<string>>(new Set());
  const [expandedPDs, setExpandedPDs] = React.useState<Set<string>>(new Set());
  const [expandedSDs, setExpandedSDs] = React.useState<Set<string>>(new Set());

  const { data, isLoading, error } = useQuery({
    queryKey: ['dhasa', requestId, system],
    queryFn: async () => {
      // Always use depth=5 and include_antardhasa=true for all systems
      if (system === 'vimsottari') return fetchDhasa(requestId, true, 5);
      if (system === 'chara') return fetchCharaDasha(requestId, true);
      if (system === 'sthira') return fetchSthiraDasha(requestId, true);
      if (system === 'narayana') return fetchNarayanaDasha(requestId, true);
      if (system === 'drig') return fetchDrigDasha(requestId, true);
      if (system === 'yogardha') return fetchYogardhaDasha(requestId, true);
      if (system === 'paryaaya') return fetchParyaayaDasha(requestId, true);
      if (system === 'brahma') return fetchBrahmaDasha(requestId, true);
      if (system === 'mandooka') return fetchMandookaDasha(requestId, true);
      if (system === 'sudasa') return fetchSudasaDasha(requestId, true);
      if (system === 'kalachakra') return fetchKalachakraDasha(requestId, true);
      if (system === 'navamsa') return fetchNavamsaDasha(requestId, true);
      if (system === 'trikona') return fetchTrikonaDasha(requestId, true);
      if (system === 'chakra') return fetchChakraDasha(requestId, true);
      if (system === 'kendraadhi_rasi') return fetchKendraadhiRasiDasha(requestId, true);
      if (system === 'shoola') return fetchShoolaDhasa(requestId, true);

      // Generic Graha Dhasas
      if (['ashtottari', 'yogini', 'shodashottari', 'dwadasottari', 'panchottari', 'shatabdika', 'chaturashiti_sama', 'dwisaptati_sama', 'shashtihayani'].includes(system)) {
        return fetchGenericGrahaDhasa(requestId, system, true);
      }
      return null;
    },
    enabled: !!requestId
  });

  const toggleMD = (idx: number) => {
    const newSet = new Set(expandedMDs);
    if (newSet.has(idx)) newSet.delete(idx);
    else newSet.add(idx);
    setExpandedMDs(newSet);
  };

  const toggleAD = (key: string) => {
    const newSet = new Set(expandedADs);
    if (newSet.has(key)) newSet.delete(key);
    else newSet.add(key);
    setExpandedADs(newSet);
  };

  const togglePD = (key: string) => {
    const newSet = new Set(expandedPDs);
    if (newSet.has(key)) newSet.delete(key);
    else newSet.add(key);
    setExpandedPDs(newSet);
  };

  const toggleSD = (key: string) => {
    const newSet = new Set(expandedSDs);
    if (newSet.has(key)) newSet.delete(key);
    else newSet.add(key);
    setExpandedSDs(newSet);
  };

  const systems = [
    {
      group: 'Nakshatra (Graha)', options: [
        { value: 'vimsottari', label: 'Vimsottari' },
        { value: 'ashtottari', label: 'Ashtottari' },
        { value: 'yogini', label: 'Yogini' },
        { value: 'shodashottari', label: 'Shodashottari' },
        { value: 'dwadasottari', label: 'Dwadasottari' },
        { value: 'panchottari', label: 'Panchottari' },
        { value: 'shatabdika', label: 'Shatabdika' },
        { value: 'chaturashiti_sama', label: 'Chaturashiti Sama' },
        { value: 'dwisaptati_sama', label: 'Dwisaptati Sama' },
        { value: 'shashtihayani', label: 'Shashtihayani' },
      ]
    },
    {
      group: 'Rasi (Jaimini/Other)', options: [
        { value: 'chara', label: 'Chara' },
        { value: 'sthira', label: 'Sthira' },
        { value: 'narayana', label: 'Narayana' },
        { value: 'drig', label: 'Drig' },
        { value: 'yogardha', label: 'Yogardha' },
        { value: 'paryaaya', label: 'Paryaaya' },
        { value: 'brahma', label: 'Brahma' },
        { value: 'mandooka', label: 'Mandooka' },
        { value: 'sudasa', label: 'Sudasa' },
        { value: 'kalachakra', label: 'Kalachakra' },
        { value: 'navamsa', label: 'Navamsa' },
        { value: 'trikona', label: 'Trikona' },
        { value: 'chakra', label: 'Chakra' },
        { value: 'kendraadhi_rasi', label: 'Kendraadhi Rasi' },
        { value: 'shoola', label: 'Shoola' },
      ]
    }
  ];

  return (
    <div className="p-4 bg-white rounded shadow space-y-4">
      <div className="flex flex-wrap items-center gap-4 border-b pb-4">
        <h2 className="text-lg font-semibold">Dhasas</h2>
        <select
          value={system}
          onChange={e => setSystem(e.target.value)}
          className="border rounded px-2 py-1 text-sm bg-white"
        >
          {systems.map(g => (
            <optgroup key={g.group} label={g.group}>
              {g.options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </optgroup>
          ))}
        </select>

        {system === 'vimsottari' && (
          <span className="text-xs text-gray-600">Showing all 5 levels (MD/AD/PD/SD/PAD)</span>
        )}
      </div>

      {isLoading && <div>Loading Dhasa...</div>}
      {error && <div className="text-red-600">Error loading dhasa</div>}

      {data && (() => {
        const planetNames = ['Sun☉', 'Moon☽', 'Mars♂', 'Mercury☿', 'Jupiter♃', 'Venus♀', 'Saturn♄', 'Rahu☊', 'Ketu☋'];
        const getName = (lord: number) => planetNames[lord] || `P${lord}`;
        const formatDate = (dateArr: number[]) => Array.isArray(dateArr)
          ? `${dateArr[0]}-${String(dateArr[1]).padStart(2, '0')}-${String(dateArr[2]).padStart(2, '0')}`
          : dateArr;

        // Interactive collapsible tree for Vimsottari
        if (system === 'vimsottari' && data.depth && data.depth > 2) {
          return (
            <div className="space-y-2 overflow-auto max-h-[600px] p-2">
              {data.periods?.map((md: any, mdIdx: number) => {
                const mdExpanded = expandedMDs.has(mdIdx);
                return (
                  <div key={mdIdx} className="border rounded shadow-sm">
                    {/* MD Level */}
                    <div
                      onClick={() => toggleMD(mdIdx)}
                      className="bg-indigo-600 text-white px-3 py-2 rounded cursor-pointer hover:bg-indigo-700 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{mdExpanded ? '▼' : '▶'}</span>
                        <span className="font-bold text-lg">{getName(md.lord)}</span>
                        <span className="text-xs opacity-75">MD</span>
                      </div>
                      <span className="text-sm opacity-90">{formatDate(md.start)}</span>
                    </div>

                    {/* AD Level */}
                    {mdExpanded && md.antardasha && (
                      <div className="bg-blue-50 p-2 space-y-1">
                        {md.antardasha.map((ad: any, adIdx: number) => {
                          const adKey = `${mdIdx}-${adIdx}`;
                          const adExpanded = expandedADs.has(adKey);
                          return (
                            <div key={adIdx} className="border rounded bg-white">
                              <div
                                onClick={() => toggleAD(adKey)}
                                className="bg-blue-100 px-3 py-1.5 cursor-pointer hover:bg-blue-200 flex items-center justify-between"
                              >
                                <div className="flex items-center gap-2">
                                  <span className="text-sm">{adExpanded ? '▼' : '▶'}</span>
                                  <span className="font-semibold text-blue-700">{getName(ad.lord)}</span>
                                  <span className="text-xs text-blue-600">AD</span>
                                </div>
                                <span className="text-xs text-blue-600">{formatDate(ad.start)}</span>
                              </div>

                              {/* PD Level */}
                              {adExpanded && ad.pratyantara && (
                                <div className="bg-purple-50 p-2 space-y-1">
                                  {ad.pratyantara.map((pd: any, pdIdx: number) => {
                                    const pdKey = `${adKey}-${pdIdx}`;
                                    const pdExpanded = expandedPDs.has(pdKey);
                                    return (
                                      <div key={pdIdx} className="border rounded bg-white">
                                        <div
                                          onClick={() => togglePD(pdKey)}
                                          className="bg-purple-100 px-3 py-1 cursor-pointer hover:bg-purple-200 flex items-center justify-between text-sm"
                                        >
                                          <div className="flex items-center gap-2">
                                            <span className="text-xs">{pdExpanded ? '▼' : '▶'}</span>
                                            <span className="font-medium text-purple-700">{getName(pd.lord)}</span>
                                            <span className="text-xs text-purple-600">PD</span>
                                          </div>
                                          <span className="text-xs text-purple-600">{formatDate(pd.start)}</span>
                                        </div>

                                        {/* SD Level */}
                                        {pdExpanded && pd.sookshma && (
                                          <div className="bg-orange-50 p-1 space-y-1">
                                            {pd.sookshma.map((sd: any, sdIdx: number) => {
                                              const sdKey = `${pdKey}-${sdIdx}`;
                                              const sdExpanded = expandedSDs.has(sdKey);
                                              return (
                                                <div key={sdIdx} className="border rounded bg-white">
                                                  <div
                                                    onClick={() => toggleSD(sdKey)}
                                                    className="bg-orange-100 px-2 py-1 cursor-pointer hover:bg-orange-200 flex items-center justify-between text-xs"
                                                  >
                                                    <div className="flex items-center gap-1">
                                                      <span className="text-xs">{sdExpanded ? '▼' : '▶'}</span>
                                                      <span className="font-medium text-orange-700">{getName(sd.lord)}</span>
                                                      <span className="text-xs text-orange-600">SD</span>
                                                    </div>
                                                    <span className="text-xs text-orange-600">{formatDate(sd.start)}</span>
                                                  </div>

                                                  {/* PAD Level */}
                                                  {sdExpanded && sd.prana && (
                                                    <div className="bg-gray-50 p-1">
                                                      <div className="grid grid-cols-3 gap-1 text-xs">
                                                        {sd.prana.map((pad: any, padIdx: number) => (
                                                          <div key={padIdx} className="bg-white border px-2 py-1 rounded">
                                                            <span className="text-gray-700 font-medium">{getName(pad.lord)}</span>
                                                            <span className="text-gray-500 ml-1 text-xs">{formatDate(pad.start)}</span>
                                                          </div>
                                                        ))}
                                                      </div>
                                                    </div>
                                                  )}
                                                </div>
                                              );
                                            })}
                                          </div>
                                        )}
                                      </div>
                                    );
                                  })}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          );
        }

        // Flat table for other dasha systems
        const rows = data.periods?.map((p: any) => ({
          start: p.start,
          md: p.dhasaLord || p.dhasaRasi,
          ad: p.antardashaLord || p.bhuktiRasi || '-'
        })) || [];

        return (
          <div className="overflow-auto max-h-[500px]">
            <table className="min-w-full text-xs border">
              <thead className="bg-gray-100 sticky top-0">
                <tr>
                  <th className="px-2 py-1 text-left">Start Date</th>
                  <th className="px-2 py-1 text-left">MD / Rasi</th>
                  <th className="px-2 py-1 text-left">AD / Bhukti</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row: any, i: number) => (
                  <tr key={i} className={`border-t ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                    <td className="px-2 py-1 font-mono whitespace-nowrap">{row.start}</td>
                    <td className="px-2 py-1 font-medium text-indigo-700">{row.md}</td>
                    <td className="px-2 py-1">{row.ad}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })()}
    </div>
  );
}
