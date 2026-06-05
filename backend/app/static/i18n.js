/**
 * Lightweight i18n engine for AI数字名片
 * Usage: const i18n = await initI18n(navigator.language);
 *        i18n.$t('app_name')  // => 'AI数字名片'
 *
 * Translations are loaded from /static/locales/{lang}.json at runtime.
 * A fallback map is embedded for offline/error scenarios.
 */

const FALLBACK_ZH = {
    app_name: 'AI数字名片',
    app_subtitle: '链客宝 · 企业家智能商务厅',
    login: '登录', register: '注册',
    logging_in: '登录中...', registering: '注册中...',
    phone_placeholder: '手机号', password_placeholder: '密码',
    password_placeholder_min: '密码（至少6位）', name_placeholder: '姓名',
    no_account: '没有账号？去注册', has_account: '已有账号？去登录',
    logout: '退出', user: '用户',
    loading: '加载中...', no_brochures: '还没有数字名片',
    create_first_brochure: '创建你的第一张AI数字名片，开启商业连接',
    create_my_brochure: '创建我的名片', new_brochure: '+ 新建名片',
    unnamed: '未命名', updated: '更新: ',
    edit: '编辑', preview: '预览', share: '分享',
    link_copied: '链接已复制',
    login_failed: '登录失败，请检查账号密码',
    network_error: '网络错误，请重试',
    password_min_error: '密码至少6位',
    register_failed: '注册失败，请重试',
    my_brochures: '我的画册', create_brochure: '创建画册',
    editor_title: '🪪 AI数字名片', editor_subtitle: '智能创建 · 一键分享',
    step_upload: '上传/用途', step_edit: '编辑', step_preview: '预览', step_match: '匹配',
    upload_title: '📤 上传名片', upload_hint: '支持图片 (JPG/PNG) 或 PDF 格式',
    upload_drag: '拖拽文件到此处，或点击上传', upload_format: '支持 JPG / PNG / PDF',
    purpose_title: '🎯 你的名片用途是什么？', purpose_hint: '选择后系统将帮你突出展示重点信息',
    ai_extract: '🤖 AI 智能提取', ai_extracting: '🤖 AI 正在提取信息...',
    review_title: '✏️ 确认信息', review_hint: 'AI 已提取以下字段，请核对修改',
    purpose_label: '名片用途:',
    label_name: '姓名', label_phone: '手机', label_email: '邮箱',
    label_wechat: '微信', label_company: '公司', label_title: '职位',
    label_bio: '个人简介', bio_placeholder: '个人简介',
    label_company_intro: '公司简介', company_intro_placeholder: '公司简介，介绍公司业务和优势',
    none: '暂无',
    btn_back: '← 返回', btn_next: '下一步 →',
    preview_title: '👀 预览图册', preview_hint: '翻页效果预览',
    btn_edit: '← 编辑', btn_publish: '发布图册 →',
    publish_success: '🎉 发布成功！', publish_desc: '您的AI数字名片已创建',
    share_link: '分享链接', copy_link: '📋 复制链接',
    match_title: '🤝 供需匹配结果', no_match: '暂无匹配结果，稍后再来看看',
    btn_home: '🏠 首页', btn_new: '🔄 新建',
    loading_brochure: '加载图册中...',
    btn_share: '📤 分享', btn_contact: '💬 联系我',
    views: '次浏览', not_found: '图册不存在或已失效', no_content: '暂无内容',
    page_cover: '个人封面', page_contact: '联系方式', page_company: '企业信息',
    page_qrcode: '二维码', page_detail: '详情', page_icon_default: '📄',
    copied_to_clipboard: '链接已复制到剪贴板',
    contact_requested: '💬 联系方式已发送请求', offline_mode: '📡 当前处于离线模式',
    purpose_partner: '找合作伙伴', purpose_client: '找客户',
    purpose_investor: '找投资人', purpose_supplier: '找供应商',
    purpose_partner_desc: '寻找技术/业务合作方', purpose_client_desc: '展示产品或服务能力',
    purpose_investor_desc: '突出团队与融资亮点', purpose_supplier_desc: '展示采购需求与合作',
    purpose_partner_badge: '🤝 找合作伙伴', purpose_client_badge: '💰 找客户',
    purpose_investor_badge: '📈 找投资人', purpose_supplier_badge: '🔧 找供应商',
    purpose_partner_hint: '致力于寻找技术/业务合作伙伴，欢迎洽谈合作',
    purpose_client_hint: '致力于拓展客户资源，提供优质产品与服务',
    purpose_investor_hint: '正在融资阶段，期待与投资人交流',
    purpose_supplier_hint: '寻求优质供应商合作伙伴，共建供应链',
    page_cover_partner: '寻求合作', page_cover_client: '为您服务',
    page_cover_investor: '融资进行中', page_cover_supplier: '优质供应商',
    page_title_investor_contact: '联系方式', page_title_investor_team: '团队与融资',
    page_title_investor_qrcode: '联系投资人', page_scan_qrcode: '扫码添加好友',
    page_partner_coop: '合作方向：技术联合开发 / 市场渠道共享 / 资源互换',
    page_partner_advantage: '核心优势：丰富的行业经验与落地案例',
    page_partner_cta: '欢迎洽谈合作\n扫码或联系',
    page_client_service: '服务范围：产品/服务解决方案',
    page_client_why: '为什么选择我们：专业团队 · 品质保障 · 售后无忧',
    page_client_cta: '获取报价/方案\n扫码咨询',
    page_investor_team: '核心团队：深耕行业多年，技术与管理经验丰富',
    page_investor_stage: '融资阶段：Pre-A轮',
    page_investor_milestones: '里程碑：已获多项专利与行业奖项',
    page_investor_market: '市场前景：千亿级蓝海市场',
    page_investor_cta: '期待与您详聊\n扫码查看BP',
    page_cover_investor: '融资封面',
    page_supplier_category: '主营品类：产品/服务',
    page_supplier_advantage: '合作优势：品质认证 · 稳定供货 · 价格优势',
    page_supplier_cases: '合作案例：服务多家知名企业',
    page_supplier_cta: '获取产品目录\n扫码洽谈',
    brochure_title_suffix: '的数字名片',
    error_occurred: '❌ 发布失败: ', publish_demo: '✅ 发布成功！(演示模式)',
    publish_done: '✅ 发布成功！', ai_complete: '✅ AI 提取完成，请核对信息',
    publishing: '📤 正在发布...',
    offline_title: '离线 · AI数字名片',
    offline_disconnected: '网络已断开',
    offline_viewing_cache: '你正在查看已缓存的离线内容',
    offline_sync_hint: '已缓存的内容将在恢复网络后同步更新',
    offline_cached_pages: '已缓存页面：',
    offline_reconnect: '重新连接',
};

