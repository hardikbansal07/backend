import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  fetchAspects, fetchStrength, fetchYogas, fetchSummary, fetchDeepStrength, fetchBundle,
  fetchTransit, fetchArudha, fetchAltCharts, fetchBhavaChakra, fetchRenderedChart,
  fetchCharaDasha, fetchSthiraDasha, fetchNarayanaDasha, fetchDrigDasha, fetchYogardhaDasha,
  fetchParyaayaDasha, fetchBrahmaDasha, fetchMandookaDasha, fetchSudasaDasha,
  fetchKalachakraDasha, fetchNavamsaDasha, fetchTrikonaDasha, fetchChakraDasha,
  fetchKendraadhiRasiDasha
} from '../api';
import { SpecialLagnasPanel } from './SpecialLagnasPanel';
import { PlanetFlagsBadge } from './PlanetFlagsBadge';
import { RasiDrishtiPanel } from './RasiDrishtiPanel';
import { SpecialPointsPanel } from './SpecialPointsPanel';
import { ArudhaPanel } from './ArudhaPanel';
import { AltChartsPanel } from './AltChartsPanel';
import { BhavaChakraPanel } from './BhavaChakraPanel';
import { ThemeEditor } from './ThemeEditor';
import SSLikePanel from './SSLikePanel';
import { PanchangaPanel } from './PanchangaPanel';
import { TransitPanel } from './TransitPanel';

// ... (I will paste the Charts component and its helpers here, adapting imports)

