import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchTajakaAnnual, fetchTajakaYogas, fetchAnnualDhasaMudda, fetchAnnualDhasaPatyayini } from '../api';

export function TajakaPanel({ requestId, birthYear }: { requestId: string; birthYear: number }) {
  const [year, setYear] = React.useState(new Date().getFullYear());
  const [dhasaType, setDhasaType] = React.useState<'mudda'|'patyayini'>('mudda');

  const { data: chart, isLoading: chartLoading } = useQuery({
    queryKey: ['tajakaAnnual', requestId, year],
    queryFn: () => fetchTajakaAnnual(requestId, year),
    enabled: !!requestId
  });

  const { data: yogas } = useQuery({
    queryKey: ['tajakaYogas', requestId, year],
    queryFn: () => fetchTajakaYogas(requestId, year),
    enabled: !!requestId
  });

  const { data: dhasa } = useQuery({
    queryKey: ['tajakaDhasa', requestId, year, dhasaType],
    queryFn: () => dhasaType === 'mudda' ? fetchAnnualDhasaMudda(requestId, year) : fetchAnnualDhasaPatyayini(requestId, year),
    enabled: !!requestId
  });

  return (
    <div className="space-y-6 p-4 bg-white rounded shadow">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold">Tajaka (Annual) Analysis</h2>
        <div className="flex items-center gap-2">
          <label className="text-sm">Year:</label>
          <input 
            type="number" 
            value={year} 
            onChange={e => setYear(parseInt(e.target.value))} 
            className="border rounded px-2 py-1 w-20"
          />
        </div>
      </div>

      {chartLoading && <div>Loading Annual Chart...</div>}

      {chart && (
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-medium mb-2">Annual Chart (Varshaphal)</h3>
            <div className="overflow-auto border rounded max-h-96">
              <table className="min-w-full text-xs">
                <thead className="bg-gray-100 sticky top-0">
                  <tr>
                    <th className="px-2 py-1 text-left">Planet</th>
                    <th className="px-2 py-1 text-left">Sign</th>
                    <th className="px-2 py-1 text-left">Deg</th>
                    <th className="px-2 py-1 text-left">House</th>
                  </tr>
                </thead>
                <tbody>
                  {chart.planets.map((p: any) => (
                    <tr key={p.name} className="border-t">
                      <td className="px-2 py-1 font-medium">{p.name}</td>
                      <td className="px-2 py-1">{p.sign}</td>
                      <td className="px-2 py-1">{p.longitudeDMS}</td>
                      <td className="px-2 py-1">{p.house}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-2 text-xs">
              <strong>Muntha:</strong> {chart.muntha?.sign} ({chart.muntha?.house}H)
            </div>
            <div className="mt-1 text-xs">
              <strong>Lord of Year:</strong> {chart.lord_of_year}
            </div>
          </div>

          <div>
            <h3 className="font-medium mb-2">Panchavargiya Bala</h3>
            <div className="overflow-auto border rounded max-h-60">
               <table className="min-w-full text-xs">
                <thead className="bg-gray-100 sticky top-0">
                  <tr>
                    <th className="px-2 py-1 text-left">Planet</th>
                    <th className="px-2 py-1 text-left">Total</th>
                    <th className="px-2 py-1 text-left">Strength</th>
                  </tr>
                </thead>
                <tbody>
                  {chart.panchavargiya_bala && Object.entries(chart.panchavargiya_bala).map(([k, v]: any) => (
                    <tr key={k} className="border-t">
                      <td className="px-2 py-1 capitalize">{k}</td>
                      <td className="px-2 py-1">{v.total?.toFixed(2)}</td>
                      <td className="px-2 py-1">{v.strength}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {yogas && yogas.yogas && (
        <div>
          <h3 className="font-medium mb-2">Tajaka Yogas</h3>
          <div className="flex flex-wrap gap-2">
            {yogas.yogas.map((y: any, i: number) => (
              <div key={i} className="border rounded p-2 text-xs bg-indigo-50 border-indigo-200">
                <div className="font-semibold">{y.name}</div>
                <div>{y.planets.join(' - ')}</div>
                <div className="text-gray-600">{y.detail}</div>
              </div>
            ))}
            {yogas.yogas.length === 0 && <div className="text-sm text-gray-500">No major yogas found.</div>}
          </div>
        </div>
      )}

      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-medium">Annual Dashas</h3>
          <select 
            value={dhasaType} 
            onChange={e => setDhasaType(e.target.value as any)}
            className="border rounded px-2 py-1 text-xs"
          >
            <option value="mudda">Mudda Dasha</option>
            <option value="patyayini">Patyayini Dasha</option>
          </select>
        </div>
        {dhasa && (
          <div className="overflow-auto border rounded max-h-60">
            <table className="min-w-full text-xs">
              <thead className="bg-gray-100 sticky top-0">
                <tr>
                  <th className="px-2 py-1 text-left">MD</th>
                  <th className="px-2 py-1 text-left">AD</th>
                  <th className="px-2 py-1 text-left">Start</th>
                  <th className="px-2 py-1 text-left">End</th>
                </tr>
              </thead>
              <tbody>
                {dhasa.periods.map((p: any, i: number) => (
                  <tr key={i} className="border-t">
                    <td className="px-2 py-1 font-medium">{p.dhasaLord}</td>
                    <td className="px-2 py-1">{p.antardashaLord || '-'}</td>
                    <td className="px-2 py-1">{p.start}</td>
                    <td className="px-2 py-1">{p.end}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