const FALLBACK_EN = {
    app_name: 'AI Digital Business Card',
    app_subtitle: 'ChainKe · Smart Business Lounge',
    login: 'Login', register: 'Register',
    logging_in: 'Logging in...', registering: 'Registering...',
    phone_placeholder: 'Phone Number', password_placeholder: 'Password',
    password_placeholder_min: 'Password (at least 6 chars)', name_placeholder: 'Name',
    no_account: 'No account? Register', has_account: 'Already have an account? Login',
    logout: 'Logout', user: 'User',
    loading: 'Loading...', no_brochures: 'No brochures yet',
    create_first_brochure: 'Create your first AI digital business card and start connecting',
    create_my_brochure: 'Create My Card', new_brochure: '+ New Card',
    unnamed: 'Unnamed', updated: 'Updated: ',
    edit: 'Edit', preview: 'Preview', share: 'Share',
    link_copied: 'Link copied',
    login_failed: 'Login failed, please check credentials',
    network_error: 'Network error, please retry',
    password_min_error: 'Password must be at least 6 characters',
    register_failed: 'Registration failed, please retry',
    my_brochures: 'My Brochures', create_brochure: 'Create Brochure',
    editor_title: '🪪 AI Digital Business Card', editor_subtitle: 'Smart Create · One-Click Share',
    step_upload: 'Upload/Purpose', step_edit: 'Edit', step_preview: 'Preview', step_match: 'Match',
    upload_title: '📤 Upload Business Card', upload_hint: 'Supports JPG/PNG or PDF formats',
    upload_drag: 'Drag files here, or click to upload', upload_format: 'Supports JPG / PNG / PDF',
    purpose_title: '🎯 What is your card purpose?', purpose_hint: 'We will highlight key information based on your selection',
    ai_extract: '🤖 AI Smart Extract', ai_extracting: '🤖 AI is extracting information...',
    review_title: '✏️ Review Information', review_hint: 'AI has extracted the following fields, please verify',
    purpose_label: 'Card Purpose:',
    label_name: 'Name', label_phone: 'Phone', label_email: 'Email',
    label_wechat: 'WeChat', label_company: 'Company', label_title: 'Title',
    label_bio: 'Bio', bio_placeholder: 'Bio',
    label_company_intro: 'Company Intro', company_intro_placeholder: 'Company intro, describe your business and strengths',
    none: 'N/A',
    btn_back: '← Back', btn_next: 'Next →',
    preview_title: '👀 Preview Brochure', preview_hint: 'Page flip preview',
    btn_edit: '← Edit', btn_publish: 'Publish →',
    publish_success: '🎉 Published Successfully!', publish_desc: 'Your AI digital business card has been created',
    share_link: 'Share Link', copy_link: '📋 Copy Link',
    match_title: '🤝 Supply-Demand Match Results', no_match: 'No matches yet, check back later',
    btn_home: '🏠 Home', btn_new: '🔄 New',
    loading_brochure: 'Loading brochure...',
    btn_share: '📤 Share', btn_contact: '💬 Contact Me',
    views: 'views', not_found: 'Brochure not found or expired', no_content: 'No content',
    page_cover: 'Cover', page_contact: 'Contact Info', page_company: 'Company Info',
    page_qrcode: 'QR Code', page_detail: 'Details', page_icon_default: '📄',
    copied_to_clipboard: 'Link copied to clipboard',
    contact_requested: '💬 Contact request sent', offline_mode: '📡 Currently offline',
    purpose_partner: 'Find Partners', purpose_client: 'Find Clients',
    purpose_investor: 'Find Investors', purpose_supplier: 'Find Suppliers',
    purpose_partner_desc: 'Looking for technical/business partners', purpose_client_desc: 'Showcase products or services',
    purpose_investor_desc: 'Highlight team and funding highlights', purpose_supplier_desc: 'Showcase procurement needs and cooperation',
    purpose_partner_badge: '🤝 Find Partners', purpose_client_badge: '💰 Find Clients',
    purpose_investor_badge: '📈 Find Investors', purpose_supplier_badge: '🔧 Find Suppliers',
    purpose_partner_hint: 'Looking for technical/business partners, feel free to discuss',
    purpose_client_hint: 'Looking to expand client base with quality products and services',
    purpose_investor_hint: 'Currently fundraising, looking forward to connecting with investors',
    purpose_supplier_hint: 'Seeking quality supplier partners for supply chain collaboration',
    page_cover_partner: 'Seeking Partnership', page_cover_client: 'At Your Service',
    page_cover_investor: 'Fundraising', page_cover_supplier: 'Quality Supplier',
    page_title_investor_contact: 'Contact Info', page_title_investor_team: 'Team & Funding',
    page_title_investor_qrcode: 'Contact Investor', page_scan_qrcode: 'Scan to add friend',
    page_partner_coop: 'Cooperation: Joint tech dev / Market channel sharing / Resource exchange',
    page_partner_advantage: 'Core advantage: Rich industry experience with proven cases',
    page_partner_cta: 'Welcome to discuss\nScan or contact',
    page_client_service: 'Service scope: Product/service solutions',
    page_client_why: 'Why us: Professional team · Quality assurance · Worry-free after-sales',
    page_client_cta: 'Get quote/solution\nScan to inquire',
    page_investor_team: 'Core team: Deep industry experience, strong tech & management',
    page_investor_stage: 'Funding stage: Pre-A',
    page_investor_milestones: 'Milestones: Multiple patents & industry awards',
    page_investor_market: 'Market outlook: Billion-level blue ocean',
    page_investor_cta: 'Looking forward to chatting\nScan for BP',
    page_cover_investor: 'Fundraising Cover',
    page_supplier_category: 'Main categories: Products/Services',
    page_supplier_advantage: 'Advantages: Quality certified · Stable supply · Competitive price',
    page_supplier_cases: 'Cases: Served multiple well-known enterprises',
    page_supplier_cta: 'Get catalog\nScan to discuss',
    brochure_title_suffix: "'s Digital Card",
    error_occurred: '❌ Publish failed: ', publish_demo: '✅ Published! (Demo mode)',
    publish_done: '✅ Published successfully!', ai_complete: '✅ AI extraction complete, please verify',
    publishing: '📤 Publishing...',
    offline_title: 'Offline · AI Digital Card',
    offline_disconnected: 'Network disconnected',
    offline_viewing_cache: 'You are viewing cached offline content',
    offline_sync_hint: 'Cached content will sync when back online',
    offline_cached_pages: 'Cached pages:',
    offline_reconnect: 'Reconnect',
};

/**
 * Initialize i18n with a locale string
 * Loads translations from /static/locales/{lang}.json, falls back to embedded data
 * @param {string} locale - e.g. 'zh-CN', 'en-US'
 * @returns {Promise<{locale: string, $t: Function}>}
 */
async function initI18n(locale) {
    // Determine language
    let lang = 'zh';
    if (locale) {
        const code = locale.toLowerCase();
        if (code.startsWith('en') || code.startsWith('ja') || code.startsWith('ko') || code === 'en') {
            lang = 'en';
        }
    }

    const fallback = lang === 'en' ? FALLBACK_EN : FALLBACK_ZH;

    // Try loading from JSON file
    let translations = {};
    try {
        const resp = await fetch(`/static/locales/${lang}.json`);
        if (resp.ok) {
            translations = await resp.json();
        } else {
            translations = fallback;
        }
    } catch (e) {
        console.warn('[i18n] Failed to load locale file, using fallback:', e.message);
        translations = fallback;
    }

    function $t(key) {
        return translations[key] !== undefined ? translations[key] : (fallback[key] !== undefined ? fallback[key] : key);
    }

    const i18n = { locale: lang, $t };
    window.__i18n = i18n;
    return i18n;
}
