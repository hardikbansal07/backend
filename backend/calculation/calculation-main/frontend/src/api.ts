import axios from 'axios';

// Type augmentation for Vite env to satisfy TS where missing
// (lightweight – avoids needing global d.ts if not present)
interface ImportMetaEnv { VITE_API_BASE?: string }
interface ImportMeta { env: ImportMetaEnv }

// Access env with any cast to avoid issues if Vite types not included
const base = ((import.meta as any).env?.VITE_API_BASE as string) || '';
export const api = axios.create({ baseURL: base });

// Simple in-memory ETag store keyed by method+url+sortedParams (no body caching yet)
const etagCache: Record<string, string> = {};
const dataCache: Record<string, any> = {};
// Axios request interceptor to attach If-None-Match and Authorization
api.interceptors.request.use(cfg => {
  try {
    // Add Authorization header if user is logged in
    const storedUser = localStorage.getItem('astro_user');
    if (storedUser) {
      const userData = JSON.parse(storedUser);
      if (userData.token) {
        (cfg.headers as any) = (cfg.headers as any) || {};
        (cfg.headers as any)['Authorization'] = `Bearer ${userData.token}`;
      }
    }

    // Add ETag handling for GET requests
    if (cfg.method?.toUpperCase() === 'GET') {
      const u = cfg.baseURL?.replace(/\/$/, '') + (cfg.url || '');
      const params = cfg.params ? Object.keys(cfg.params).sort().map(k => k + '=' + cfg.params[k]).join('&') : '';
      const key = cfg.method + ':' + u + '?' + params;
      const et = etagCache[key];
      if (et) {
        // Ensure headers is mutable AxiosHeaders
        (cfg.headers as any) = (cfg.headers as any) || {};
        (cfg.headers as any)['If-None-Match'] = et;
      }
      (cfg as any)._etagKey = key;
    }
  } catch { }
  return cfg;
});
// Response interceptor to store new ETags / handle 304 gracefully
api.interceptors.response.use(res => {
  try {
    const key = (res.config as any)._etagKey; const et = res.headers?.['etag'] || res.headers?.['ETag'];
    if (key && et) { etagCache[key] = et; }
    if (key) { dataCache[key] = res.data; }
  } catch { }
  return res;
}, err => {
  try {
    const res = err.response;
    if (res && res.status === 304) {
      const key = (res.config as any)._etagKey;
      if (key && etagCache[key]) {
        const cachedData = dataCache[key];
        const headers = { ...(res.headers || {}), 'x-cached': '1' };
        return Promise.resolve({ ...res, data: cachedData, status: 200, statusText: 'OK (cached 304)', headers });
      }
    }
  } catch { }
  return Promise.reject(err);
});

export interface HoroscopeRequest {
  birthDateTime: string;
  location: { place?: string; tzOffset: number; latitude?: number; longitude?: number };
  language?: string;
  divisionalFactors?: number[];
  // Calculation type: 'drik' (default library drik) or 'ss' (Surya Siddhanta)
  calcType?: 'drik' | 'ss';
  sendToAgent?: boolean;
  sendToAgentMode?: 'summary' | 'bundle' | 'full';
  ayanamsaMode?: string;
  houseSystem?: string;
}

export async function createHoroscope(req: HoroscopeRequest) {
  const res = await api.post('/api/horoscope', req);
  return res.data;
}