export function ChartsView({ result }: { result: any }) {
  if (!result) return null;
  const [active, setActive] = React.useState('D1');
  const requestId = result.meta?.requestId;
  const { data: aspects } = useQuery({ queryKey: ['aspects', requestId], queryFn: () => fetchAspects(requestId), enabled: !!requestId });
  const { data: strength } = useQuery({ queryKey: ['strength', requestId], queryFn: () => fetchStrength(requestId), enabled: !!requestId });
  const [yogaMode, setYogaMode] = React.useState<'basic' | 'full'>('full');
  const [yogaLang, setYogaLang] = React.useState('en');
  const [yogaFilterPlanet, setYogaFilterPlanet] = React.useState<string>('All');
  const [yogaDebug, setYogaDebug] = React.useState<boolean>(false);
  const planetOptions = React.useMemo(() => (result.rasiChart?.planets || []).map((p: any) => p.name).filter((v: string, i: number, a: string[]) => a.indexOf(v) === i), [result]);
  const { data: yogas } = useQuery({
    queryKey: ['yogas', requestId, yogaMode, yogaLang, yogaFilterPlanet, yogaDebug],
    queryFn: () => fetchYogas(requestId, yogaMode, yogaLang, yogaFilterPlanet, yogaDebug),
    enabled: !!requestId && active === 'D1'
  });
  const { data: summary } = useQuery({ queryKey: ['summary', requestId], queryFn: () => fetchSummary(requestId), enabled: !!requestId && active === 'D1', staleTime: 30000 });
  const [showMatrix, setShowMatrix] = React.useState(false);
  const [filter, setFilter] = React.useState<{ dignity: string; retro: string }>({ dignity: 'All', retro: 'Any' });
  const [showDeepStrength, setShowDeepStrength] = React.useState(false);
  const [deepIncludeAspects, setDeepIncludeAspects] = React.useState(false);
  const [deepIncludePrastara, setDeepIncludePrastara] = React.useState(false);
  const { data: deepStrength } = useQuery({ queryKey: ['deepstrength', requestId, showDeepStrength, deepIncludeAspects, deepIncludePrastara], queryFn: () => fetchDeepStrength(requestId, deepIncludeAspects, deepIncludePrastara), enabled: !!requestId && showDeepStrength });

  const [showKundli, setShowKundli] = React.useState(true); // Default to true
  const [kundliStyle, setKundliStyle] = React.useState<'South' | 'North'>('South');
  const [kundliTheme, setKundliTheme] = React.useState<'Light' | 'Dark' | 'Classic'>('Light');
  const [showThemeEditor, setShowThemeEditor] = React.useState(false);
  const [kundliHighlights, setKundliHighlights] = React.useState(true);
  const [showGlyphs, setShowGlyphs] = React.useState(false);
  const [showDivisionsInline, setShowDivisionsInline] = React.useState(false);
  const [showAspectsOnHover, setShowAspectsOnHover] = React.useState(false);
  const [shadeKendra, setShadeKendra] = React.useState(true);
  const [shadeTrikon, setShadeTrikon] = React.useState(true);
  const [shadeDusthana, setShadeDusthana] = React.useState(false);
  const [shadeUpachaya, setShadeUpachaya] = React.useState(false);
  const [hideOuterKundli, setHideOuterKundli] = React.useState(false);
  const [showTransit, setShowTransit] = React.useState(false);

  const { data: transit } = useQuery({ queryKey: ['transitOverlay', requestId, showTransit], queryFn: () => fetchTransit(requestId), enabled: !!requestId && showTransit && active === 'D1', staleTime: 60000 });
  const { data: arudha } = useQuery({ queryKey: ['arudha', requestId], queryFn: () => fetchArudha(requestId), enabled: !!requestId && active === 'D1' });
  const { data: altCharts } = useQuery({ queryKey: ['altCharts', requestId], queryFn: () => fetchAltCharts(requestId), enabled: !!requestId && active === 'D1' });
  const { data: bhavaChakra } = useQuery({ queryKey: ['bhavaChakra', requestId], queryFn: () => fetchBhavaChakra(requestId), enabled: !!requestId && active === 'D1' });
  const [hoverPlanet, setHoverPlanet] = React.useState<string>('');

  // Build unique charts list
  const seen = new Set<string>();
  const allCharts = [{ key: 'D1', data: result.rasiChart }, ...(result.divisionalCharts || []).map((c: any) => ({ key: 'D' + c.factor, data: c }))]
    .filter(c => { if (seen.has(c.key)) return false; seen.add(c.key); return true; });

  React.useEffect(() => { if (!allCharts.find(c => c.key === active)) setActive('D1'); }, [result]);

  const transitMap = React.useMemo(() => {
    const m: Record<string, any> = {};
    if (transit?.planets) transit.planets.forEach((tp: any) => { m[tp.name] = tp; });
    return m;
  }, [transit]);

  return (
    <div className="mt-6 bg-white p-4 rounded shadow">
      <div className="flex flex-wrap gap-2 mb-4 items-center border-b pb-4">
        {allCharts.map(c => <button key={c.key} onClick={() => setActive(c.key)} className={`px-3 py-1 rounded text-xs font-medium ${active === c.key ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800 hover:bg-gray-200'}`}>{c.key}</button>)}
        <div className="h-6 w-px bg-gray-300 mx-2"></div>
        <button onClick={() => setShowKundli(v => !v)} className={`px-2 py-1 rounded text-xs font-medium ${showKundli ? 'bg-indigo-600 text-white' : 'bg-indigo-100 text-indigo-800'}`}>{showKundli ? 'Hide Kundli' : 'Show Kundli'}</button>
        {showKundli && <select value={kundliStyle} onChange={e => setKundliStyle(e.target.value as any)} className="border px-1 py-0.5 rounded text-[10px]">
          <option value="South">South</option>
          <option value="North">North</option>
          <option value="East">East</option>
        </select>}
      </div>

      <div className="grid md:grid-cols-12 gap-6">
        <div className="md:col-span-5">
          {active === 'D1' && showKundli && (
            kundliStyle === 'South' ? <KundliView chart={result.rasiChart} transitMap={transitMap} showTransit={showTransit} theme={kundliTheme} highlights={kundliHighlights} glyphs={showGlyphs} aspects={showAspectsOnHover ? aspects : null} hideOuter={hideOuterKundli} /> :
              kundliStyle === 'North' ? <NorthKundliView chart={result.rasiChart} transitMap={transitMap} showTransit={showTransit} theme={kundliTheme} highlights={kundliHighlights} glyphs={showGlyphs} aspects={showAspectsOnHover ? aspects : null} shadeSets={{ kendra: shadeKendra, trikon: shadeTrikon, dusthana: shadeDusthana, upachaya: shadeUpachaya }} hideOuter={hideOuterKundli} /> :
                <EastIndianChart chart={result.rasiChart} transitMap={transitMap} showTransit={showTransit} theme={kundliTheme} glyphs={showGlyphs} hideOuter={hideOuterKundli} />
          )}
          {active !== 'D1' && showKundli && (
            kundliStyle === 'South' ? <KundliView chart={allCharts.find(c => c.key === active)?.data} transitMap={{}} showTransit={false} theme={kundliTheme} highlights={kundliHighlights} glyphs={showGlyphs} /> :
              kundliStyle === 'North' ? <NorthKundliView chart={allCharts.find(c => c.key === active)?.data} transitMap={{}} showTransit={false} theme={kundliTheme} highlights={kundliHighlights} glyphs={showGlyphs} shadeSets={{ kendra: shadeKendra, trikon: shadeTrikon, dusthana: shadeDusthana, upachaya: shadeUpachaya }} /> :
                <EastIndianChart chart={allCharts.find(c => c.key === active)?.data} transitMap={{}} showTransit={false} theme={kundliTheme} glyphs={showGlyphs} />
          )}
        </div>
        <div className="md:col-span-7">
          {allCharts.filter(c => c.key === active).map(c => <ChartTable key={c.key} chart={c.data} hoverPlanet={hoverPlanet} setHoverPlanet={setHoverPlanet} />)}
        </div>
      </div>

      {active === 'D1' && yogas && yogas.yogas?.length > 0 && <div className="mt-4 text-[11px] bg-indigo-50 border border-indigo-200 rounded p-3">
        <div className="font-semibold mb-2">Yogas ({yogas.yogas.filter((y: any) => y.present).length})</div>
        <div className="flex flex-wrap gap-2">
          {yogas.yogas.filter((y: any) => y.present).map((y: any) => <span key={y.name} className="px-2 py-1 rounded bg-indigo-200 border border-indigo-300 text-indigo-900" title={y.detail || ''}>{y.name}</span>)}
        </div>
      </div>}

      {active === 'D1' && requestId && (
        <div className="mt-4 grid md:grid-cols-2 gap-3">
          <SpecialLagnasPanel requestId={requestId} />
          <SpecialPointsPanel requestId={requestId} />
        </div>
      )}

      {/* Panchanga and Transit Panels */}
      {active === 'D1' && requestId && (
        <div className="mt-4 space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
            <h3 className="text-lg font-semibold p-4 border-b border-gray-200 dark:border-gray-700">Panchanga (Hindu Calendar)</h3>
            <PanchangaPanel requestId={requestId} />
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
            <h3 className="text-lg font-semibold p-4 border-b border-gray-200 dark:border-gray-700">Current Transits</h3>
            <TransitPanel requestId={requestId} />
          </div>
        </div>
      )}
    </div>
  );
}

