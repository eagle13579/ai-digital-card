import { LitElement, html, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { classMap } from 'lit/directives/class-map.js';
import { cardStyles } from './styles.js';

/* ============================================
   Card Data Types
   ============================================ */
export interface DigitalCardData {
  id: string;
  name: string;
  title?: string;
  company?: string;
  email?: string;
  phone?: string;
  website?: string;
  avatar?: string;
  coverImage?: string;
  bio?: string;
  location?: string;
  socialLinks?: SocialLink[];
  theme?: 'light' | 'dark';
  premium?: boolean;
}

export interface SocialLink {
  platform: string;
  url: string;
  label?: string;
}

export interface CardErrorEvent {
  code: string;
  message: string;
  detail?: unknown;
}

/* ============================================
   Icon Helper — inline SVG icons
   Only used within shadow DOM (no external deps)
   ============================================ */
const ICONS: Record<string, string> = {
  email: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>`,
  phone: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>`,
  website: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>`,
  location: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>`,
  share: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>`,
  edit: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
  view: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`,
  close: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
  linkedin: `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>`,
  twitter: `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>`,
  github: `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/></svg>`,
};

const SOCIAL_ICONS: Record<string, string> = {
  linkedin: ICONS.linkedin,
  twitter: ICONS.twitter,
  x: ICONS.twitter,
  github: ICONS.github,
  wechat: '💬',
  whatsapp: '💬',
  telegram: '✈️',
};

/* ============================================
   <ai-digital-card> Custom Element
   ============================================ */
@customElement('ai-digital-card')
export class AiDigitalCard extends LitElement {
  static override styles = cardStyles;

  /* ---- Properties ---- */

  /** Display mode: 'embed' (inline, no chrome) or 'full' (card with glass design) */
  @property({ type: String, reflect: true }) mode: 'embed' | 'full' = 'full';

  /** API base URL for fetching card data */
  @property({ type: String, attribute: 'api-base' }) apiBase: string = '';

  /** Theme: 'light' or 'dark' */
  @property({ type: String, reflect: true }) theme: 'light' | 'dark' = 'dark';

  /** User authentication token for API calls */
  @property({ type: String, attribute: 'user-token' }) userToken: string = '';

  /** Card width (CSS value) */
  @property({ type: String }) width: string = '';

  /** Card height (CSS value) */
  @property({ type: String }) height: string = '';

  /** Card ID to load on connection */
  @property({ type: String, attribute: 'card-id' }) cardId: string = '';

  /* ---- State ---- */

  @state() private _loading = false;
  @state() private _error: string | null = null;
  @state() private _errorDetail: string | null = null;
  @state() private _card: DigitalCardData | null = null;

  /* ---- Lifecycle ---- */

  override connectedCallback(): void {
    super.connectedCallback();

    // Sync width/height to CSS custom properties
    if (this.width) {
      this.style.setProperty('--width', this.width);
    }
    if (this.height) {
      this.style.setProperty('--height', this.height);
    }

    // Auto-load card if card-id is provided
    if (this.cardId) {
      this.loadCard(this.cardId);
    }
  }

  override attributeChangedCallback(name: string, _old: string | null, value: string | null): void {
    super.attributeChangedCallback(name, _old, value);

    if (name === 'width' && value) {
      this.style.setProperty('--width', value);
    }
    if (name === 'height' && value) {
      this.style.setProperty('--height', value);
    }
    if (name === 'card-id' && value && value !== _old) {
      this.loadCard(value);
    }
  }

  /* ---- Public Methods ---- */

  /**
   * Load card data by ID from the API or from inline data.
   * @param id - Card identifier
   */
  async loadCard(id: string): Promise<void> {
    if (!id) {
      this._emitError('INVALID_ID', 'Card ID is required');
      return;
    }

    this._loading = true;
    this._error = null;
    this._errorDetail = null;
    this._card = null;
    await this.requestUpdate();

    try {
      if (this.apiBase) {
        const data = await this._fetchCard(id);
        this._card = data;
      } else {
        // No API base set — try to use inline data or dispatch event for host to provide data
        this._emitError(
          'NO_API_BASE',
          'No API base URL configured. Set api-base attribute or provide card data via data property.',
        );
        this._loading = false;
        return;
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load card data';
      this._error = message;
      this._errorDetail = err instanceof Error ? err.stack || null : null;
      this._emitError('LOAD_FAILED', message, err);
    } finally {
      this._loading = false;
    }
  }

  /**
   * Trigger share action — dispatches 'card-share' event.
   */
  shareCard(): void {
    if (!this._card) return;
    this._dispatchEvent('card-share', { card: this._card });
  }

  /**
   * Trigger edit action — dispatches 'card-edit' event.
   */
  editCard(): void {
    if (!this._card) return;
    this._dispatchEvent('card-edit', { card: this._card });
  }

  /**
   * Send an action message — dispatches event with action type.
   * @param action - Action name string
   */
  sendMessage(action: string): void {
    if (!this._card) return;
    this._dispatchEvent('card-message', { card: this._card, action });
  }

  /* ---- Private Helpers ---- */

  private async _fetchCard(id: string): Promise<DigitalCardData> {
    const base = this.apiBase.replace(/\/+$/, '');
    const url = `${base}/cards/${encodeURIComponent(id)}`;

    const headers: Record<string, string> = {
      'Accept': 'application/json',
    };

    if (this.userToken) {
      headers['Authorization'] = `Bearer ${this.userToken}`;
    }

    const response = await fetch(url, { headers });

    if (!response.ok) {
      const statusText = response.statusText || 'Unknown error';
      throw new Error(`HTTP ${response.status}: ${statusText}`);
    }

    const json = await response.json();

    // Normalize: backend might wrap data in a nested field
    const data: DigitalCardData = json.data || json.card || json;

    return {
      id: data.id,
      name: data.name || 'Unknown',
      title: data.title,
      company: data.company,
      email: data.email,
      phone: data.phone,
      website: data.website,
      avatar: data.avatar,
      coverImage: data.coverImage || data.cover_image,
      bio: data.bio,
      location: data.location,
      socialLinks: data.socialLinks || data.social_links || [],
      theme: data.theme,
      premium: data.premium || false,
    };
  }

  private _getInitials(name: string): string {
    if (!name) return '?';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
    return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
  }

  private _getSocialIcon(platform: string): string {
    const key = platform.toLowerCase().trim();
    return SOCIAL_ICONS[key] || '🔗';
  }

  private _emitError(code: string, message: string, detail?: unknown): void {
    this._dispatchEvent('error', { code, message, detail } as CardErrorEvent);
  }

  private _dispatchEvent(type: string, detail: unknown): void {
    this.dispatchEvent(
      new CustomEvent(type, {
        bubbles: true,
        composed: true,
        detail,
      }),
    );
  }

  /* ---- Render ---- */

  override render() {
    const containerClasses = {
      'card-container': true,
      dark: this.theme === 'dark',
      light: this.theme === 'light',
    };

    return html`
      <div class=${classMap(containerClasses)} part="container">
        ${this._loading ? this._renderLoading() : nothing}
        ${!this._loading && this._error ? this._renderError() : nothing}
        ${!this._loading && !this._error && this._card ? this._renderCard() : nothing}
        ${!this._loading && !this._error && !this._card && !this.cardId ? this._renderEmpty() : nothing}
      </div>
    `;
  }

  private _renderLoading() {
    return html`
      <div class="card-loading" part="loading" role="status" aria-label="Loading card">
        <div class="spinner"></div>
        <span class="loading-text">Loading card...</span>
      </div>
    `;
  }

  private _renderError() {
    return html`
      <div class="card-error" part="error" role="alert">
        <div class="error-icon">!</div>
        <div class="error-title">Failed to Load</div>
        <div class="error-message">${this._error}</div>
        <button class="error-retry" @click=${() => this.cardId && this.loadCard(this.cardId)} part="retry-button">
          Retry
        </button>
      </div>
    `;
  }

  private _renderEmpty() {
    return html`
      <div class="card-error" part="empty" role="status">
        <div class="error-title">No Card</div>
        <div class="error-message">Provide a <code>card-id</code> attribute or call <code>loadCard(id)</code>.</div>
      </div>
    `;
  }

  private _renderCard() {
    const card = this._card!;
    const initials = this._getInitials(card.name);

    return html`
      <div class="card-content" part="content">
        ${this._renderCover(card)}
        ${this._renderAvatar(card, initials)}
        ${this._renderInfo(card)}
        ${this._renderDetails(card)}
        ${this._renderSocial(card)}
        ${this.mode === 'full' ? this._renderActions(card) : nothing}
      </div>
    `;
  }

  private _renderCover(card: DigitalCardData) {
    if (!card.coverImage && !card.premium) return nothing;

    return html`
      <div class="card-cover" part="cover">
        ${card.coverImage
          ? html`<img src=${card.coverImage} alt="" loading="lazy" />`
          : nothing}
        <div class="card-cover-overlay"></div>
      </div>
    `;
  }

  private _renderAvatar(card: DigitalCardData, initials: string) {
    const avatarImageStyle = card.avatar
      ? `background-image: url('${card.avatar}'); background-size: cover; background-position: center;`
      : '';

    return html`
      <div class="card-avatar-section" part="avatar-section">
        <div class="card-avatar" part="avatar" style=${avatarImageStyle || nothing}>
          ${card.avatar
            ? nothing
            : html`<div class="card-avatar-initials">${initials}</div>`}
        </div>
        ${card.premium
          ? html`<span class="card-badge card-badge-premium" part="badge" style="margin-left:auto;margin-bottom:8px">✦ PRO</span>`
          : nothing}
      </div>
    `;
  }

  private _renderInfo(card: DigitalCardData) {
    return html`
      <div class="card-info" part="info">
        <h2 class="card-name" part="name">${card.name}</h2>
        ${card.title ? html`<p class="card-title" part="title">${card.title}</p>` : nothing}
        ${card.company ? html`<p class="card-company" part="company">${card.company}</p>` : nothing}
        ${card.bio ? html`<p class="card-bio" part="bio">${card.bio}</p>` : nothing}
      </div>
    `;
  }

  private _renderDetails(card: DigitalCardData) {
    const details: { icon: string; label: string; value: string; href?: string }[] = [];

    if (card.email) {
      details.push({
        icon: ICONS.email,
        label: 'Email',
        value: card.email,
        href: `mailto:${card.email}`,
      });
    }

    if (card.phone) {
      details.push({
        icon: ICONS.phone,
        label: 'Phone',
        value: card.phone,
        href: `tel:${card.phone.replace(/[\s\-\(\)]/g, '')}`,
      });
    }

    if (card.website) {
      details.push({
        icon: ICONS.website,
        label: 'Website',
        value: card.website.replace(/^https?:\/\//, ''),
        href: card.website.startsWith('http') ? card.website : `https://${card.website}`,
      });
    }

    if (card.location) {
      details.push({
        icon: ICONS.location,
        label: 'Location',
        value: card.location,
      });
    }

    if (details.length === 0) return nothing;

    return html`
      <div class="card-details" part="details">
        ${details.map(
          (d) => html`
            ${d.href
              ? html`
                  <a class="card-detail-item" href=${d.href} target="_blank" rel="noopener noreferrer" part="detail-link">
                    <span class="detail-icon" part="detail-icon">${d.icon}</span>
                    <span>
                      <span class="detail-label">${d.label}</span><br />
                      <span class="detail-value">${d.value}</span>
                    </span>
                  </a>
                `
              : html`
                  <div class="card-detail-item" part="detail-item">
                    <span class="detail-icon" part="detail-icon">${d.icon}</span>
                    <span>
                      <span class="detail-label">${d.label}</span><br />
                      <span class="detail-value">${d.value}</span>
                    </span>
                  </div>
                `}
          `,
        )}
      </div>
    `;
  }

  private _renderSocial(card: DigitalCardData) {
    if (!card.socialLinks || card.socialLinks.length === 0) return nothing;

    return html`
      <div class="card-social" part="social">
        ${card.socialLinks.map(
          (link) => html`
            <a
              class="social-link"
              href=${link.url}
              target="_blank"
              rel="noopener noreferrer"
              title=${link.label || link.platform}
              part="social-link"
            >
              ${this._getSocialIcon(link.platform)}
            </a>
          `,
        )}
      </div>
    `;
  }

  private _renderActions(_card: DigitalCardData) {
    return html`
      <div class="card-actions" part="actions">
        <button class="card-action-btn" part="action-view" @click=${() => this._dispatchEvent('card-view', { card: this._card })}>
          ${ICONS.view} View
        </button>
        <button class="card-action-btn" part="action-share" @click=${this.shareCard}>
          ${ICONS.share} Share
        </button>
        <button class="card-action-btn primary" part="action-edit" @click=${this.editCard}>
          ${ICONS.edit} Edit
        </button>
      </div>
    `;
  }
}

/* ---- TypeScript declaration for the custom element ---- */
declare global {
  interface HTMLElementTagNameMap {
    'ai-digital-card': AiDigitalCard;
  }
}
