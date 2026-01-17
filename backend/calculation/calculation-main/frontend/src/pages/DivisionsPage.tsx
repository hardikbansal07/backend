import React from 'react';
import DivisionalChartsPage from '../components/DivisionalChartsPage';

export default function DivisionsPage({ result, onClose }: { result: any; onClose: ()=>void }){
  return (
    <div className="fixed inset-0 bg-white/95 z-50 p-6 overflow-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold">Divisional Charts</h1>
        <div className="flex items-center gap-2">
          <button onClick={onClose} className="px-3 py-1 rounded bg-gray-200 text-gray-800">Close</button>
        </div>
      </div>
      <div>
        <DivisionalChartsPage result={result} />
      </div>
    </div>
  );
}
