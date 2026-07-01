"""AI数字名片 国际化(i18n) 模块

中英文翻译映射表。
所有 API 响应的 message/detail 字段通过此模块翻译。
"""

# ════════════════════════════════════════════════════════════
# 翻译映射表: key -> { zh: ..., en: ..., ja: ..., ko: ..., es: ..., fr: ..., de: ..., pt: ..., ru: ..., ar: ..., th: ..., vi: ... }
# 命名约定: {domain}_{action}_{descriptor}
# ════════════════════════════════════════════════════════════

# 所有支持的语言代码 (用于遍历填充默认值)
ALL_LANGS = ["zh", "en", "ja", "ko", "es", "fr", "de", "pt", "ru", "ar", "th", "vi"]

def _fill_langs(d: dict[str, str]) -> dict[str, str]:
    """确保所有语言都有值，缺失的用 en 或 zh 兜底。"""
    for lang in ALL_LANGS:
        if lang not in d:
            d[lang] = d.get("en", d.get("zh", ""))
    return d

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── 通用 ──────────────────────────────────────────────
    "success": _fill_langs({"zh": "操作成功", "en": "Success", "ja": "操作成功", "ko": "작업 성공", "es": "Operación exitosa", "fr": "Opération réussie", "de": "Erfolgreich", "pt": "Operação bem-sucedida", "ru": "Успешно", "ar": "عملية ناجحة", "th": "ดำเนินการสำเร็จ", "vi": "Thao tác thành công"}),
    "internal_error": _fill_langs({"zh": "服务器内部错误", "en": "Internal Server Error", "ja": "サーバー内部エラー", "ko": "서버 내부 오류", "es": "Error interno del servidor", "fr": "Erreur interne du serveur", "de": "Interner Serverfehler", "pt": "Erro interno do servidor", "ru": "Внутренняя ошибка сервера", "ar": "خطأ داخلي في الخادم", "th": "ข้อผิดพลาดภายในเซิร์ฟเวอร์", "vi": "Lỗi máy chủ nội bộ"}),
    "not_found": _fill_langs({"zh": "资源不存在", "en": "Resource not found", "ja": "リソースが見つかりません", "ko": "리소스를 찾을 수 없습니다", "es": "Recurso no encontrado", "fr": "Ressource introuvable", "de": "Ressource nicht gefunden", "pt": "Recurso não encontrado", "ru": "Ресурс не найден", "ar": "المورد غير موجود", "th": "ไม่พบทรัพยากร", "vi": "Không tìm thấy tài nguyên"}),
    "too_many_requests": _fill_langs({"zh": "请求过于频繁，请稍后再试", "en": "Too Many Requests, please try again later", "ja": "リクエストが多すぎます。後でもう一度お試しください", "ko": "요청이 너무 많습니다. 나중에 다시 시도해주세요", "es": "Demasiadas solicitudes, inténtelo más tarde", "fr": "Trop de requêtes, veuillez réessayer plus tard", "de": "Zu viele Anfragen, bitte später erneut versuchen", "pt": "Muitas solicitações, tente novamente mais tarde", "ru": "Слишком много запросов, повторите попытку позже", "ar": "طلبات كثيرة جداً، يرجى المحاولة لاحقاً", "th": "คำขอมากเกินไป กรุณาลองใหม่ภายหลัง", "vi": "Quá nhiều yêu cầu, vui lòng thử lại sau"}),
    "bad_request": _fill_langs({"zh": "请求参数错误", "en": "Bad request", "ja": "リクエストパラメータが不正です", "ko": "잘못된 요청입니다", "es": "Solicitud incorrecta", "fr": "Mauvaise requête", "de": "Ungültige Anfrage", "pt": "Solicitação inválida", "ru": "Неверный запрос", "ar": "طلب غير صالح", "th": "คำขอไม่ถูกต้อง", "vi": "Yêu cầu không hợp lệ"}),

    # ── 画册 (brochure) ──────────────────────────────────
    "brochure_created": _fill_langs({"zh": "画册创建成功", "en": "Brochure created successfully"}),
    "brochure_updated": _fill_langs({"zh": "画册更新成功", "en": "Brochure updated successfully"}),
    "brochure_deleted": _fill_langs({"zh": "画册已删除", "en": "Brochure deleted"}),
    "brochure_not_found": _fill_langs({"zh": "画册不存在", "en": "Brochure not found"}),
    "brochure_already_exists": _fill_langs({"zh": "该用户画册已存在", "en": "Brochure already exists for this user"}),
    "brochure_no_permission_create": _fill_langs({"zh": "不能为其他用户创建画册", "en": "Cannot create brochure for another user"}),
    "brochure_no_permission_update": _fill_langs({"zh": "无权修改此画册", "en": "No permission to update this brochure"}),
    "brochure_no_permission_delete": _fill_langs({"zh": "无权删除此画册", "en": "No permission to delete this brochure"}),
    "brochure_no_content": _fill_langs({"zh": "暂无内容", "en": "No content"}),
    "brochure_publish_success": _fill_langs({"zh": "发布成功！", "en": "Published successfully!"}),
    "brochure_publish_demo": _fill_langs({"zh": "发布成功！(演示模式)", "en": "Published successfully! (demo mode)"}),

    # ── 用户认证 (auth) ──────────────────────────────────
    "auth_missing_header": _fill_langs({"zh": "缺少 Authorization 头，请先登录", "en": "Missing Authorization header, please login first"}),
    "auth_token_invalid": _fill_langs({"zh": "Token 无效或已过期，请重新登录", "en": "Token invalid or expired, please login again"}),
    "auth_phone_exists": _fill_langs({"zh": "该手机号已注册", "en": "This phone number is already registered"}),
    "auth_register_failed": _fill_langs({"zh": "注册失败，请稍后再试", "en": "Registration failed, please try again later"}),
    "auth_token_create_failed": _fill_langs({"zh": "创建 token 失败", "en": "Failed to create token"}),
    "auth_login_failed": _fill_langs({"zh": "手机号或密码错误", "en": "Incorrect phone number or password"}),
    "auth_user_not_found": _fill_langs({"zh": "用户不存在", "en": "User not found"}),
    "auth_logout_success": _fill_langs({"zh": "已退出登录", "en": "Logged out"}),
    "auth_network_error": _fill_langs({"zh": "网络错误，请重试", "en": "Network error, please retry"}),
    "auth_password_too_short": _fill_langs({"zh": "密码至少6位", "en": "Password must be at least 6 characters"}),

    # ── 信任网络 (trust) ────────────────────────────────
    "trust_added": _fill_langs({"zh": "信任关系添加成功", "en": "Trust relationship added successfully"}),
    "trust_removed": _fill_langs({"zh": "信任关系已移除", "en": "Trust relationship removed"}),
    "trust_add_failed": _fill_langs({"zh": "添加信任关系失败", "en": "Failed to add trust relationship"}),
    "trust_remove_failed": _fill_langs({"zh": "移除信任关系失败", "en": "Failed to remove trust relationship"}),
    "trust_no_permission": _fill_langs({"zh": "无权操作其他用户的信任网络", "en": "No permission to modify other user's trust network"}),
    "trust_target_not_found": _fill_langs({"zh": "被信任用户画册不存在", "en": "Trusted user's brochure not found"}),

    # ── 匹配 (match) ────────────────────────────────────
    "match_source_not_found": _fill_langs({"zh": "源用户画册不存在", "en": "Source user brochure not found"}),
    "match_no_results": _fill_langs({"zh": "暂无匹配结果，稍后再来看看", "en": "No matches found, check back later"}),
    "match_engine_running": _fill_langs({"zh": "🤖 AI 正在提取信息...", "en": "🤖 AI is extracting information..."}),
    "match_extract_complete": _fill_langs({"zh": "✅ AI 提取完成，请核对信息", "en": "✅ AI extraction complete, please verify"}),

    # ── 批量导入 (batch) ────────────────────────────────
    "batch_import_empty": _fill_langs({"zh": "导入列表不能为空", "en": "Import list cannot be empty"}),
    "batch_import_result": _fill_langs({"zh": "成功导入 {success} 个用户，失败 {fail} 个", "en": "Successfully imported {success} users, {fail} failed"}),
    "batch_import_db_error": _fill_langs({"zh": "写入数据库失败", "en": "Database write failed"}),

    # ── 链客宝同步 (chainke) ────────────────────────────
    "chainke_module_not_loaded": _fill_langs({"zh": "链客宝桥接模块未加载，同步跳过", "en": "Chainke bridge module not loaded, sync skipped"}),
    "chainke_sync_complete": _fill_langs({"zh": "同步完成", "en": "Sync completed"}),

    # ── 速率限制 ────────────────────────────────────────
    "rate_limit_exceeded": _fill_langs({"zh": "请求过于频繁，请稍后再试", "en": "Too Many Requests"}),

    # ── 访客 ────────────────────────────────────────────
    "visitor_logged": _fill_langs({"zh": "访问已记录", "en": "Visit logged"}),
    "brochure_expired": _fill_langs({"zh": "图册不存在或已失效", "en": "Brochure not found or expired"}),

    # ── 前端 UI 文案 ────────────────────────────────────
    "ui_app_name": _fill_langs({"zh": "AI数字名片", "en": "AI Digital Business Card"}),
    "ui_subtitle": _fill_langs({"zh": "链客宝 · 企业家智能商务厅", "en": "Chainke · Smart Business Hall"}),
    "ui_login": _fill_langs({"zh": "登录", "en": "Login"}),
    "ui_register": _fill_langs({"zh": "注册", "en": "Register"}),
    "ui_logout": _fill_langs({"zh": "退出", "en": "Logout"}),
    "ui_phone": _fill_langs({"zh": "手机号", "en": "Phone Number"}),
    "ui_password": _fill_langs({"zh": "密码", "en": "Password"}),
    "ui_name": _fill_langs({"zh": "姓名", "en": "Name"}),
    "ui_phone_placeholder": _fill_langs({"zh": "手机号", "en": "Phone Number"}),
    "ui_password_placeholder": _fill_langs({"zh": "密码（至少6位）", "en": "Password (min 6 chars)"}),
    "ui_name_placeholder": _fill_langs({"zh": "姓名", "en": "Your Name"}),
    "ui_login_loading": _fill_langs({"zh": "登录中...", "en": "Logging in..."}),
    "ui_register_loading": _fill_langs({"zh": "注册中...", "en": "Registering..."}),
    "ui_switch_to_register": _fill_langs({"zh": "没有账号？去注册", "en": "No account? Register"}),
    "ui_switch_to_login": _fill_langs({"zh": "已有账号？去登录", "en": "Already have an account? Login"}),
    "ui_new_brochure": _fill_langs({"zh": "+ 新建名片", "en": "+ New Card"}),
    "ui_loading": _fill_langs({"zh": "加载中...", "en": "Loading..."}),
    "ui_no_brochures_title": _fill_langs({"zh": "还没有数字名片", "en": "No digital cards yet"}),
    "ui_no_brochures_desc": _fill_langs({"zh": "创建你的第一张AI数字名片，开启商业连接", "en": "Create your first AI digital card and start business connections"}),
    "ui_create_first": _fill_langs({"zh": "创建我的名片", "en": "Create My Card"}),
    "ui_unnamed": _fill_langs({"zh": "未命名", "en": "Unnamed"}),
    "ui_updated_prefix": _fill_langs({"zh": "更新: ", "en": "Updated: "}),
    "ui_edit": _fill_langs({"zh": "编辑", "en": "Edit"}),
    "ui_preview": _fill_langs({"zh": "预览", "en": "Preview"}),
    "ui_share": _fill_langs({"zh": "分享", "en": "Share"}),
    "ui_link_copied": _fill_langs({"zh": "链接已复制", "en": "Link copied"}),
    "ui_share_title": _fill_langs({"zh": "我的数字名片", "en": "My Digital Card"}),
    "ui_logging_out": _fill_langs({"zh": "退出中...", "en": "Logging out..."}),
    "ui_offline_mode": _fill_langs({"zh": "📡 当前处于离线模式", "en": "📡 Currently offline"}),
    "ui_network_disconnected": _fill_langs({"zh": "网络已断开", "en": "Network disconnected"}),
    "ui_offline_hint": _fill_langs({"zh": "你正在查看已缓存的离线内容", "en": "You are viewing cached offline content"}),
    "ui_cached_pages": _fill_langs({"zh": "已缓存页面：", "en": "Cached pages:"}),
    "ui_cached_sync_hint": _fill_langs({"zh": "已缓存的内容将在恢复网络后同步更新", "en": "Cached content will sync when back online"}),
    "ui_reconnect": _fill_langs({"zh": "重新连接", "en": "Reconnect"}),
    "ui_editor_title": _fill_langs({"zh": "🪪 AI数字名片", "en": "🪪 AI Digital Card"}),
    "ui_editor_subtitle": _fill_langs({"zh": "智能创建 · 一键分享", "en": "Smart Create · One-click Share"}),
    "ui_upload_title": _fill_langs({"zh": "📤 上传名片", "en": "📤 Upload Card"}),
    "ui_upload_hint": _fill_langs({"zh": "支持图片 (JPG/PNG) 或 PDF 格式", "en": "Supports images (JPG/PNG) or PDF"}),
    "ui_upload_drag": _fill_langs({"zh": "拖拽文件到此处，或点击上传", "en": "Drag files here, or click to upload"}),
    "ui_upload_supported": _fill_langs({"zh": "支持 JPG / PNG / PDF", "en": "Supports JPG / PNG / PDF"}),
    "ui_purpose_title": _fill_langs({"zh": "🎯 你的名片用途是什么？", "en": "🎯 What's your card purpose?"}),
    "ui_purpose_hint": _fill_langs({"zh": "选择后系统将帮你突出展示重点信息", "en": "Select to highlight key info"}),
    "ui_ai_extract": _fill_langs({"zh": "🤖 AI 智能提取", "en": "🤖 AI Smart Extract"}),
    "ui_review_title": _fill_langs({"zh": "✏️ 确认信息", "en": "✏️ Review Info"}),
    "ui_review_hint": _fill_langs({"zh": "AI 已提取以下字段，请核对修改", "en": "AI extracted the fields below, please verify"}),
    "ui_purpose_label": _fill_langs({"zh": "名片用途:", "en": "Card purpose:"}),
    "ui_back": _fill_langs({"zh": "← 返回", "en": "← Back"}),
    "ui_next": _fill_langs({"zh": "下一步 →", "en": "Next →"}),
    "ui_preview_title_label": _fill_langs({"zh": "👀 预览图册", "en": "👀 Preview Album"}),
    "ui_preview_hint": _fill_langs({"zh": "翻页效果预览", "en": "Flip effect preview"}),
    "ui_edit_btn": _fill_langs({"zh": "← 编辑", "en": "← Edit"}),
    "ui_publish": _fill_langs({"zh": "发布图册 →", "en": "Publish →"}),
    "ui_publish_success": _fill_langs({"zh": "🎉 发布成功！", "en": "🎉 Published!"}),
    "ui_publish_desc": _fill_langs({"zh": "您的AI数字名片已创建", "en": "Your AI digital card has been created"}),
    "ui_share_link": _fill_langs({"zh": "分享链接", "en": "Share Link"}),
    "ui_copy_link": _fill_langs({"zh": "📋 复制链接", "en": "📋 Copy Link"}),
    "ui_match_results": _fill_langs({"zh": "🤝 供需匹配结果", "en": "🤝 Match Results"}),
    "ui_home": _fill_langs({"zh": "🏠 首页", "en": "🏠 Home"}),
    "ui_new": _fill_langs({"zh": "🔄 新建", "en": "🔄 New"}),
    "ui_publishing": _fill_langs({"zh": "📤 正在发布...", "en": "📤 Publishing..."}),
    "ui_publish_failed": _fill_langs({"zh": "❌ 发布失败: ", "en": "❌ Publish failed: "}),
    "ui_contact_me": _fill_langs({"zh": "💬 联系我", "en": "💬 Contact Me"}),
    "ui_views": _fill_langs({"zh": "次浏览", "en": "views"}),
    "ui_loading_brochure": _fill_langs({"zh": "加载图册中...", "en": "Loading album..."}),
    "ui_contact_request_sent": _fill_langs({"zh": "💬 联系方式已发送请求", "en": "💬 Contact request sent"}),
    "ui_steps_upload": _fill_langs({"zh": "上传/用途", "en": "Upload"}),
    "ui_steps_edit": _fill_langs({"zh": "编辑", "en": "Edit"}),
    "ui_steps_preview": _fill_langs({"zh": "预览", "en": "Preview"}),
    "ui_steps_match": _fill_langs({"zh": "匹配", "en": "Match"}),
    "ui_purpose_partner": _fill_langs({"zh": "找合作伙伴", "en": "Find Partners"}),
    "ui_purpose_partner_desc": _fill_langs({"zh": "寻找技术/业务合作方", "en": "Find tech/business partners"}),
    "ui_purpose_client": _fill_langs({"zh": "找客户", "en": "Find Clients"}),
    "ui_purpose_client_desc": _fill_langs({"zh": "展示产品或服务能力", "en": "Showcase products/services"}),
    "ui_purpose_investor": _fill_langs({"zh": "找投资人", "en": "Find Investors"}),
    "ui_purpose_investor_desc": _fill_langs({"zh": "突出团队与融资亮点", "en": "Highlight team & funding"}),
    "ui_purpose_supplier": _fill_langs({"zh": "找供应商", "en": "Find Suppliers"}),
    "ui_purpose_supplier_desc": _fill_langs({"zh": "展示采购需求与合作", "en": "Show procurement needs"}),
    "ui_field_name": _fill_langs({"zh": "姓名", "en": "Name"}),
    "ui_field_phone": _fill_langs({"zh": "手机", "en": "Phone"}),
    "ui_field_email": _fill_langs({"zh": "邮箱", "en": "Email"}),
    "ui_field_wechat": _fill_langs({"zh": "微信", "en": "WeChat"}),
    "ui_field_company": _fill_langs({"zh": "公司", "en": "Company"}),
    "ui_field_title": _fill_langs({"zh": "职位", "en": "Title"}),
    "ui_field_name_ph": _fill_langs({"zh": "姓名", "en": "Name"}),
    "ui_field_phone_ph": _fill_langs({"zh": "手机号", "en": "Phone"}),
    "ui_field_email_ph": _fill_langs({"zh": "邮箱", "en": "Email"}),
    "ui_field_wechat_ph": _fill_langs({"zh": "微信号", "en": "WeChat ID"}),
    "ui_field_company_ph": _fill_langs({"zh": "公司名称", "en": "Company Name"}),
    "ui_field_title_ph": _fill_langs({"zh": "职位", "en": "Title"}),
    "ui_page_cover": _fill_langs({"zh": "个人封面", "en": "Cover"}),
    "ui_page_contact": _fill_langs({"zh": "联系方式", "en": "Contact"}),
    "ui_page_company": _fill_langs({"zh": "企业信息", "en": "Company"}),
    "ui_page_qrcode": _fill_langs({"zh": "二维码", "en": "QR Code"}),
    "ui_page_detail": _fill_langs({"zh": "详情", "en": "Details"}),
    "ui_scan_qrcode": _fill_langs({"zh": "扫码添加好友", "en": "Scan to add friend"}),
    "ui_purpose_hint_partner": _fill_langs({"zh": "致力于寻找技术/业务合作伙伴，欢迎洽谈合作", "en": "Looking for tech/business partners, welcome to discuss"}),
    "ui_purpose_hint_client": _fill_langs({"zh": "致力于拓展客户资源，提供优质产品与服务", "en": "Looking for clients, offering quality products & services"}),
    "ui_purpose_hint_investor": _fill_langs({"zh": "正在融资阶段，期待与投资人交流", "en": "Currently fundraising, looking forward to connecting with investors"}),
    "ui_purpose_hint_supplier": _fill_langs({"zh": "寻求优质供应商合作伙伴，共建供应链", "en": "Seeking quality supplier partners"}),
    "ui_brochure_title_suffix": _fill_langs({"zh": "的数字名片", "en": "'s Digital Card"}),
    "ui_contact_item_phone": _fill_langs({"zh": "电话", "en": "Phone"}),
    "ui_contact_item_email": _fill_langs({"zh": "邮箱", "en": "Email"}),
    "ui_contact_item_wechat": _fill_langs({"zh": "微信", "en": "WeChat"}),
    "ui_section_bio": _fill_langs({"zh": "📝 个人简介", "en": "📝 Bio"}),
    "ui_section_contact": _fill_langs({"zh": "📞 联系方式", "en": "📞 Contact"}),
    "ui_section_tags": _fill_langs({"zh": "🏷️ 标签", "en": "🏷️ Tags"}),
    "ui_footer_version": _fill_langs({"zh": "AI数字名片 v2.1", "en": "AI Digital Card v2.1"}),
    "ui_visited_count": _fill_langs({"zh": "👁️ 已被浏览 {count} 次", "en": "👁️ Viewed {count} times"}),
    "ui_page_nav": _fill_langs({"zh": "第 {current}/{total} 页", "en": "Page {current}/{total}"}),

    # ── 卡片编辑页 (Card Editor) ──────────────────────────
    "card_editor_title": _fill_langs({"zh": "编辑名片", "en": "Edit Card"}),
    "upload_brochure": _fill_langs({"zh": "上传名片", "en": "Upload Brochure"}),
    "card_purpose": _fill_langs({"zh": "你的名片用途是什么", "en": "Purpose of your card"}),
    "card_cover": _fill_langs({"zh": "个人封面", "en": "Personal Cover"}),
    "company_info": _fill_langs({"zh": "企业信息", "en": "Company Info"}),
    "company_name": _fill_langs({"zh": "公司名称", "en": "Company Name"}),
    "position_title": _fill_langs({"zh": "职位", "en": "Position"}),
    "contact_info": _fill_langs({"zh": "联系方式", "en": "Contact Info"}),
    "share_link": _fill_langs({"zh": "分享链接", "en": "Share Link"}),
    "step_company": _fill_langs({"zh": "企业信息", "en": "Company Info"}),
    "step_contact": _fill_langs({"zh": "联系方式", "en": "Contact Info"}),
    "step_preview": _fill_langs({"zh": "预览", "en": "Preview"}),
    "purpose_business": _fill_langs({"zh": "业务合作方", "en": "Business Partner"}),
    "purpose_supplier": _fill_langs({"zh": "优质供应商", "en": "Supplier"}),
    "purpose_investor": _fill_langs({"zh": "投资方", "en": "Investor"}),
    "purpose_employee": _fill_langs({"zh": "企业员工", "en": "Employee"}),
    "purpose_personal": _fill_langs({"zh": "个人名片", "en": "Personal"}),
    "find_partner": _fill_langs({"zh": "找合作伙伴", "en": "Find Partner"}),
    "find_supplier": _fill_langs({"zh": "找供应商", "en": "Find Supplier"}),
    "find_investor": _fill_langs({"zh": "找投资人", "en": "Find Investor"}),
    "match_result": _fill_langs({"zh": "供需匹配结果", "en": "Match Results"}),

    # ── 画册查看页 (Viewer) ──────────────────────────────
    "viewer_title": _fill_langs({"zh": "数字名片", "en": "Digital Card"}),
    "loading_brochure": _fill_langs({"zh": "加载图册中", "en": "Loading..."}),
    "initialized": _fill_langs({"zh": "初始化翻页引擎", "en": "Initializing..."}),
    "page_indicator": _fill_langs({"zh": "分页指示器", "en": "Page Indicator"}),
    "supply_chain": _fill_langs({"zh": "共建供应链", "en": "Supply Chain"}),
    "service_us": _fill_langs({"zh": "为您服务", "en": "Our Services"}),
    "why_choose_us": _fill_langs({"zh": "为什么选择我们", "en": "Why Choose Us"}),
    "main_category": _fill_langs({"zh": "主营品类", "en": "Main Category"}),
    "product_manager": _fill_langs({"zh": "产品经理", "en": "Product Manager"}),
    "professional_team": _fill_langs({"zh": "专业团队 · 品质保障 · 售后无忧", "en": "Professional Team"}),
    "experience": _fill_langs({"zh": "丰富的行业经验与落地案例", "en": "Rich Experience"}),

    # ── 认证扩展 (auth) ──────────────────────────────────
    "auth_cannot_verify": _fill_langs({"zh": "无法验证凭证", "en": "Cannot verify credentials"}),
    "auth_wechat_service_failed": _fill_langs({"zh": "微信登录服务调用失败", "en": "WeChat login service call failed"}),
    "auth_wechat_login_failed": _fill_langs({"zh": "微信登录失败", "en": "WeChat login failed"}),
    "auth_wechat_no_openid": _fill_langs({"zh": "微信登录失败: 未获取到 openid", "en": "WeChat login failed: openid not obtained"}),
    "auth_register_success": _fill_langs({"zh": "注册成功", "en": "Registration successful"}),
    "auth_login_success": _fill_langs({"zh": "登录成功", "en": "Login successful"}),
    "auth_password_reset_sent": _fill_langs({"zh": "密码重置链接已发送", "en": "Password reset link sent"}),
    "auth_session_expired": _fill_langs({"zh": "会话已过期，请重新登录", "en": "Session expired, please login again"}),

    # ── 画册扩展 (brochure) ──────────────────────────────
    "brochure_invalid_purpose": _fill_langs({"zh": "不支持的用途", "en": "Invalid purpose"}),
    "brochure_not_found_or_expired": _fill_langs({"zh": "画册不存在或链接已失效", "en": "Brochure not found or link expired"}),
    "brochure_no_permission_publish": _fill_langs({"zh": "无权发布此画册", "en": "No permission to publish this brochure"}),
    "brochure_no_permission_operate": _fill_langs({"zh": "无权操作此画册", "en": "No permission to operate on this brochure"}),
    "brochure_published": _fill_langs({"zh": "画册已发布", "en": "Brochure published"}),
    "brochure_draft_saved": _fill_langs({"zh": "草稿已保存", "en": "Draft saved"}),
    "brochure_upload_success": _fill_langs({"zh": "图片上传成功", "en": "Image uploaded successfully"}),
    "brochure_share_token_refreshed": _fill_langs({"zh": "分享链接已刷新", "en": "Share link refreshed"}),
    "brochure_clone_success": _fill_langs({"zh": "画册已复制", "en": "Brochure cloned successfully"}),

    # ── 团队管理 (team) ──────────────────────────────────
    "team_not_found": _fill_langs({"zh": "团队不存在", "en": "Team not found"}),
    "team_created": _fill_langs({"zh": "团队创建成功", "en": "Team created successfully"}),
    "team_updated": _fill_langs({"zh": "团队信息已更新", "en": "Team updated successfully"}),
    "team_deleted": _fill_langs({"zh": "团队已删除", "en": "Team deleted"}),
    "team_no_permission_admin": _fill_langs({"zh": "权限不足，需要管理员或所有者权限", "en": "Insufficient permissions, admin or owner role required"}),
    "team_no_permission_owner": _fill_langs({"zh": "权限不足，需要所有者权限", "en": "Insufficient permissions, owner role required"}),
    "team_invite_contact_required": _fill_langs({"zh": "邮箱或手机号至少需要一项", "en": "Email or phone number is required"}),
    "team_role_updated": _fill_langs({"zh": "角色更新成功", "en": "Role updated successfully"}),
    "team_title_updated": _fill_langs({"zh": "职位更新成功", "en": "Title updated successfully"}),
    "team_cannot_remove_owner": _fill_langs({"zh": "不能移除团队所有者", "en": "Cannot remove the team owner"}),
    "team_member_removed": _fill_langs({"zh": "成员已移除", "en": "Member removed successfully"}),
    "team_join_success": _fill_langs({"zh": "加入团队成功", "en": "Joined team successfully"}),
    "team_invite_sent": _fill_langs({"zh": "邀请已发送", "en": "Invitation sent"}),
    "team_invite_accepted": _fill_langs({"zh": "已接受邀请", "en": "Invitation accepted"}),
    "team_invite_declined": _fill_langs({"zh": "已拒绝邀请", "en": "Invitation declined"}),
    "team_invite_cancelled": _fill_langs({"zh": "邀请已取消", "en": "Invitation cancelled"}),
    "team_join_member_info_failed": _fill_langs({"zh": "加入成功但获取成员信息失败", "en": "Joined but failed to get member info"}),
    "team_max_members_reached": _fill_langs({"zh": "团队成员数已达上限", "en": "Team member limit reached"}),
    "team_invite_expired": _fill_langs({"zh": "邀请已过期", "en": "Invitation expired"}),

    # ── 支付 (payment) ───────────────────────────────────
    "payment_unsupported_channel": _fill_langs({"zh": "不支持的支付渠道", "en": "Unsupported payment channel"}),
    "payment_free_no_purchase": _fill_langs({"zh": "免费会员无需购买", "en": "Free membership does not require purchase"}),
    "payment_existing_pending_order": _fill_langs({"zh": "您已有未支付的订单，请先完成支付", "en": "You have an unpaid order, please complete payment first"}),
    "payment_channel_order_failed": _fill_langs({"zh": "支付渠道下单失败", "en": "Payment channel order failed"}),
    "payment_order_not_found": _fill_langs({"zh": "订单不存在", "en": "Order not found"}),
    "payment_no_permission_order": _fill_langs({"zh": "无权查看该订单", "en": "No permission to view this order"}),
    "payment_notify_success": _fill_langs({"zh": "支付通知处理成功", "en": "Payment notification processed successfully"}),
    "payment_signature_failed": _fill_langs({"zh": "签名验证失败", "en": "Signature verification failed"}),
    "payment_success": _fill_langs({"zh": "支付成功", "en": "Payment successful"}),
    "payment_refund_success": _fill_langs({"zh": "退款成功", "en": "Refund successful"}),
    "payment_refund_failed": _fill_langs({"zh": "退款失败", "en": "Refund failed"}),
    "payment_subscription_expired": _fill_langs({"zh": "会员已到期，请续费", "en": "Membership expired, please renew"}),

    # ── 信任网络扩展 (trust) ────────────────────────────
    "trust_cannot_trust_self": _fill_langs({"zh": "不能信任自己", "en": "Cannot trust yourself"}),
    "trust_already_exists": _fill_langs({"zh": "已建立信任关系", "en": "Trust relationship already exists"}),
    "trust_not_found": _fill_langs({"zh": "信任关系不存在", "en": "Trust relationship not found"}),
    "trust_level_promoted": _fill_langs({"zh": "信任等级已提升", "en": "Trust level upgraded"}),
    "trust_level_demoted": _fill_langs({"zh": "信任等级已降低", "en": "Trust level downgraded"}),

    # ── 访客/兴趣 (visitor) ─────────────────────────────
    "visitor_no_permission": _fill_langs({"zh": "无权查看此画册的访客记录", "en": "No permission to view visitor logs"}),
    "visitor_no_permission_stats": _fill_langs({"zh": "无权查看此画册的统计", "en": "No permission to view visitor stats"}),
    "visitor_interest_expressed": _fill_langs({"zh": "兴趣已表达", "en": "Interest expressed"}),
    "visitor_anonymous": _fill_langs({"zh": "匿名访客", "en": "Anonymous visitor"}),

    # ── GDPR 数据合规 ────────────────────────────────────
    "gdpr_export_success": _fill_langs({"zh": "数据导出成功", "en": "Data export successful"}),
    "gdpr_account_deleted": _fill_langs({"zh": "账户已删除（匿名化），所有个人数据已移除", "en": "Account deleted (anonymized), all personal data removed"}),
    "gdpr_delete_confirm": _fill_langs({"zh": "确定要删除账户吗？此操作不可撤销", "en": "Are you sure you want to delete your account? This action is irreversible"}),
    "gdpr_export_in_progress": _fill_langs({"zh": "数据导出正在准备中", "en": "Data export is being prepared"}),

    # ── API Key 管理 ─────────────────────────────────────
    "api_key_not_found": _fill_langs({"zh": "API Key 不存在", "en": "API Key not found"}),
    "api_key_created": _fill_langs({"zh": "API Key 创建成功", "en": "API Key created successfully"}),
    "api_key_revoked": _fill_langs({"zh": "API Key 已吊销", "en": "API Key revoked"}),
    "api_key_save_warning": _fill_langs({"zh": "请立即保存此 Key，它只会被显示这一次", "en": "Save this key now, it will only be shown this once"}),

    # ── 标签管理 (tag) ────────────────────────────────────
    "tag_not_found": _fill_langs({"zh": "标签不存在", "en": "Tag not found"}),
    "tag_no_permission_delete": _fill_langs({"zh": "无权删除此标签", "en": "No permission to delete this tag"}),
    "tag_deleted": _fill_langs({"zh": "标签已删除", "en": "Tag deleted"}),
    "tag_added": _fill_langs({"zh": "标签添加成功", "en": "Tag added successfully"}),

    # ── A/B 测试 ─────────────────────────────────────────
    "ab_test_created": _fill_langs({"zh": "实验创建成功", "en": "Experiment created successfully"}),
    "ab_test_updated": _fill_langs({"zh": "实验更新成功", "en": "Experiment updated successfully"}),
    "ab_test_deleted": _fill_langs({"zh": "实验已删除", "en": "Experiment deleted"}),
    "ab_test_not_found": _fill_langs({"zh": "实验不存在", "en": "Experiment not found"}),
    "ab_test_started": _fill_langs({"zh": "实验已启动", "en": "Experiment started"}),
    "ab_test_paused": _fill_langs({"zh": "实验已暂停", "en": "Experiment paused"}),
    "ab_test_resumed": _fill_langs({"zh": "实验已恢复", "en": "Experiment resumed"}),
    "ab_test_stopped": _fill_langs({"zh": "实验已结束", "en": "Experiment stopped"}),
    "ab_test_event_logged": _fill_langs({"zh": "事件已记录", "en": "Event logged"}),
    "ab_test_only_draft_modifiable": _fill_langs({"zh": "仅草稿状态可修改", "en": "Only draft experiments can be modified"}),
    "ab_test_invalid_status_start": _fill_langs({"zh": "当前状态不允许启动", "en": "Current status does not allow starting"}),
    "ab_test_min_variants": _fill_langs({"zh": "需要至少 2 个变体（包含对照组）", "en": "At least 2 variants (including control) are required"}),
    "ab_test_only_running_pause": _fill_langs({"zh": "仅运行中的实验可暂停", "en": "Only running experiments can be paused"}),
    "ab_test_only_paused_resume": _fill_langs({"zh": "仅暂停中的实验可恢复", "en": "Only paused experiments can be resumed"}),
    "ab_test_only_active_stop": _fill_langs({"zh": "仅运行中或暂停中的实验可结束", "en": "Only running or paused experiments can be stopped"}),
    "ab_test_variant_not_found": _fill_langs({"zh": "变体不存在", "en": "Variant not found"}),

    # ── 供需匹配 (match) ─────────────────────────────────
    "match_record_not_found": _fill_langs({"zh": "匹配记录不存在", "en": "Match record not found"}),
    "match_no_permission": _fill_langs({"zh": "无权操作此记录", "en": "No permission to operate on this record"}),
    "match_no_permission_record": _fill_langs({"zh": "无权操作此匹配记录", "en": "No permission to operate on this match record"}),
    "match_target_not_found": _fill_langs({"zh": "目标用户不存在", "en": "Target user not found"}),
    "match_payment_required": _fill_langs({"zh": "需要付费会员才能解锁联系方式，请升级会员", "en": "Paid membership required to view contact info, please upgrade"}),
    "match_quota_exhausted": _fill_langs({"zh": "本月解锁配额已用尽，请升级会员获取更多配额", "en": "Monthly unlock quota exhausted, please upgrade for more quota"}),
    "match_status_updated": _fill_langs({"zh": "状态已更新", "en": "Status updated"}),

    # ── 推荐系统 (recommend) ─────────────────────────────
    "recommend_invalid_strategy": _fill_langs({"zh": "不支持的推荐策略", "en": "Unsupported recommendation strategy"}),
    "recommend_invalid_purpose": _fill_langs({"zh": "不支持的用途", "en": "Unsupported purpose"}),
    "recommend_target_not_found": _fill_langs({"zh": "目标用户不存在", "en": "Target user not found"}),
    "recommend_rag_failed": _fill_langs({"zh": "RAG 查询失败", "en": "RAG query failed"}),

    # ── 第三方集成 (integration) ────────────────────────
    "integration_already_exists": _fill_langs({"zh": "集成已存在，请勿重复创建", "en": "Integration already exists, do not duplicate"}),
    "integration_unsupported_provider": _fill_langs({"zh": "不支持的提供商", "en": "Unsupported provider"}),
    "integration_not_enabled": _fill_langs({"zh": "集成未启用", "en": "Integration not enabled"}),
    "integration_no_enabled": _fill_langs({"zh": "没有已启用的集成", "en": "No enabled integrations"}),
    "integration_not_found": _fill_langs({"zh": "集成配置不存在", "en": "Integration config not found"}),
    "integration_webhook_no_test": _fill_langs({"zh": "Webhook 无需连接测试，请发送测试事件验证", "en": "Webhook does not require connectivity test, send a test event to verify"}),

    # ── 分享 (share) ─────────────────────────────────────
    "share_not_found": _fill_langs({"zh": "名片不存在或链接已失效", "en": "Card not found or link expired"}),
    "share_qr_failed": _fill_langs({"zh": "QR 码生成失败", "en": "QR code generation failed"}),
    "share_nfc_failed": _fill_langs({"zh": "NFC 配置生成失败", "en": "NFC config generation failed"}),

    # ── SSO 单点登录 ─────────────────────────────────────
    "sso_unsupported_provider": _fill_langs({"zh": "不支持的 SSO 提供商或配置不完整", "en": "Unsupported SSO provider or incomplete config"}),
    "sso_auth_failed": _fill_langs({"zh": "SSO 授权失败", "en": "SSO authorization failed"}),
    "sso_missing_code": _fill_langs({"zh": "缺少授权码", "en": "Missing authorization code"}),
    "sso_invalid_state": _fill_langs({"zh": "无效的 state 参数，请重新发起登录", "en": "Invalid state parameter, please re-initiate login"}),
    "sso_token_exchange_failed": _fill_langs({"zh": "令牌交换失败", "en": "Token exchange failed"}),
    "sso_userinfo_failed": _fill_langs({"zh": "获取用户信息失败", "en": "Failed to fetch user info"}),
    "sso_invalid_jwt": _fill_langs({"zh": "无效的 JWT 令牌", "en": "Invalid JWT token"}),
    "sso_no_unique_id": _fill_langs({"zh": "无法获取 SSO 唯一标识", "en": "Cannot get SSO unique identifier"}),
    "sso_account_already_bound": _fill_langs({"zh": "账号已被其他用户绑定", "en": "Account already bound to another user"}),
    "sso_account_bound": _fill_langs({"zh": "账号绑定成功", "en": "Account bound successfully"}),
    "sso_account_unbound": _fill_langs({"zh": "账号解绑成功", "en": "Account unbound successfully"}),

    # ── 审批流 (approval) ────────────────────────────────
    "approval_pending": _fill_langs({"zh": "待审批", "en": "Pending approval"}),
    "approval_approved": _fill_langs({"zh": "已通过", "en": "Approved"}),
    "approval_rejected": _fill_langs({"zh": "已拒绝", "en": "Rejected"}),
    "approval_submitted": _fill_langs({"zh": "审批已提交", "en": "Approval submitted"}),
    "approval_no_permission": _fill_langs({"zh": "无权审批", "en": "No permission to approve"}),
    "approval_not_found": _fill_langs({"zh": "审批记录不存在", "en": "Approval record not found"}),
    "approval_already_processed": _fill_langs({"zh": "审批已被处理", "en": "Approval already processed"}),

    # ── 用户管理 (user) ──────────────────────────────────
    "user_profile_updated": _fill_langs({"zh": "个人信息已更新", "en": "Profile updated successfully"}),
    "user_avatar_updated": _fill_langs({"zh": "头像已更新", "en": "Avatar updated successfully"}),
    "user_password_updated": _fill_langs({"zh": "密码已修改", "en": "Password updated successfully"}),
    "user_account_locked": _fill_langs({"zh": "账户已被锁定", "en": "Account has been locked"}),
    "user_account_unlocked": _fill_langs({"zh": "账户已解锁", "en": "Account unlocked"}),

    # ── 批量导入扩展 (batch import) ──────────────────────
    "batch_import_format_error": _fill_langs({"zh": "导入格式错误", "en": "Import format error"}),
    "batch_import_too_large": _fill_langs({"zh": "导入数据过大，请分批导入", "en": "Import data too large, please batch split"}),

    # ── 批量操作 (batch operation) ───────────────────────
    "batch_operation_complete": _fill_langs({"zh": "批量操作完成", "en": "Batch operation completed"}),
    "batch_operation_partial": _fill_langs({"zh": "批量操作部分失败", "en": "Batch operation partially failed"}),
    "batch_operation_failed": _fill_langs({"zh": "批量操作失败", "en": "Batch operation failed"}),

    # ── 通知 (notification) ──────────────────────────────
    "notification_not_found": _fill_langs({"zh": "通知不存在", "en": "Notification not found"}),
    "notification_marked_read": _fill_langs({"zh": "已标记为已读", "en": "Marked as read"}),
    "notification_all_read": _fill_langs({"zh": "全部标记为已读", "en": "All marked as read"}),

    # ── Webhook ──────────────────────────────────────────
    "webhook_not_found": _fill_langs({"zh": "Webhook 不存在", "en": "Webhook not found"}),
    "webhook_event_payload_too_large": _fill_langs({"zh": "事件 payload 过大", "en": "Event payload too large"}),
    "webhook_delivery_failed": _fill_langs({"zh": "Webhook 推送失败", "en": "Webhook delivery failed"}),
    "webhook_delivery_success": _fill_langs({"zh": "Webhook 推送成功", "en": "Webhook delivered successfully"}),
    "webhook_disabled": _fill_langs({"zh": "Webhook 已禁用", "en": "Webhook disabled"}),
    "webhook_enabled": _fill_langs({"zh": "Webhook 已启用", "en": "Webhook enabled"}),

    # ── 上传/媒体 (media) ────────────────────────────────
    "media_upload_failed": _fill_langs({"zh": "上传失败", "en": "Upload failed"}),
    "media_file_too_large": _fill_langs({"zh": "文件过大", "en": "File too large"}),
    "media_unsupported_format": _fill_langs({"zh": "不支持的格式", "en": "Unsupported format"}),
    "media_delete_success": _fill_langs({"zh": "文件已删除", "en": "File deleted"}),

    # ── 数据校验 ─────────────────────────────────────────
    "validation_required_field": _fill_langs({"zh": "此字段为必填项", "en": "This field is required"}),
    "validation_invalid_phone": _fill_langs({"zh": "手机号格式不正确", "en": "Invalid phone number format"}),
    "validation_invalid_email": _fill_langs({"zh": "邮箱格式不正确", "en": "Invalid email format"}),
    "validation_invalid_url": _fill_langs({"zh": "URL 格式不正确", "en": "Invalid URL format"}),
    "validation_max_length": _fill_langs({"zh": "超出最大长度限制", "en": "Exceeds maximum length"}),
}


def t(key: str, lang: str = "zh") -> str:
    """根据 key 和语言代码返回翻译文本。

    Args:
        key: 翻译键名
        lang: 语言代码 (zh / en / ja / ko / es / fr / de / pt / ru / ar / th / vi)

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
        12种语言之一: zh / en / ja / ko / es / fr / de / pt / ru / ar / th / vi
    """
    if not accept_language:
        return "zh"
    accept_language = accept_language.lower()
    # 语言检测优先级列表 (按常见度排序)
    lang_map = [
        ("zh", "zh"), ("en", "en"), ("ja", "ja"), ("ko", "ko"),
        ("es", "es"), ("fr", "fr"), ("de", "de"), ("pt", "pt"),
        ("ru", "ru"), ("ar", "ar"), ("th", "th"), ("vi", "vi"),
    ]
    for code, lang in lang_map:
        if code in accept_language:
            return lang
    # 默认英文
    return "en"
