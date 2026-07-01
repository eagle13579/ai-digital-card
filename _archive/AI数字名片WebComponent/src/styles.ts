import { css } from 'lit';

export const cardStyles = css`
  /* ============================================
     <ai-digital-card> — Shadow DOM Styles
     Based on AI Digital Card Design Token System
     ============================================ */

  :host {
    --card-width: var(--width, 360px);
    --card-height: var(--height, auto);
    --card-radius: 16px;

    /* Design Tokens (aligned with Phase 1 token system) */
    --color-brand-500: #6366f1;
    --color-brand-400: #818cf8;
    --color-brand-600: #4f46e5;
    --color-success-500: #22c55e;
    --color-danger-500: #ef4444;
    --color-info-500: #3b82f6;
    --color-warning-500: #f59e0b;

    --gradient-brand: linear-gradient(135deg, #6366f1, #8b5cf6);

    --spacing-1: 4px;
    --spacing-2: 8px;
    --spacing-3: 12px;
    --spacing-4: 16px;
    --spacing-5: 20px;
    --spacing-6: 24px;
    --spacing-8: 32px;
    --spacing-10: 40px;

    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --radius-full: 9999px;

    --shadow-sm: 0 1px 2px 0 rgba(0,0,0,0.20);
    --shadow-md: 0 4px 12px -2px rgba(0,0,0,0.25);
    --shadow-lg: 0 12px 32px -4px rgba(0,0,0,0.30);

    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

    --size-xs: 0.75rem;
    --size-sm: 0.8125rem;
    --size-base: 0.875rem;
    --size-md: 0.9375rem;
    --size-lg: 1rem;
    --size-xl: 1.125rem;
    --size-2xl: 1.25rem;
    --size-3xl: 1.5rem;

    --weight-regular: 400;
    --weight-medium: 500;
    --weight-semibold: 600;
    --weight-bold: 700;

    --leading-tight: 1.2;
    --leading-base: 1.5;
    --leading-relaxed: 1.75;

    --duration-fast: 100ms;
    --duration-base: 200ms;
    --duration-slow: 300ms;
    --easing-out: cubic-bezier(0, 0, 0.2, 1);
    --easing-in-out: cubic-bezier(0.4, 0, 0.2, 1);

    --transition-fast: var(--duration-fast) var(--easing-out);
    --transition-base: var(--duration-base) var(--easing-in-out);
    --transition-slow: var(--duration-slow) var(--easing-in-out);

    display: inline-block;
    width: var(--card-width);
    height: var(--card-height);
    font-family: var(--font-sans);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    box-sizing: border-box;
  }

  :host *,
  :host *::before,
  :host *::after {
    box-sizing: border-box;
  }

  /* ---- Card Container ---- */
  .card-container {
    position: relative;
    width: 100%;
    height: 100%;
    border-radius: var(--card-radius);
    overflow: hidden;
    transition: transform var(--transition-slow), box-shadow var(--transition-slow);
  }

  .card-container:hover {
    transform: translateY(-2px);
  }

  /* ---- Theme: Dark ---- */
  :host([theme='dark']) .card-container,
  .card-container.dark {
    --color-surface-base: #0a0a0f;
    --color-surface-card: rgba(255, 255, 255, 0.06);
    --color-surface-hover: rgba(255, 255, 255, 0.08);
    --color-text-primary: rgba(255, 255, 255, 0.95);
    --color-text-secondary: rgba(255, 255, 255, 0.65);
    --color-text-tertiary: rgba(255, 255, 255, 0.40);
    --color-border-default: rgba(255, 255, 255, 0.10);
    --color-border-strong: rgba(255, 255, 255, 0.18);

    background: var(--color-surface-card);
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    border: 1px solid var(--color-border-default);
    box-shadow: var(--shadow-md), 0 0 0 1px rgba(255,255,255,0.04) inset;
    color: var(--color-text-primary);
  }

  /* ---- Theme: Light ---- */
  :host([theme='light']) .card-container,
  .card-container.light {
    --color-surface-base: #ffffff;
    --color-surface-card: rgba(255, 255, 255, 0.95);
    --color-surface-hover: rgba(0, 0, 0, 0.03);
    --color-text-primary: rgba(9, 9, 11, 0.92);
    --color-text-secondary: rgba(9, 9, 11, 0.65);
    --color-text-tertiary: rgba(9, 9, 11, 0.45);
    --color-border-default: rgba(0, 0, 0, 0.08);
    --color-border-strong: rgba(0, 0, 0, 0.16);

    background: var(--color-surface-card);
    box-shadow: 0 2px 8px 0 rgba(0,0,0,0.08), var(--shadow-md);
    border: 1px solid var(--color-border-default);
    color: var(--color-text-primary);
  }

  /* ---- Mode: Embed ---- */
  :host([mode='embed']) .card-container {
    border-radius: 0;
    border: none;
    box-shadow: none;
    backdrop-filter: none;
    background: transparent;
  }

  :host([mode='embed']) .card-container:hover {
    transform: none;
  }

  /* ---- Loading State ---- */
  .card-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-4);
    padding: var(--spacing-10) var(--spacing-6);
    text-align: center;
  }

  .spinner {
    width: 36px;
    height: 36px;
    border: 3px solid var(--color-border-default);
    border-top-color: var(--color-brand-500);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .loading-text {
    font-size: var(--size-sm);
    color: var(--color-text-secondary);
    font-weight: var(--weight-medium);
  }

  /* ---- Error State ---- */
  .card-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-3);
    padding: var(--spacing-10) var(--spacing-6);
    text-align: center;
  }

  .error-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: rgba(239, 68, 68, 0.10);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: var(--size-2xl);
    color: var(--color-danger-500);
  }

  .error-title {
    font-size: var(--size-lg);
    font-weight: var(--weight-semibold);
    color: var(--color-text-primary);
  }

  .error-message {
    font-size: var(--size-sm);
    color: var(--color-text-secondary);
    line-height: var(--leading-relaxed);
  }

  .error-retry {
    margin-top: var(--spacing-2);
    padding: var(--spacing-2) var(--spacing-4);
    background: var(--color-brand-500);
    color: #fff;
    border: none;
    border-radius: var(--radius-md);
    font-size: var(--size-sm);
    font-weight: var(--weight-medium);
    cursor: pointer;
    transition: background var(--transition-fast);
  }

  .error-retry:hover {
    background: var(--color-brand-600);
  }

  /* ---- Card Content (Loaded) ---- */
  .card-content {
    position: relative;
    display: flex;
    flex-direction: column;
    width: 100%;
  }

  /* ---- Cover Section ---- */
  .card-cover {
    position: relative;
    width: 100%;
    height: 120px;
    overflow: hidden;
    background: var(--gradient-brand);
  }

  .card-cover img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .card-cover-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, transparent 60%, rgba(0,0,0,0.4) 100%);
  }

  /* ---- Avatar ---- */
  .card-avatar-section {
    position: relative;
    display: flex;
    align-items: flex-end;
    padding: 0 var(--spacing-5);
    margin-top: -40px;
    z-index: 1;
  }

  .card-avatar {
    width: 72px;
    height: 72px;
    border-radius: 50%;
    border: 3px solid var(--color-surface-base);
    background: var(--color-surface-hover);
    object-fit: cover;
    overflow: hidden;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: var(--size-3xl);
    color: var(--color-text-secondary);
    background-size: cover;
    background-position: center;
  }

  .card-avatar-initials {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: var(--size-2xl);
    font-weight: var(--weight-bold);
    color: #fff;
    background: var(--gradient-brand);
  }

  /* ---- Info Section ---- */
  .card-info {
    padding: var(--spacing-4) var(--spacing-5) var(--spacing-5);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
  }

  .card-name {
    font-size: var(--size-xl);
    font-weight: var(--weight-bold);
    color: var(--color-text-primary);
    line-height: var(--leading-tight);
    margin: 0;
  }

  .card-title {
    font-size: var(--size-base);
    font-weight: var(--weight-medium);
    color: var(--color-text-secondary);
    margin: 0;
  }

  .card-company {
    font-size: var(--size-sm);
    color: var(--color-text-tertiary);
    margin: 0;
  }

  .card-bio {
    font-size: var(--size-sm);
    color: var(--color-text-secondary);
    line-height: var(--leading-relaxed);
    margin: var(--spacing-2) 0 0;
    padding: var(--spacing-3) 0;
    border-top: 1px solid var(--color-border-default);
  }

  /* ---- Contact Details ---- */
  .card-details {
    padding: 0 var(--spacing-5) var(--spacing-4);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
  }

  .card-detail-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-3);
    font-size: var(--size-sm);
    color: var(--color-text-secondary);
    text-decoration: none;
    padding: var(--spacing-1) 0;
    transition: color var(--transition-fast);
  }

  .card-detail-item:hover {
    color: var(--color-brand-500);
  }

  .detail-icon {
    width: 32px;
    height: 32px;
    border-radius: var(--radius-md);
    background: var(--color-surface-hover);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: var(--size-md);
  }

  .detail-label {
    font-size: var(--size-xs);
    color: var(--color-text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: var(--weight-medium);
  }

  .detail-value {
    font-size: var(--size-sm);
    color: var(--color-text-primary);
    font-weight: var(--weight-medium);
  }

  /* ---- Social Links ---- */
  .card-social {
    padding: 0 var(--spacing-5) var(--spacing-5);
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-2);
  }

  .social-link {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: var(--radius-md);
    background: var(--color-surface-hover);
    border: 1px solid var(--color-border-default);
    color: var(--color-text-secondary);
    text-decoration: none;
    font-size: var(--size-lg);
    transition: all var(--transition-fast);
  }

  .social-link:hover {
    background: var(--color-brand-500);
    border-color: var(--color-brand-500);
    color: #fff;
    transform: translateY(-1px);
  }

  /* ---- Actions Bar ---- */
  .card-actions {
    display: flex;
    gap: var(--spacing-2);
    padding: var(--spacing-4) var(--spacing-5);
    border-top: 1px solid var(--color-border-default);
  }

  .card-action-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-1);
    padding: var(--spacing-2) var(--spacing-3);
    border: 1px solid var(--color-border-default);
    border-radius: var(--radius-md);
    background: transparent;
    color: var(--color-text-secondary);
    font-size: var(--size-xs);
    font-weight: var(--weight-medium);
    font-family: var(--font-sans);
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
  }

  .card-action-btn:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
    border-color: var(--color-border-strong);
  }

  .card-action-btn.primary {
    background: var(--color-brand-500);
    border-color: var(--color-brand-500);
    color: #fff;
  }

  .card-action-btn.primary:hover {
    background: var(--color-brand-600);
    border-color: var(--color-brand-600);
  }

  /* ---- Badge ---- */
  .card-badge {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-1);
    padding: 2px var(--spacing-2);
    border-radius: var(--radius-full);
    font-size: var(--size-xs);
    font-weight: var(--weight-medium);
    line-height: 1.4;
  }

  .card-badge-premium {
    background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.15));
    color: var(--color-brand-400);
    border: 1px solid rgba(99,102,241,0.20);
  }

  /* ---- Responsive: Mobile First ---- */
  @media (max-width: 480px) {
    :host {
      --card-width: 100%;
    }

    .card-cover {
      height: 100px;
    }

    .card-avatar {
      width: 60px;
      height: 60px;
      margin-top: -36px;
    }

    .card-info {
      padding: var(--spacing-3) var(--spacing-4) var(--spacing-4);
    }

    .card-name {
      font-size: var(--size-lg);
    }

    .card-details {
      padding: 0 var(--spacing-4) var(--spacing-3);
    }

    .card-social {
      padding: 0 var(--spacing-4) var(--spacing-4);
    }

    .card-actions {
      padding: var(--spacing-3) var(--spacing-4);
    }
  }

  @media (min-width: 481px) and (max-width: 768px) {
    :host {
      --card-width: 100%;
      max-width: 420px;
    }
  }

  /* ---- Accessibility ---- */
  .card-action-btn:focus-visible,
  .social-link:focus-visible,
  .error-retry:focus-visible {
    outline: 2px solid var(--color-brand-500);
    outline-offset: 2px;
  }

  /* ---- Reduced Motion ---- */
  @media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
      animation-duration: 0.01ms !important;
      transition-duration: 0.01ms !important;
    }
  }

  /* ---- Skeleton Loading ---- */
  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }

  .skeleton {
    background: linear-gradient(
      90deg,
      var(--color-surface-hover) 25%,
      var(--color-border-default) 50%,
      var(--color-surface-hover) 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
    border-radius: var(--radius-sm);
  }

  .skeleton-text {
    height: 14px;
    width: 60%;
    margin-bottom: var(--spacing-2);
  }

  .skeleton-text.short {
    width: 40%;
  }

  .skeleton-text.long {
    width: 80%;
  }

  .skeleton-avatar {
    width: 72px;
    height: 72px;
    border-radius: 50%;
  }

  .skeleton-button {
    height: 36px;
    border-radius: var(--radius-md);
  }
`;
