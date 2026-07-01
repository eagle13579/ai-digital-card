import { BrowserRouter as Router } from 'react-router-dom';
import { I18nProvider } from './i18n';
import { RTLProvider } from './i18n/RTLProvider';
import ErrorBoundary from './components/ErrorBoundary';
import AppRoutes from './router';

export default function App() {
  return (
    <ErrorBoundary>
      <I18nProvider>
        <RTLProvider>
          <Router>
            <div className="bg-neutral-bg min-h-screen text-on-surface select-none">
              <AppRoutes />
            </div>
          </Router>
        </RTLProvider>
      </I18nProvider>
    </ErrorBoundary>
  );
}
