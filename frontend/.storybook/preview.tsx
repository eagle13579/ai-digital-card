import type { Preview } from '@storybook/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { I18nProvider } from '../src/i18n';
import '../src/index.css';

/** 全局装饰器：为 Story 提供国际化 + 路由上下文 */
const withProviders = (Story: React.ComponentType) => (
  <BrowserRouter>
    <I18nProvider>
      <div className="bg-neutral-bg min-h-screen p-6">
        <Story />
      </div>
    </I18nProvider>
  </BrowserRouter>
);

const preview: Preview = {
  decorators: [withProviders],
  parameters: {
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#f8fafc' },
        { name: 'dark', value: '#0f172a' },
        { name: 'surface', value: '#ffffff' },
      ],
    },
    viewport: {
      viewports: {
        mobile: { name: 'Mobile', styles: { width: '375px', height: '812px' } },
        tablet: { name: 'Tablet', styles: { width: '768px', height: '1024px' } },
        desktop: { name: 'Desktop', styles: { width: '1280px', height: '800px' } },
      },
    },
    a11y: {
      config: { rules: [{ id: 'color-contrast', enabled: true }] },
    },
    options: {
      storySort: {
        order: ['Design System', 'Components'],
      },
    },
  },
  tags: ['autodocs'],
};

export default preview;