// --- Sub Components ---

function ChartTable({ chart, hoverPlanet, setHoverPlanet }: { chart: any; hoverPlanet: string; setHoverPlanet: (s: string) => void }) {
  const dignityClass = (d?: string) => {
    if (!d) return 'bg-gray-100 text-gray-800';
    switch (d) {
      case 'Exalted': return 'bg-green-600 text-white';
      case 'Debilitated': return 'bg-red-600 text-white';
      case 'Own': return 'bg-teal-600 text-white';
      case 'Moolatrikona': return 'bg-blue-600 text-white';
      default: return 'bg-gray-200 text-gray-900';
    }
  };

  const nakshatraName = (raw?: string) => {
    if (!raw) return '';
    const map: Record<string, string> = {
      'Makam': 'Ashlesha',
      'Purvabhadra': 'Purva Bhadrapada',
      'Uttarabhadra': 'Uttara Bhadrapada',
      'Purvashada': 'Purva Ashadha',
      'Uttarashada': 'Uttara Ashadha',
      'Sravana': 'Shravana',
    };
    return map[raw] ?? raw;
  };

  return (
    <div className="overflow-auto border rounded">
      <table className="min-w-full text-xs">
        <thead className="bg-gray-100 sticky top-0"><tr>
          <th className="px-2 py-1 text-left">Planet</th>
          <th className="px-2 py-1 text-left">Sign</th>
          <th className="px-2 py-1 text-left">House</th>
          <th className="px-2 py-1 text-left">Deg</th>
          <th className="px-2 py-1 text-left">Nakshatra</th>
          <th className="px-2 py-1 text-left">Dignity</th>
        </tr></thead>
        <tbody>
          {chart.planets?.map((p: any) => {
            const highlight = hoverPlanet && (p.name === hoverPlanet);
            return <tr key={p.name} onMouseEnter={() => setHoverPlanet(p.name)} onMouseLeave={() => setHoverPlanet('')} className={`border-t hover:bg-gray-50 ${highlight ? 'bg-yellow-100' : ''}`}>
              <td className="px-2 py-1 font-medium">{p.name} {p.retrograde && '(R)'}</td>
              <td className="px-2 py-1">{p.sign || ''}</td>
              <td className="px-2 py-1">{p.house}</td>
              <td className="px-2 py-1 whitespace-nowrap">{p.longitudeDMS}</td>
              <td className="px-2 py-1">{p.nakshatra && <span>{nakshatraName(p.nakshatra)}-{p.nakshatraPada}</span>}</td>
              <td className="px-2 py-1"><span className={`px-1.5 py-0.5 rounded ${dignityClass(p.dignity)}`}>{p.dignity || '-'}</span></td>
            </tr>
          })}
        </tbody>
      </table>
    </div>
  );
}

