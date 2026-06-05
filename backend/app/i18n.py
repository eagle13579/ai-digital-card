"""AI数字名片 国际化(i18n) 模块

中英文翻译映射表。
所有 API 响应的 message/detail 字段通过此模块翻译。
"""

# ════════════════════════════════════════════════════════════
# 翻译映射表: key -> { zh: ..., en: ... }
# 命名约定: {domain}_{action}_{descriptor}
# ════════════════════════════════════════════════════════════

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── 通用 ──────────────────────────────────────────────
    "success": {"zh": "操作成功", "en": "Success"},
    "internal_error": {"zh": "服务器内部错误", "en": "Internal Server Error"},
    "not_found": {"zh": "资源不存在", "en": "Resource not found"},
    "too_many_requests": {"zh": "请求过于频繁，请稍后再试", "en": "Too Many Requests, please try again later"},
    "bad_request": {"zh": "请求参数错误", "en": "Bad request"},

    # ── 画册 (brochure) ──────────────────────────────────
    "brochure_created": {"zh": "画册创建成功", "en": "Brochure created successfully"},
    "brochure_updated": {"zh": "画册更新成功", "en": "Brochure updated successfully"},
    "brochure_deleted": {"zh": "画册已删除", "en": "Brochure deleted"},
    "brochure_not_found": {"zh": "画册不存在", "en": "Brochure not found"},
    "brochure_already_exists": {"zh": "该用户画册已存在", "en": "Brochure already exists for this user"},
    "brochure_no_permission_create": {"zh": "不能为其他用户创建画册", "en": "Cannot create brochure for another user"},
    "brochure_no_permission_update": {"zh": "无权修改此画册", "en": "No permission to update this brochure"},
    "brochure_no_permission_delete": {"zh": "无权删除此画册", "en": "No permission to delete this brochure"},
    "brochure_no_content": {"zh": "暂无内容", "en": "No content"},
    "brochure_publish_success": {"zh": "发布成功！", "en": "Published successfully!"},
    "brochure_publish_demo": {"zh": "发布成功！(演示模式)", "en": "Published successfully! (demo mode)"},

    # ── 用户认证 (auth) ──────────────────────────────────
    "auth_missing_header": {"zh": "缺少 Authorization 头，请先登录", "en": "Missing Authorization header, please login first"},
    "auth_token_invalid": {"zh": "Token 无效或已过期，请重新登录", "en": "Token invalid or expired, please login again"},
    "auth_phone_exists": {"zh": "该手机号已注册", "en": "This phone number is already registered"},
    "auth_register_failed": {"zh": "注册失败，请稍后再试", "en": "Registration failed, please try again later"},
    "auth_token_create_failed": {"zh": "创建 token 失败", "en": "Failed to create token"},
    "auth_login_failed": {"zh": "手机号或密码错误", "en": "Incorrect phone number or password"},
    "auth_user_not_found": {"zh": "用户不存在", "en": "User not found"},
    "auth_logout_success": {"zh": "已退出登录", "en": "Logged out"},
    "auth_network_error": {"zh": "网络错误，请重试", "en": "Network error, please retry"},
    "auth_password_too_short": {"zh": "密码至少6位", "en": "Password must be at least 6 characters"},

    # ── 信任网络 (trust) ────────────────────────────────
    "trust_added": {"zh": "信任关系添加成功", "en": "Trust relationship added successfully"},
    "trust_removed": {"zh": "信任关系已移除", "en": "Trust relationship removed"},
    "trust_add_failed": {"zh": "添加信任关系失败", "en": "Failed to add trust relationship"},
    "trust_remove_failed": {"zh": "移除信任关系失败", "en": "Failed to remove trust relationship"},
    "trust_no_permission": {"zh": "无权操作其他用户的信任网络", "en": "No permission to modify other user's trust network"},
    "trust_target_not_found": {"zh": "被信任用户画册不存在", "en": "Trusted user's brochure not found"},

    # ── 匹配 (match) ────────────────────────────────────
    "match_source_not_found": {"zh": "源用户画册不存在", "en": "Source user brochure not found"},
    "match_no_results": {"zh": "暂无匹配结果，稍后再来看看", "en": "No matches found, check back later"},
    "match_engine_running": {"zh": "🤖 AI 正在提取信息...", "en": "🤖 AI is extracting information..."},
    "match_extract_complete": {"zh": "✅ AI 提取完成，请核对信息", "en": "✅ AI extraction complete, please verify"},

    # ── 批量导入 (batch) ────────────────────────────────
    "batch_import_empty": {"zh": "导入列表不能为空", "en": "Import list cannot be empty"},
    "batch_import_result": {"zh": "成功导入 {success} 个用户，失败 {fail} 个", "en": "Successfully imported {success} users, {fail} failed"},
    "batch_import_db_error": {"zh": "写入数据库失败", "en": "Database write failed"},

    # ── 链客宝同步 (chainke) ────────────────────────────
    "chainke_module_not_loaded": {"zh": "链客宝桥接模块未加载，同步跳过", "en": "Chainke bridge module not loaded, sync skipped"},
    "chainke_sync_complete": {"zh": "同步完成", "en": "Sync completed"},

    # ── 速率限制 ────────────────────────────────────────
    "rate_limit_exceeded": {"zh": "请求过于频繁，请稍后再试", "en": "Too Many Requests"},

    # ── 访客 ────────────────────────────────────────────
    "visitor_logged": {"zh": "访问已记录", "en": "Visit logged"},
    "brochure_expired": {"zh": "图册不存在或已失效", "en": "Brochure not found or expired"},

    # ── 前端 UI 文案 ────────────────────────────────────
    "ui_app_name": {"zh": "AI数字名片", "en": "AI Digital Business Card"},
    "ui_subtitle": {"zh": "链客宝 · 企业家智能商务厅", "en": "Chainke · Smart Business Hall"},
    "ui_login": {"zh": "登录", "en": "Login"},
    "ui_register": {"zh": "注册", "en": "Register"},
    "ui_logout": {"zh": "退出", "en": "Logout"},
    "ui_phone": {"zh": "手机号", "en": "Phone Number"},
    "ui_password": {"zh": "密码", "en": "Password"},
    "ui_name": {"zh": "姓名", "en": "Name"},
    "ui_phone_placeholder": {"zh": "手机号", "en": "Phone Number"},
    "ui_password_placeholder": {"zh": "密码（至少6位）", "en": "Password (min 6 chars)"},
    "ui_name_placeholder": {"zh": "姓名", "en": "Your Name"},
    "ui_login_loading": {"zh": "登录中...", "en": "Logging in..."},
    "ui_register_loading": {"zh": "注册中...", "en": "Registering..."},
    "ui_switch_to_register": {"zh": "没有账号？去注册", "en": "No account? Register"},
    "ui_switch_to_login": {"zh": "已有账号？去登录", "en": "Already have an account? Login"},
    "ui_new_brochure": {"zh": "+ 新建名片", "en": "+ New Card"},
    "ui_loading": {"zh": "加载中...", "en": "Loading..."},
    "ui_no_brochures_title": {"zh": "还没有数字名片", "en": "No digital cards yet"},
    "ui_no_brochures_desc": {"zh": "创建你的第一张AI数字名片，开启商业连接", "en": "Create your first AI digital card and start business connections"},
    "ui_create_first": {"zh": "创建我的名片", "en": "Create My Card"},
    "ui_unnamed": {"zh": "未命名", "en": "Unnamed"},
    "ui_updated_prefix": {"zh": "更新: ", "en": "Updated: "},
    "ui_edit": {"zh": "编辑", "en": "Edit"},
    "ui_preview": {"zh": "预览", "en": "Preview"},
    "ui_share": {"zh": "分享", "en": "Share"},
    "ui_link_copied": {"zh": "链接已复制", "en": "Link copied"},
    "ui_share_title": {"zh": "我的数字名片", "en": "My Digital Card"},
    "ui_logging_out": {"zh": "退出中...", "en": "Logging out..."},
    "ui_offline_mode": {"zh": "📡 当前处于离线模式", "en": "📡 Currently offline"},
    "ui_network_disconnected": {"zh": "网络已断开", "en": "Network disconnected"},
    "ui_offline_hint": {"zh": "你正在查看已缓存的离线内容", "en": "You are viewing cached offline content"},
    "ui_cached_pages": {"zh": "已缓存页面：", "en": "Cached pages:"},
    "ui_cached_sync_hint": {"zh": "已缓存的内容将在恢复网络后同步更新", "en": "Cached content will sync when back online"},
    "ui_reconnect": {"zh": "重新连接", "en": "Reconnect"},
    "ui_editor_title": {"zh": "🪪 AI数字名片", "en": "🪪 AI Digital Card"},
    "ui_editor_subtitle": {"zh": "智能创建 · 一键分享", "en": "Smart Create · One-click Share"},
    "ui_upload_title": {"zh": "📤 上传名片", "en": "📤 Upload Card"},
    "ui_upload_hint": {"zh": "支持图片 (JPG/PNG) 或 PDF 格式", "en": "Supports images (JPG/PNG) or PDF"},
    "ui_upload_drag": {"zh": "拖拽文件到此处，或点击上传", "en": "Drag files here, or click to upload"},
    "ui_upload_supported": {"zh": "支持 JPG / PNG / PDF", "en": "Supports JPG / PNG / PDF"},
    "ui_purpose_title": {"zh": "🎯 你的名片用途是什么？", "en": "🎯 What's your card purpose?"},
    "ui_purpose_hint": {"zh": "选择后系统将帮你突出展示重点信息", "en": "Select to highlight key info"},
    "ui_ai_extract": {"zh": "🤖 AI 智能提取", "en": "🤖 AI Smart Extract"},
    "ui_review_title": {"zh": "✏️ 确认信息", "en": "✏️ Review Info"},
    "ui_review_hint": {"zh": "AI 已提取以下字段，请核对修改", "en": "AI extracted the fields below, please verify"},
    "ui_purpose_label": {"zh": "名片用途:", "en": "Card purpose:"},
    "ui_back": {"zh": "← 返回", "en": "← Back"},
    "ui_next": {"zh": "下一步 →", "en": "Next →"},
    "ui_preview_title_label": {"zh": "👀 预览图册", "en": "👀 Preview Album"},
    "ui_preview_hint": {"zh": "翻页效果预览", "en": "Flip effect preview"},
    "ui_edit_btn": {"zh": "← 编辑", "en": "← Edit"},
    "ui_publish": {"zh": "发布图册 →", "en": "Publish →"},
    "ui_publish_success": {"zh": "🎉 发布成功！", "en": "🎉 Published!"},
    "ui_publish_desc": {"zh": "您的AI数字名片已创建", "en": "Your AI digital card has been created"},
    "ui_share_link": {"zh": "分享链接", "en": "Share Link"},
    "ui_copy_link": {"zh": "📋 复制链接", "en": "📋 Copy Link"},
    "ui_match_results": {"zh": "🤝 供需匹配结果", "en": "🤝 Match Results"},
    "ui_home": {"zh": "🏠 首页", "en": "🏠 Home"},
    "ui_new": {"zh": "🔄 新建", "en": "🔄 New"},
    "ui_publishing": {"zh": "📤 正在发布...", "en": "📤 Publishing..."},
    "ui_publish_failed": {"zh": "❌ 发布失败: ", "en": "❌ Publish failed: "},
    "ui_contact_me": {"zh": "💬 联系我", "en": "💬 Contact Me"},
    "ui_views": {"zh": "次浏览", "en": "views"},
    "ui_loading_brochure": {"zh": "加载图册中...", "en": "Loading album..."},
    "ui_contact_request_sent": {"zh": "💬 联系方式已发送请求", "en": "💬 Contact request sent"},
    "ui_steps_upload": {"zh": "上传/用途", "en": "Upload"},
    "ui_steps_edit": {"zh": "编辑", "en": "Edit"},
    "ui_steps_preview": {"zh": "预览", "en": "Preview"},
    "ui_steps_match": {"zh": "匹配", "en": "Match"},
    "ui_purpose_partner": {"zh": "找合作伙伴", "en": "Find Partners"},
    "ui_purpose_partner_desc": {"zh": "寻找技术/业务合作方", "en": "Find tech/business partners"},
    "ui_purpose_client": {"zh": "找客户", "en": "Find Clients"},
    "ui_purpose_client_desc": {"zh": "展示产品或服务能力", "en": "Showcase products/services"},
    "ui_purpose_investor": {"zh": "找投资人", "en": "Find Investors"},
    "ui_purpose_investor_desc": {"zh": "突出团队与融资亮点", "en": "Highlight team & funding"},
    "ui_purpose_supplier": {"zh": "找供应商", "en": "Find Suppliers"},
    "ui_purpose_supplier_desc": {"zh": "展示采购需求与合作", "en": "Show procurement needs"},
    "ui_field_name": {"zh": "姓名", "en": "Name"},
    "ui_field_phone": {"zh": "手机", "en": "Phone"},
    "ui_field_email": {"zh": "邮箱", "en": "Email"},
    "ui_field_wechat": {"zh": "微信", "en": "WeChat"},
    "ui_field_company": {"zh": "公司", "en": "Company"},
    "ui_field_title": {"zh": "职位", "en": "Title"},
    "ui_field_name_ph": {"zh": "姓名", "en": "Name"},
    "ui_field_phone_ph": {"zh": "手机号", "en": "Phone"},
    "ui_field_email_ph": {"zh": "邮箱", "en": "Email"},
    "ui_field_wechat_ph": {"zh": "微信号", "en": "WeChat ID"},
    "ui_field_company_ph": {"zh": "公司名称", "en": "Company Name"},
    "ui_field_title_ph": {"zh": "职位", "en": "Title"},
    "ui_page_cover": {"zh": "个人封面", "en": "Cover"},
    "ui_page_contact": {"zh": "联系方式", "en": "Contact"},
    "ui_page_company": {"zh": "企业信息", "en": "Company"},
    "ui_page_qrcode": {"zh": "二维码", "en": "QR Code"},
    "ui_page_detail": {"zh": "详情", "en": "Details"},
    "ui_scan_qrcode": {"zh": "扫码添加好友", "en": "Scan to add friend"},
    "ui_purpose_hint_partner": {"zh": "致力于寻找技术/业务合作伙伴，欢迎洽谈合作", "en": "Looking for tech/business partners, welcome to discuss"},
    "ui_purpose_hint_client": {"zh": "致力于拓展客户资源，提供优质产品与服务", "en": "Looking for clients, offering quality products & services"},
    "ui_purpose_hint_investor": {"zh": "正在融资阶段，期待与投资人交流", "en": "Currently fundraising, looking forward to connecting with investors"},
    "ui_purpose_hint_supplier": {"zh": "寻求优质供应商合作伙伴，共建供应链", "en": "Seeking quality supplier partners"},
    "ui_brochure_title_suffix": {"zh": "的数字名片", "en": "'s Digital Card"},
    "ui_contact_item_phone": {"zh": "电话", "en": "Phone"},
    "ui_contact_item_email": {"zh": "邮箱", "en": "Email"},
    "ui_contact_item_wechat": {"zh": "微信", "en": "WeChat"},
    "ui_section_bio": {"zh": "📝 个人简介", "en": "📝 Bio"},
    "ui_section_contact": {"zh": "📞 联系方式", "en": "📞 Contact"},
    "ui_section_tags": {"zh": "🏷️ 标签", "en": "🏷️ Tags"},
    "ui_footer_version": {"zh": "AI数字名片 v2.1", "en": "AI Digital Card v2.1"},
    "ui_visited_count": {"zh": "👁️ 已被浏览 {count} 次", "en": "👁️ Viewed {count} times"},
    "ui_page_nav": {"zh": "第 {current}/{total} 页", "en": "Page {current}/{total}"},

    # ── 卡片编辑页 (Card Editor) ──────────────────────────
    "card_editor_title": {"zh": "编辑名片", "en": "Edit Card"},
    "upload_brochure": {"zh": "上传名片", "en": "Upload Brochure"},
    "card_purpose": {"zh": "你的名片用途是什么", "en": "Purpose of your card"},
    "card_cover": {"zh": "个人封面", "en": "Personal Cover"},
    "company_info": {"zh": "企业信息", "en": "Company Info"},
    "company_name": {"zh": "公司名称", "en": "Company Name"},
    "position_title": {"zh": "职位", "en": "Position"},
    "contact_info": {"zh": "联系方式", "en": "Contact Info"},
    "share_link": {"zh": "分享链接", "en": "Share Link"},
    "step_company": {"zh": "企业信息", "en": "Company Info"},
    "step_contact": {"zh": "联系方式", "en": "Contact Info"},
    "step_preview": {"zh": "预览", "en": "Preview"},
    "purpose_business": {"zh": "业务合作方", "en": "Business Partner"},
    "purpose_supplier": {"zh": "优质供应商", "en": "Supplier"},
    "purpose_investor": {"zh": "投资方", "en": "Investor"},
    "purpose_employee": {"zh": "企业员工", "en": "Employee"},
    "purpose_personal": {"zh": "个人名片", "en": "Personal"},
    "find_partner": {"zh": "找合作伙伴", "en": "Find Partner"},
    "find_supplier": {"zh": "找供应商", "en": "Find Supplier"},
    "find_investor": {"zh": "找投资人", "en": "Find Investor"},
    "match_result": {"zh": "供需匹配结果", "en": "Match Results"},

    # ── 画册查看页 (Viewer) ──────────────────────────────
    "viewer_title": {"zh": "数字名片", "en": "Digital Card"},
    "loading_brochure": {"zh": "加载图册中", "en": "Loading..."},
    "initialized": {"zh": "初始化翻页引擎", "en": "Initializing..."},
    "page_indicator": {"zh": "分页指示器", "en": "Page Indicator"},
    "supply_chain": {"zh": "共建供应链", "en": "Supply Chain"},
    "service_us": {"zh": "为您服务", "en": "Our Services"},
    "why_choose_us": {"zh": "为什么选择我们", "en": "Why Choose Us"},
    "main_category": {"zh": "主营品类", "en": "Main Category"},
    "product_manager": {"zh": "产品经理", "en": "Product Manager"},
    "professional_team": {"zh": "专业团队 · 品质保障 · 售后无忧", "en": "Professional Team"},
    "experience": {"zh": "丰富的行业经验与落地案例", "en": "Rich Experience"},
}


def t(key: str, lang: str = "zh") -> str:
    """根据 key 和语言代码返回翻译文本。

    Args:
        key: 翻译键名
        lang: 语言代码 (zh / en)

    Returns:
        翻译后的文本，找不到时返回 key 本身
    """
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    return entry.get(lang, entry.get("zh", key))


def detect_lang(accept_language: str = "") -> str:
    """从 Accept-Language 头中检测语言。

    Args:
        accept_language: Accept-Language 请求头值

    Returns:
        'zh' 或 'en'
    """
    if not accept_language:
        return "zh"
    accept_language = accept_language.lower()
    if "zh" in accept_language:
        return "zh"
    if "en" in accept_language:
        return "en"
    # 默认中文
    return "zh"