export async function fetchDhasa(id: string, includeAntardhasa: boolean = true, depth: number = 2, fullTree: boolean = false, maxNodes: number = 2000, raw: boolean = true, rawLimit?: number) {
  const params: any = { request_id: id, limit: 120, include_antardhasa: includeAntardhasa, depth, full_tree: fullTree, max_nodes: maxNodes, raw };
  if (typeof rawLimit === 'number') params.raw_limit = rawLimit;
  const res = await api.get('/api/dhasa/vimsottari', { params });
  return res.data;
}
export async function fetchCharaDasha(id: string, includeAntardhasa: boolean = true, method: number = 1) {
  const res = await api.get('/api/dhasa/chara', { params: { request_id: id, limit: 120, include_antardhasa: includeAntardhasa, method } });
  return res.data as { requestId: string; periods: { dhasaRasi: string; bhuktiRasi?: string; start: string; durationYears?: number }[] };
}
export async function fetchSthiraDasha(id: string, includeAntardhasa = true) {
  const res = await api.get('/api/dhasa/sthira', { params: { request_id: id, include_antardhasa: includeAntardhasa } });
  return res.data as { requestId: string; system: string; periods: { dhasaRasi: string; bhuktiRasi?: string; start: string; durationYears?: number }[] };
}
export async function fetchNarayanaDasha(id: string, includeAntardhasa = true, divisional: number = 1, varsha: boolean = false, years: number = 1) {
  const res = await api.get('/api/dhasa/narayana', { params: { request_id: id, include_antardhasa: includeAntardhasa, divisional, varsha, years } });
  return res.data as { requestId: string; system: string; periods: { dhasaRasi: string; bhuktiRasi?: string; start: string; durationYears?: number }[] };
}
export async function fetchDrigDasha(id: string, includeAntardhasa = true) {
  const res = await api.get('/api/dhasa/drig', { params: { request_id: id, include_antardhasa: includeAntardhasa } });
  return res.data as { requestId: string; system: string; periods: { dhasaRasi: string; bhuktiRasi?: string; start: string; durationYears?: number }[] };
}
export async function fetchYogardhaDasha(id: string, includeAntardhasa = true, divisional: number = 1, years: number = 1) {
  const res = await api.get('/api/dhasa/yogardha', { params: { request_id: id, include_antardhasa: includeAntardhasa, divisional, years } });
  return res.data as { requestId: string; system: string; periods: { dhasaRasi: string; bhuktiRasi?: string; start: string; durationYears?: number }[] };
}
export async function fetchParyaayaDasha(id: string, includeAntardhasa = true, divisional: number = 6, tribhagi: boolean = false) {
  const res = await api.get('/api/dhasa/paryaaya', { params: { request_id: id, include_antardhasa: includeAntardhasa, divisional, tribhagi } });
  return res.data as { requestId: string; system: string; periods: { dhasaRasi: string; bhuktiRasi?: string; start: string; durationYears?: number }[] };
}
export async function fetchBrahmaDasha(id: string, includeAntardhasa = true, divisional: number = 1, years: number = 1) {
  const res = await api.get('/api/dhasa/brahma', { params: { request_id: id, include_antardhasa: includeAntardhasa, divisional, years } });
  return res.data as { requestId: string; system: string; periods: { dhasaRasi: string; bhuktiRasi?: string; start: string; durationYears?: number }[] };
}
export async function fetchMandookaDasha(id: string, includeAntardhasa = true, divisional: number = 1) {
  const res = await api.get('/api/dhasa/mandooka', { params: { request_id: id, include_antardhasa: includeAntardhasa, divisional } });
  return res.data as { requestId: string; system: string; periods: { dhasaRasi: string; bhuktiRasi?: string; start: string; durationYears?: number }[] };
}
export async function fetchSudasaDasha(id: string, includeAntardhasa = true, divisional: number = 1) {
  const res = await api.get('/api/dhasa/sudasa', { params: { request_id: id, include_antardhasa: includeAntardhasa, divisional } });
  return res.data as { requestId: string; system: string; periods: { dhasaRasi: string; bhuktiRasi?: string; start: string; durationYears?: number }[] };
}
export async function fetchKalachakraDasha(id: string, includeAntardhasa = true, start: number | string = 1, starOffset: number = 1) {
  const res = await api.get('/api/dhasa/kalachakra', { params: { request_id: id, include_antardhasa: includeAntardhasa, start, star_offset: starOffset } });
  return res.data as { requestId: string; system: string; periods: { dhasaRasi: string; bhuktiRasi?: string; start: string; durationYears?: number }[] };
}
export async function fetchNavamsaDasha(id: string, includeAntardhasa = true, divisional: number = 9) {
  const res = await api.get('/api/dhasa/navamsa', { params: { request_id: id, include_antardhasa: includeAntardhasa, divisional } });
  return res.data as { requestId: string; system: string; periods: { dhasaRasi: string; bhuktiRasi?: string; start: string; durationYears?: number }[] };
}
export async function fetchTrikonaDasha(id: string, includeAntardhasa = true, divisional: number = 1) {
  const res = await api.get('/api/dhasa/trikona', { params: { request_id: id, include_antardhasa: includeAntardhasa, divisional } });
  return res.data as { requestId: string; system: string; periods: { dhasaRasi: string; bhuktiRasi?: string; start: string; durationYears?: number }[] };
}
export async function fetchChakraDasha(id: string, includeAntardhasa = false, divisional: number = 1, years: number = 1) {
  const res = await api.get('/api/dhasa/chakra', { params: { request_id: id, include_antardhasa: includeAntardhasa, divisional, years } });
  return res.data as { requestId: string; system: string; periods: { dhasaRasi: string; bhuktiRasi?: string; start: string; durationYears?: number }[] };
}
export async function fetchKendraadhiRasiDasha(id: string, includeAntardhasa = true, divisional: number = 1) {
  const res = await api.get('/api/dhasa/kendraadhi_rasi', { params: { request_id: id, include_antardhasa: includeAntardhasa, divisional } });
  return res.data as { requestId: string; system: string; periods: { dhasaRasi: string; bhuktiRasi?: string; start: string; durationYears?: number }[] };
}
export async function fetchRasiDhasaShoola(id: string, includeAntardhasa = true) {
  const res = await api.get('/api/dhasa/rasi/shoola', { params: { request_id: id, include_antardhasa: includeAntardhasa } });
  return res.data;
}
export async function fetchGrahaDhasa(id: string, system: string, includeAntardhasa = true, limit = 120) {
  const res = await api.get(`/api/dhasa/graha/${system}`, { params: { request_id: id, include_antardhasa: includeAntardhasa, limit } });
  return res.data;
}