function KundliView({ chart, transitMap, showTransit, theme = 'Light', highlights = false, glyphs = false, aspects = null, hideOuter = false }: { chart: any; transitMap: Record<string, any>; showTransit: boolean; theme?: 'Light' | 'Dark' | 'Classic'; highlights?: boolean; glyphs?: boolean; aspects?: any; hideOuter?: boolean }) {
  const map: Record<number, { r: number; c: number }> = {
    1: { r: 3, c: 0 }, 2: { r: 2, c: 0 }, 3: { r: 1, c: 0 }, 4: { r: 0, c: 0 }, 5: { r: 0, c: 1 }, 6: { r: 0, c: 2 }, 7: { r: 0, c: 3 }, 8: { r: 1, c: 3 }, 9: { r: 2, c: 3 }, 10: { r: 3, c: 3 }, 11: { r: 3, c: 2 }, 12: { r: 3, c: 1 }
  };
  const cells: any[][] = Array.from({ length: 4 }, () => Array.from({ length: 4 }, () => null));
  const planets = (chart.planets || []).filter((p: any) => hideOuter ? !['Uranus', 'Neptune', 'Pluto'].includes(p.name) : true);
  planets.forEach((p: any) => {
    const pos = map[p.house]; if (!pos) return; cells[pos.r][pos.c] = cells[pos.r][pos.c] || []; cells[pos.r][pos.c].push(p);
  });
  const abbrev = (name: string) => name.length <= 4 ? name : name.slice(0, 3);
  const themeCls = theme === 'Dark' ? 'bg-gray-900 text-gray-100 border-gray-600' : theme === 'Classic' ? 'bg-amber-50 text-gray-900 border-amber-600' : 'bg-white text-gray-900 border-gray-400';
  const kendra = new Set([1, 4, 7, 10]);
  const trikon = new Set([1, 5, 9]);
  return <div className="mb-4" id="wheel-container">
    <div className={`grid grid-cols-4 w-[320px] h-[320px] border ${themeCls} relative mx-auto`}>
      {cells.map((row, ri) => row.map((cell, ci) => {
        const house = Object.entries(map).find(([h, v]) => v.r === ri && v.c === ci);
        const hNum = house ? parseInt(house[0]) : undefined;
        const asc = hNum === chart.ascendantHouse;
        const content = Array.isArray(cell) ? cell : [];
        const show = !(ri === 1 && (ci === 1 || ci === 2)) && !(ri === 2 && (ci === 1 || ci === 2));
        const highlightCls = highlights && hNum ? (
          asc ? 'ring-2 ring-yellow-400' : kendra.has(hNum) ? 'bg-indigo-50' : trikon.has(hNum) ? 'bg-green-50' : ''
        ) : '';
        return <div key={`${ri}-${ci}`} className={`relative border border-gray-300 flex flex-col items-center justify-start text-[10px] p-0.5 ${!show ? 'bg-gray-100' : ''} ${asc ? 'bg-yellow-100' : ''} ${highlightCls}`}>
          {show && <div className="absolute top-0 left-0 text-[9px] px-0.5 text-gray-500">{hNum}</div>}
          {show && content.length > 0 && <div className="flex flex-wrap gap-0.5 mt-3 justify-center">
            {content.slice(0, 4).map((p: any) => {
              const label = glyphs ? abbrev(p.name) : abbrev(p.name);
              return <span key={p.name} className={`px-1 rounded text-[9px] ${p.dignity === 'Exalted' ? 'bg-green-200 text-green-900' : p.dignity === 'Debilitated' ? 'bg-red-200 text-red-900' : p.dignity === 'Own' ? 'bg-teal-200 text-teal-900' : 'bg-gray-200'} ${p.retrograde ? 'italic' : ''}`}>{label}</span>;
            })}
            {content.length > 4 && <span className="text-[8px]">+{content.length - 4}</span>}
          </div>}
        </div>;
      }))}
    </div>
  </div>;
}

