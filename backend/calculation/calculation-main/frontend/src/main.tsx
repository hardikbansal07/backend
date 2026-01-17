import React from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './styles.css';
import StartPage from './pages/StartPage';
import HoroscopeNavbar from './components/HoroscopeNavbar';

const qc = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      refetchOnWindowFocus: false,
      retry: 1
    }
  }
});

function App() {
  return (
    <QueryClientProvider client={qc}>
      <div className="min-h-screen bg-gray-50">
        <HoroscopeNavbar />
        <div className="pt-16">
          <StartPage />
        </div>
      </div>
    </QueryClientProvider>
  );
}

const rootEl = document.getElementById('root');
if (rootEl) {
  createRoot(rootEl).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