export async function fetchPanchanga(id: string) {
  const res = await api.get('/api/panchanga', { params: { request_id: id } });
  return res.data;
}
export interface TransitPanchangaOpts {
  dateTime?: string; // ISO local e.g. 2025-11-13T18:51:27
  latitude?: number;
  longitude?: number;
  tzOffset?: number; // hours
  ayanamsaMode?: string;
  calcType?: 'drik' | 'ss';
}
export async function fetchTransitPanchanga(id: string, opts?: TransitPanchangaOpts) {
  const params: any = { request_id: id };
  if (opts?.dateTime) params.dateTime = opts.dateTime;
  if (typeof opts?.latitude === 'number') params.latitude = opts.latitude;
  if (typeof opts?.longitude === 'number') params.longitude = opts.longitude;
  if (typeof opts?.tzOffset === 'number') params.tzOffset = opts.tzOffset;
  if (opts?.ayanamsaMode) params.ayanamsaMode = opts.ayanamsaMode;
  if (opts?.calcType) params.calcType = opts.calcType;
  const res = await api.get('/api/panchanga/transit', { params });
  return res.data;
}
export async function fetchTransit(id: string) {
  const res = await api.get('/api/transit', { params: { request_id: id } });
  return res.data;
}
export async function fetchNakshatras() {
  const res = await api.get('/api/nakshatras');
  return res.data.items as string[];
}
export async function matchCompat(body: { maleNakshatra: string; femaleNakshatra: string; system?: string }) {
  const res = await api.post('/api/match', body);
  return res.data;
}

