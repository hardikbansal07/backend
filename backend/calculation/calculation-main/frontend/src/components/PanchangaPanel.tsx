import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchPanchanga, fetchTransitPanchanga } from '../api';

export function PanchangaPanel({ requestId }: { requestId: string }) {
    const [showTransitDate, setShowTransitDate] = React.useState(false);
    const [transitDate, setTransitDate] = React.useState('');

    const { data, isLoading, error } = useQuery({
        queryKey: ['panchanga', requestId, showTransitDate, transitDate],
        queryFn: async () => {
            if (showTransitDate && transitDate) {
                return fetchTransitPanchanga(requestId, { dateTime: transitDate });
            }
            return fetchPanchanga(requestId);
        },
        enabled: !!requestId
    });

    if (isLoading) return <div className="p-4 text-gray-500">Loading Panchanga...</div>;
    if (error) return <div className="p-4 text-red-500">Error: {(error as Error).message}</div>;
    if (!data) return <div className="p-4 text-gray-500">No data</div>;

    const calendar = data.calendar || data || {};

    // Group keys by category for better display
    const timeKeys = Object.keys(calendar).filter(k =>
        k.includes('Rise') || k.includes('Set') || k.includes('Muhurtham') || k.includes('Time')
    );

    const panchangaKeys = Object.keys(calendar).filter(k =>
        k.includes('Tithi') || k.includes('Nakshatra') || k.includes('Yoga') ||
        k.includes('Karana') || k.includes('Vaara') || k.includes('Paksha') ||
        k.includes('Maasa') || k.includes('Month')
    );

    const otherKeys = Object.keys(calendar).filter(k =>
        !timeKeys.includes(k) && !panchangaKeys.includes(k)
    );

    return (
        <div className="p-4 space-y-4">
            {/* Date Type Selector */}
            <div className="flex items-center gap-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-6">
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="radio"
                            checked={!showTransitDate}
                            onChange={() => setShowTransitDate(false)}
                            className="form-radio"
                        />
                        <span className="text-sm font-medium">Birth Chart Panchanga</span>
                    </label>

                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="radio"
                            checked={showTransitDate}
                            onChange={() => setShowTransitDate(true)}
                            className="form-radio"
                        />
                        <span className="text-sm font-medium">Transit Date Panchanga</span>
                    </label>
                </div>

                {showTransitDate && (
                    <input
                        type="datetime-local"
                        value={transitDate}
                        onChange={(e) => setTransitDate(e.target.value)}
                        className="px-3 py-1.5 border rounded-md text-sm dark:bg-gray-700 dark:border-gray-600"
                    />
                )}
            </div>

            {/* Panchanga Elements */}
            {panchangaKeys.length > 0 && (
                <div>
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 pb-2 border-b border-gray-200 dark:border-gray-700">
                        Panchanga Elements
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {panchangaKeys.map((key, idx) => {
                            const colors = [
                                'from-purple-50 to-purple-100 border-purple-200 dark:from-purple-900/20 dark:border-purple-800',
                                'from-blue-50 to-blue-100 border-blue-200 dark:from-blue-900/20 dark:border-blue-800',
                                'from-green-50 to-green-100 border-green-200 dark:from-green-900/20 dark:border-green-800',
                                'from-yellow-50 to-yellow-100 border-yellow-200 dark:from-yellow-900/20 dark:border-yellow-800',
                                'from-indigo-50 to-indigo-100 border-indigo-200 dark:from-indigo-900/20 dark:border-indigo-800',
                                'from-pink-50 to-pink-100 border-pink-200 dark:from-pink-900/20 dark:border-pink-800'
                            ];
                            const colorClass = colors[idx % colors.length];

                            return (
                                <div key={key} className={`p-3 bg-gradient-to-br ${colorClass} rounded-lg shadow-sm border`}>
                                    <h3 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">{key}</h3>
                                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{calendar[key]}</p>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Sun & Moon Timings */}
            {timeKeys.length > 0 && (
                <div>
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 pb-2 border-b border-gray-200 dark:border-gray-700">
                        Timings
                    </h4>
                    <div className="p-4 bg-gradient-to-r from-orange-50 via-yellow-50 to-blue-50 dark:from-orange-900/20 dark:via-yellow-900/20 dark:to-blue-900/20 rounded-lg shadow border border-orange-200 dark:border-orange-800">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            {timeKeys.map(key => (
                                <div key={key}>
                                    <span className="text-xs text-gray-600 dark:text-gray-400">{key}:</span>
                                    <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">{calendar[key]}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Other Info */}
            {otherKeys.length > 0 && (
                <div>
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 pb-2 border-b border-gray-200 dark:border-gray-700">
                        Additional Info
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {otherKeys.map(key => (
                            <div key={key} className="p-3 bg-gray-50 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                                <span className="text-xs text-gray-600 dark:text-gray-400">{key}:</span>
                                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{calendar[key]}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