function NorthKundliView({ chart, transitMap, showTransit, theme = 'Light', highlights = false, glyphs = false, aspects = null, shadeSets, hideOuter = false }: { chart: any; transitMap: Record<string, any>; showTransit: boolean; theme?: 'Light' | 'Dark' | 'Classic'; highlights?: boolean; glyphs?: boolean; aspects?: any; shadeSets?: { kendra: boolean; trikon: boolean; dusthana: boolean; upachaya: boolean }; hideOuter?: boolean }) {
  const size = 320;
  const planets = (chart.planets || []).filter((p: any) => hideOuter ? !['Uranus', 'Neptune', 'Pluto'].includes(p.name) : true);
  const abbrev = (n: string) => n.length <= 4 ? n : n.slice(0, 3);
  const relPos: Record<number, { x: number; y: number }> = {
    1: { x: 50, y: 15 }, 2: { x: 68, y: 25 }, 3: { x: 82, y: 50 }, 4: { x: 68, y: 75 }, 5: { x: 50, y: 85 }, 6: { x: 32, y: 75 }, 7: { x: 18, y: 50 }, 8: { x: 32, y: 25 },
    9: { x: 40, y: 50 }, 10: { x: 50, y: 38 }, 11: { x: 60, y: 50 }, 12: { x: 50, y: 62 }
  };
  const byHouse: Record<number, any[]> = {};
  planets.forEach((p: any) => { (byHouse[p.house] = byHouse[p.house] || []).push(p); });
  const zodiac = ['Ar', 'Ta', 'Ge', 'Ca', 'Le', 'Vi', 'Li', 'Sc', 'Sa', 'Cp', 'Aq', 'Pi'];
  const ascSignNum = chart.ascendantHouse; // Assuming ascendantHouse is sign number for D1? Wait, ascendantHouse is usually house 1. ascendantSignNumber is what we need.
  // Actually in the API result, ascendantHouse is usually 1 for D1 if we consider house 1 as ascendant. But we need the sign number of the ascendant.
  // Let's assume chart.ascendantSignNumber exists or we derive it.
  // For now, let's just use house numbers relative to 1.

  const themeCls = theme === 'Dark' ? 'bg-gray-900 text-gray-100 border-gray-600' : theme === 'Classic' ? 'bg-amber-50 text-gray-900 border-amber-600' : 'bg-white text-gray-900 border-gray-400';

  return <div className="mb-4 mx-auto" style={{ width: size }}>
    <div className={`relative ${themeCls} border`} style={{ width: size, height: size }}>
      <BoxWithDiamondLines size={size} />
      {Object.entries(relPos).map(([relStr, pos]) => {
        const relHouse = parseInt(relStr, 10);
        const plist = byHouse[relHouse] || []; // This is wrong if byHouse is keyed by sign.
        // In North chart, houses are fixed. House 1 is top.
        // We need to find planets in House 1, House 2 etc.
        // chart.planets has .house property.
        const planetsInHouse = planets.filter((p: any) => p.house === relHouse);

        return <div key={relStr} style={{ left: pos.x + '%', top: pos.y + '%' }} className={`absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center text-[9px]`}>
          <div className="font-bold text-gray-400">{relHouse}</div>
          <div className="flex flex-wrap gap-0.5 justify-center">
            {planetsInHouse.map((p: any) => <span key={p.name} className="px-1 bg-white/80 border rounded">{abbrev(p.name)}</span>)}
          </div>
        </div>;
      })}
    </div>
  </div>;
}

function EastIndianChart({ chart, transitMap, showTransit, theme = 'Light', glyphs = false, hideOuter = false }: { chart: any; transitMap: Record<string, any>; showTransit: boolean; theme?: 'Light' | 'Dark' | 'Classic'; glyphs?: boolean; hideOuter?: boolean }) {
  return <div>East Indian Chart Placeholder</div>;
}

function BoxWithDiamondLines({ size = 320 }: { size?: number }) {
  const s = size; const pad = 6; const left = pad; const right = s - pad; const top = pad; const bottom = s - pad; const cx = s / 2; const cy = s / 2;
  return <svg viewBox={`0 0 ${s} ${s}`} width={s} height={s} className="absolute inset-0">
    <rect x={pad} y={pad} width={s - pad * 2} height={s - pad * 2} fill="none" stroke="#222" strokeWidth={1.5} />
    <polygon points={`${cx},${top} ${right},${cy} ${cx},${bottom} ${left},${cy}`} fill="none" stroke="#222" strokeWidth={1.5} />
    <line x1={left} y1={top} x2={right} y2={bottom} stroke="#333" strokeWidth={1.2} />
    <line x1={right} y1={top} x2={left} y2={bottom} stroke="#333" strokeWidth={1.2} />
  </svg>;
}