// Additional endpoints integration
export async function fetchHealth() {
  const res = await api.get('/api/health');
  return res.data as { status: string; time: string };
}
export async function fetchHoroscope(id: string) {
  if (!id) throw new Error('id required');
  const res = await api.get(`/api/horoscope/${id}`);
  return res.data;
}
export async function deleteHoroscope(id: string) {
  const res = await api.delete(`/api/horoscope/${id}`);
  return res.data as { requestId: string; deleted: boolean };
}
export interface AgentEvent { request_id: string; status?: string; success?: boolean; created?: string; error?: string; payloadSize?: number; attempts?: number }
export interface AgentEventsEnvelope { events: AgentEvent[]; limit: number; offset: number }
export async function fetchAgentEvents(limit = 25, offset = 0) {
  const res = await api.get('/api/agent/events', { params: { limit, offset } });
  const env: AgentEventsEnvelope = { events: res.data?.events || [], limit: res.data?.limit || limit, offset: res.data?.offset || offset };
  return env;
}
export async function fetchAgentEventPayload(requestId: string) {
  const res = await api.get(`/api/agent/events/${requestId}/payload`);
  return res.data;
}
export interface AgentPayloadInfo { requestId: string; sizeBytes: number; sizeKB: number; approxSizeKB: string; modeDetected: string; topLevelKeyCount: number; topLevelKeys: string[] }
export async function fetchAgentEventPayloadInfo(requestId: string) {
  const res = await api.get(`/api/agent/events/${requestId}/payload_info`);
  return res.data as AgentPayloadInfo;
}

// List horoscopes
export interface StoredRequestItem { requestId: string; generatedAt?: string; charts?: number | null; hasDeep?: boolean }
export async function fetchHoroscopeList(limit = 100) {
  const res = await api.get('/api/horoscope', { params: { limit } });
  return (res.data?.items || []) as StoredRequestItem[];
}
export async function relayAgent(requestId: string) {
  const res = await api.post('/api/agent/relay', { requestId });
  return res.data;
}
export async function retryAgent(requestId: string) {
  const res = await api.post(`/api/agent/retry/${requestId}`);
  return res.data;
}
export async function fetchDebugHoroscope(requestId: string) {
  const res = await api.get(`/api/debug/horoscope/${requestId}`);
  return res.data;
}
export interface PlaceItem { label: string; latitude: number; longitude: number; tzOffsetHours: number; country?: string }
export async function searchPlaces(q: string) {
  const res = await api.get('/api/places', { params: { q, limit: 8 } });
  return (res.data?.items || []) as PlaceItem[];
}
export async function fetchRenderedChart(requestId: string, opts?: { chart?: string; style?: string; size?: number; format?: string }) {
  const params = { chart: opts?.chart || 'D1', style: opts?.style || 'South', format: opts?.format || 'svg', size: opts?.size || 400 };
  const res = await api.get(`/api/horoscope/${requestId}/render`, { params, responseType: 'text' as const });
  // Return object with svg and cached flag so caller can decide whether to re-use existing DOM
  const cached = (res.headers?.['x-cached'] === '1') || (res.headers?.['X-Cached'] === '1');
  return { svg: res.data as string, cached: !!cached, etag: res.headers?.['etag'] || res.headers?.['ETag'] } as { svg: string; cached: boolean; etag?: string };
}
export async function fetchAspects(requestId: string) {
  const res = await api.get('/api/aspects', { params: { request_id: requestId } });
  return res.data as { requestId: string; edges: { source: string; target: string; sourceHouse: number; targetHouse: number; aspectType: string; note?: string }[]; planetHouseMap: Record<string, number> };
}
export async function fetchStrength(requestId: string) {
  const res = await api.get('/api/strength', { params: { request_id: requestId } });
  return res.data as { requestId: string; counts: Record<string, number>; retrograde: string[]; dignities: Record<string, string[]> };
}
export async function fetchYogas(
  requestId: string,
  mode: 'basic' | 'full' = 'full',
  language: string = 'en',
  filterPlanet?: string,
  debug: boolean = false
) {
  const params: any = { request_id: requestId, mode, language };
  if (filterPlanet && filterPlanet !== 'All') params.filterPlanet = filterPlanet;
  if (debug) params.debug = true;
  const res = await api.get('/api/yogas', { params });
  return res.data as { requestId: string; yogas: { name: string; present: boolean; planets: string[]; detail?: string }[]; debug?: any };
}
export async function fetchSummary(requestId: string) {
  const res = await api.get('/api/summary', { params: { request_id: requestId } });
  return res.data as { requestId: string; strength?: any; yogas: any[]; aspectsCount: number; retrograde: string[] };
}
export async function fetchExportText(requestId: string) {
  const res = await api.get(`/api/export/text/${requestId}`, { responseType: 'text' });
  return res.data as string;
}

