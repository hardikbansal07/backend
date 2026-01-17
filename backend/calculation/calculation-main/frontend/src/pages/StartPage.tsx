import React from 'react';
import { HoroscopeForm } from '../components/HoroscopeForm';
import { ChartsView } from '../components/ChartsView';
import { DhasaPanel } from '../components/DhasaPanel';
import { AnalysisPanel } from '../components/AnalysisPanel';
import { TajakaPanel } from '../components/TajakaPanel';
import DivisionalChartsPage from '../components/DivisionalChartsPage';

export default function StartPage() {
  const [result, setResult] = React.useState<any>(null);
  const [activeTab, setActiveTab] = React.useState<'charts'|'divisions'|'dhasas'|'analysis'|'tajaka'>('charts');

  const requestId = result?.meta?.requestId;
  const birthYear = result?.rasiChart?.year || new Date().getFullYear(); // Approximate if not in meta

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Vedic Astrology Dashboard</h1>
          {requestId && <div className="text-sm text-gray-500">Request ID: {requestId}</div>}
        </header>

        <HoroscopeForm onResult={setResult} />

        {result && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-1 overflow-x-auto">
              <div className="flex space-x-1">
                {(['charts', 'divisions', 'dhasas', 'analysis', 'tajaka'] as const).map(tab => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-2 rounded-md text-sm font-medium capitalize transition-colors ${
                      activeTab === tab 
                        ? 'bg-indigo-600 text-white shadow-sm' 
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            </div>

            <div className="min-h-[500px]">
              {activeTab === 'charts' && <ChartsView result={result} />}
              {activeTab === 'divisions' && <DivisionalChartsPage result={result} />}
              {activeTab === 'dhasas' && requestId && <DhasaPanel requestId={requestId} />}
              {activeTab === 'analysis' && requestId && <AnalysisPanel requestId={requestId} />}
              {activeTab === 'tajaka' && requestId && <TajakaPanel requestId={requestId} birthYear={birthYear} />}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
