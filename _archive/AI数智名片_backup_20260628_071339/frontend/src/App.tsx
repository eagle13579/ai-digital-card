import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { I18nProvider } from './i18n';
import React, { Suspense, lazy } from 'react';
import ErrorBoundary from './components/ErrorBoundary';
import PageSkeleton from './components/LoadingSkeleton';
import Layout from './components/Layout';

const BusinessCardPageLazy = lazy(() => import('./pages/BusinessCardPage'));
const AnalyticsPageLazy = lazy(() => import('./pages/AnalyticsPage'));
const TeamPageLazy = lazy(() => import('./pages/TeamPage'));
const TeamSettingsLazy = lazy(() => import('./pages/TeamSettings'));
const PricingPageLazy = lazy(() => import('./pages/PricingPage'));
const PaymentCallbackLazy = lazy(() => import('./pages/PaymentCallback'));
const ABTestingPageLazy = lazy(() => import('./pages/ABTestingPage'));
const GDPRSettingsLazy = lazy(() => import('./pages/GDPRSettings'));

// 新多页面 SPA 架构页面
const DashboardPageLazy = lazy(() => import('./pages/DashboardPage'));
const CardEditorPageLazy = lazy(() => import('./pages/CardEditorPage'));
const SettingsPageLazy = lazy(() => import('./pages/SettingsPage'));
const NetworkPageLazy = lazy(() => import('./pages/NetworkPage'));
const MatchingPageLazy = lazy(() => import('./pages/MatchingPage'));
const ApiKeysPageLazy = lazy(() => import('./pages/ApiKeysPage'));

/**
 * 带骨架屏的懒加载包装
 * 根据页面类型显示对应的骨架屏
 */
function LazyPage({
  children,
  skeletonMode = 'card',
  skeletonCount = 3,
}: {
  children: React.ReactNode;
  skeletonMode?: 'card' | 'list' | 'detail';
  skeletonCount?: number;
}) {
  return (
    <Suspense
      fallback={
        <PageSkeleton
          mode={skeletonMode}
          count={skeletonCount}
          rows={5}
          fields={4}
        />
      }
    >
      {children}
    </Suspense>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <I18nProvider>
        <Router>
          <div className="bg-neutral-bg min-h-screen text-on-surface select-none">
            <Routes>
              {/* ===== 新多页面 SPA 路由（带 Layout 侧边导航） ===== */}
              <Route
                path="/"
                element={
                  <LazyPage skeletonMode="card" skeletonCount={3}>
                    <Layout><DashboardPageLazy /></Layout>
                  </LazyPage>
                }
              />
              <Route
                path="/cards/new"
                element={
                  <LazyPage skeletonMode="detail">
                    <Layout><CardEditorPageLazy /></Layout>
                  </LazyPage>
                }
              />
              <Route
                path="/cards/:id"
                element={
                  <LazyPage skeletonMode="detail">
                    <Layout><CardEditorPageLazy /></Layout>
                  </LazyPage>
                }
              />
              <Route
                path="/settings"
                element={
                  <LazyPage skeletonMode="card" skeletonCount={3}>
                    <Layout><SettingsPageLazy /></Layout>
                  </LazyPage>
                }
              />
              <Route
                path="/network"
                element={
                  <LazyPage skeletonMode="card" skeletonCount={3}>
                    <Layout><NetworkPageLazy /></Layout>
                  </LazyPage>
                }
              />
              <Route
                path="/matching"
                element={
                  <LazyPage skeletonMode="card" skeletonCount={3}>
                    <Layout><MatchingPageLazy /></Layout>
                  </LazyPage>
                }
              />
              <Route
                path="/api-keys"
                element={
                  <LazyPage skeletonMode="card" skeletonCount={3}>
                    <Layout><ApiKeysPageLazy /></Layout>
                  </LazyPage>
                }
              />

              {/* ===== 原有路由（保持兼容性） ===== */}
              <Route
                path="/business-card"
                element={
                  <LazyPage skeletonMode="card" skeletonCount={3}>
                    <BusinessCardPageLazy />
                  </LazyPage>
                }
              />
              <Route
                path="/card/:token"
                element={
                  <LazyPage skeletonMode="detail">
                    <BusinessCardPageLazy />
                  </LazyPage>
                }
              />
              <Route
                path="/analytics/:id"
                element={
                  <LazyPage skeletonMode="detail">
                    <AnalyticsPageLazy />
                  </LazyPage>
                }
              />
              <Route
                path="/pricing"
                element={
                  <LazyPage skeletonMode="card" skeletonCount={4}>
                    <PricingPageLazy />
                  </LazyPage>
                }
              />
              <Route
                path="/payment/callback"
                element={
                  <LazyPage skeletonMode="card">
                    <PaymentCallbackLazy />
                  </LazyPage>
                }
              />
              <Route
                path="/teams"
                element={
                  <LazyPage skeletonMode="card" skeletonCount={3}>
                    <TeamPageLazy />
                  </LazyPage>
                }
              />
              <Route
                path="/team/:teamId/settings"
                element={
                  <LazyPage skeletonMode="detail">
                    <TeamSettingsLazy />
                  </LazyPage>
                }
              />
              <Route
                path="/ab-testing"
                element={
                  <LazyPage skeletonMode="card" skeletonCount={3}>
                    <ABTestingPageLazy />
                  </LazyPage>
                }
              />
              <Route
                path="/ab-testing/:id"
                element={
                  <LazyPage skeletonMode="detail">
                    <ABTestingPageLazy />
                  </LazyPage>
                }
              />
              <Route
                path="/gdpr"
                element={
                  <LazyPage skeletonMode="detail">
                    <GDPRSettingsLazy />
                  </LazyPage>
                }
              />
            </Routes>
          </div>
        </Router>
      </I18nProvider>
    </ErrorBoundary>
  );
}