// Deep Strength (Ashtakavarga, Shadbala, etc.)
export interface DeepStrengthResponse {
  requestId: string;
  ashtakavarga?: any;
  shadbala?: any;
  bhavaBala?: any;
  vimsopaka?: any;
  avasthas?: any;
  ishtaPhala?: number[];
  aspects?: any;
  rashmi?: { subha?: number[]; uccha?: number[] };
  meta?: { generatedAt?: string; ayanamsaMode?: string };
}
export async function fetchDeepStrength(requestId: string, includeAspects = false, includePrastara = false) {
  const res = await api.get('/api/deepstrength', { params: { request_id: requestId, includeAspects, includePrastara } });
  return res.data as DeepStrengthResponse;
}

export async function fetchBundle(requestId: string, includeSummary = true) {
  const res = await api.get('/api/bundle', { params: { request_id: requestId, includeSummary: true } });
  return res.data as BundleResponse;
}

// Arudha Padas
export async function fetchArudha(requestId: string) {
  const res = await api.get('/api/arudha', { params: { request_id: requestId } });
  return res.data as { requestId: string; bhavaArudhas: Record<string, string>; bhavaArudhasD9?: Record<string, string> | null; menu?: Record<string, string[]> };
}

// Alternative (Chandra / Surya Lagna) charts
export async function fetchAltCharts(requestId: string) {
  const res = await api.get('/api/alt_charts', { params: { request_id: requestId } });
  return res.data as { requestId: string; chandra?: any; surya?: any };
}

// Bhava Chakra
export async function fetchBhavaChakra(requestId: string) {
  const res = await api.get('/api/bhava_chakra', { params: { request_id: requestId } });
  return res.data as { requestId: string; houses?: { house: number; start: string; mid: string; end: string; planets: string[] }[] };
}

// SS-like consolidated endpoints
export interface SSLikeViewResponse {
  requestId: string;
  chart?: any;
  panelRows?: { Body: string; Longitude: string; Nakshatra: string; Pada: number | string; Rasi: string; Navamsa?: string }[];
  vargas?: { factor: number; key?: string; rows: { Body: string; Longitude: string; Nakshatra: string; Pada: number | string; Rasi: string; Navamsa?: string }[] }[];
  extendedPoints?: { name: string; sign?: string; longitudeDMS?: string; nakshatra?: string; pada?: number; navamsa?: string }[];
}
export async function fetchSSLikeView(requestId: string) {
  const res = await api.get('/api/horoscope/sslike/view', { params: { request_id: requestId } });
  return res.data as SSLikeViewResponse;
}
export type SSLikeFlatRow = { Body: string; Longitude: string; Nakshatra: string; Pada: number | string; Rasi: string; Navamsa?: string };
export async function fetchSSLikeFlat(requestId: string, factor: number = 1) {
  const res = await api.get('/api/horoscope/sslike/flat', { params: { request_id: requestId, factor } });
  return res.data as { requestId: string; factor: number; rows: SSLikeFlatRow[] };
}

// Special Points (extended upagrahas + yogi/avayogi)
export async function fetchSpecialPoints(requestId: string) {
  const res = await api.get('/api/special_points', { params: { request_id: requestId } });
  return res.data as any;
}

// Outer planets config
export async function getOuterPlanetsEnabled() {
  const res = await api.get('/api/config/outer_planets');
  return res.data as { enabled: boolean };
}
export async function setOuterPlanetsEnabled(enabled: boolean) {
  const res = await api.post('/api/config/outer_planets', null, { params: { enabled } });
  return res.data as { enabled: boolean };
}

// House systems list
export interface HouseSystemItem { key: string | number; label: string }
export async function fetchHouseSystems() {
  const res = await api.get('/api/house_systems');
  return res.data as { items: HouseSystemItem[]; default: number };
}

export interface LanguageItem { label: string; code: string }
export async function fetchLanguages() {
  const res = await api.get('/api/languages');
  return (res.data?.items || []) as LanguageItem[];
}

// Timezone guess via backend nearest-city heuristic
export interface TimezoneGuess { timezone: string; offsetHours: number; observedOffsetHours: number; dst: boolean; approxDistanceKM: number; at: string }
export async function fetchTimezone(lat: number, lon: number, dt?: string) {
  const res = await api.get('/api/timezone', { params: { lat, lon, dt } });
  return res.data as TimezoneGuess;
}

// Bootstrap API
export interface BundleResponse { requestId: string; horoscope?: any; yogas?: any; strength?: any; deepStrength?: any; summary?: any }
export interface BootstrapRequest { requestId?: string; createIfMissing?: boolean; bundle?: boolean; yogasMode?: 'basic' | 'full'; includeDeep?: boolean; includeDeepAspects?: boolean; includeDeepPrastara?: boolean; includeSummary?: boolean; horoscope?: HoroscopeRequest }
export interface BootstrapResponse { requestId: string; created: boolean; bundle?: BundleResponse }
export async function bootstrap(body: BootstrapRequest) { const res = await api.post('/api/bootstrap', body); return res.data as BootstrapResponse; }

export async function fetchAllDashas(id: string) {
  const endpoints: { key: string; url: string; params?: any }[] = [
    { key: 'vimsottari', url: '/api/dhasa/vimsottari', params: { request_id: id, limit: 60, include_antardhasa: true, depth: 2 } },
    { key: 'chara', url: '/api/dhasa/chara', params: { request_id: id, limit: 60, include_antardhasa: true, method: 1 } },
    { key: 'sthira', url: '/api/dhasa/sthira', params: { request_id: id, include_antardhasa: true } },
    { key: 'narayana', url: '/api/dhasa/narayana', params: { request_id: id, include_antardhasa: true } },
    { key: 'drig', url: '/api/dhasa/drig', params: { request_id: id, include_antardhasa: true } },
    { key: 'yogardha', url: '/api/dhasa/yogardha', params: { request_id: id, include_antardhasa: true } },
    { key: 'paryaaya', url: '/api/dhasa/paryaaya', params: { request_id: id, include_antardhasa: true } },
    { key: 'brahma', url: '/api/dhasa/brahma', params: { request_id: id, include_antardhasa: true } },
    { key: 'mandooka', url: '/api/dhasa/mandooka', params: { request_id: id, include_antardhasa: true } },
    { key: 'sudasa', url: '/api/dhasa/sudasa', params: { request_id: id, include_antardhasa: true } },
    { key: 'kalachakra', url: '/api/dhasa/kalachakra', params: { request_id: id, include_antardhasa: true } },
    { key: 'navamsa', url: '/api/dhasa/navamsa', params: { request_id: id, include_antardhasa: true } },
    { key: 'trikona', url: '/api/dhasa/trikona', params: { request_id: id, include_antardhasa: true } },
    { key: 'chakra', url: '/api/dhasa/chakra', params: { request_id: id, include_antardhasa: false } },
    { key: 'kendraadhi_rasi', url: '/api/dhasa/kendraadhi_rasi', params: { request_id: id, include_antardhasa: true } },
    { key: 'ashtottari', url: '/api/dhasa/graha/ashtottari', params: { request_id: id, limit: 60, include_antardhasa: true } },
    { key: 'yogini', url: '/api/dhasa/graha/yogini', params: { request_id: id, limit: 60, include_antardhasa: true } },
    { key: 'shodasottari', url: '/api/dhasa/graha/shodashottari', params: { request_id: id, limit: 60, include_antardhasa: true } },
    { key: 'dwadasottari', url: '/api/dhasa/graha/dwadasottari', params: { request_id: id, limit: 60, include_antardhasa: true } },
    { key: 'panchottari', url: '/api/dhasa/graha/panchottari', params: { request_id: id, limit: 60, include_antardhasa: true } },
    { key: 'shatabdika', url: '/api/dhasa/graha/shatabdika', params: { request_id: id, limit: 60, include_antardhasa: true } },
    { key: 'chaturashiti_sama', url: '/api/dhasa/graha/chaturashiti_sama', params: { request_id: id, limit: 60, include_antardhasa: true } },
    { key: 'dwisaptati_sama', url: '/api/dhasa/graha/dwisaptati_sama', params: { request_id: id, limit: 60, include_antardhasa: true } },
    { key: 'shashtihayani', url: '/api/dhasa/graha/shashtihayani', params: { request_id: id, limit: 60, include_antardhasa: true } },
    { key: 'shoola', url: '/api/dhasa/rasi/shoola', params: { request_id: id, include_antardhasa: true } }
  ];
  const results: Record<string, any> = {};
  await Promise.all(endpoints.map(async ep => {
    try { const r = await api.get(ep.url, { params: ep.params }); results[ep.key] = r.data; } catch (e) { results[ep.key] = { error: true, detail: (e as any)?.message || 'error' }; }
  }));
  return results;
}

// --- New Features ---

// Tajaka (Annual)
export async function fetchTajakaAnnual(requestId: string, year: number) {
  const res = await api.get('/api/tajaka/annual', { params: { request_id: requestId, year } });
  return res.data;
}

export async function fetchTajakaYogas(requestId: string, year: number) {
  const res = await api.get('/api/tajaka/yogas', { params: { request_id: requestId, year } });
  return res.data;
}

export async function fetchAnnualDhasaMudda(requestId: string, year: number, includeAntardhasa: boolean = true) {
  const res = await api.get('/api/dhasa/annual/mudda', { params: { request_id: requestId, year, include_antardhasa: includeAntardhasa } });
  return res.data;
}

export async function fetchAnnualDhasaPatyayini(requestId: string, year: number, includeAntardhasa: boolean = true) {
  const res = await api.get('/api/dhasa/annual/patyayini', { params: { request_id: requestId, year, include_antardhasa: includeAntardhasa } });
  return res.data;
}

// Detailed Analysis
export async function fetchVaiseshikamsa(requestId: string) {
  const res = await api.get('/api/analyze/vaiseshikamsa', { params: { request_id: requestId } });
  return res.data;
}

export async function fetchSphuta(requestId: string) {
  const res = await api.get('/api/analyze/sphuta', { params: { request_id: requestId } });
  return res.data;
}

export async function fetchBhavaBala(requestId: string) {
  const res = await api.get('/api/analyze/bhavabala', { params: { request_id: requestId } });
  return res.data;
}

export async function fetchShadbala(requestId: string) {
  const res = await api.get('/api/analyze/shadbala', { params: { request_id: requestId } });
  return res.data;
}

export async function fetchAshtakavarga(requestId: string) {
  const res = await api.get('/api/analyze/ashtakavarga', { params: { request_id: requestId } });
  return res.data;
}

// Panchanga Calculation
export async function fetchPanchangaCalculate(dateTime: string, latitude: number, longitude: number, tzOffset: number) {
  const res = await api.get('/api/panchanga/calculate', { params: { dateTime, latitude, longitude, tzOffset } });
  return res.data;
}

// Vertex AI Chat
export async function chatWithAstrologer(query: string, history: any[] = []) {
  const res = await api.post('/api/v1/ai/chat', { query, history });
  return res.data;
}
// Blogs
export interface BlogItem {
  _id: string;
  title: string;
  short_description: string;
  image: string;
  category: string;
  author: string;
  created_at: string;
  content?: string; // Optional in list view
}

export interface PaginatedBlogs {
  items: BlogItem[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export async function fetchBlogs(page: number = 1, limit: number = 10) {
  const res = await api.get('/api/blogs', { params: { page, limit } });
  return res.data as PaginatedBlogs;
}

export async function fetchBlogDetail(id: string) {
  const res = await api.get(`/api/blogs/${id}`);
  return res.data as BlogItem;
}
