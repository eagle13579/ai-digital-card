/**
 * 测试数据 - AI数智名片小程序
 */
const store = require('./store')

const TEST_USERS = {
  free: {
    token: 'mock_token_free_001',
    user_id: 'u001',
    memberLevel: 'free',
    userInfo: {
      id: 'u001',
      name: '张伟',
      avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20man%20portrait%20headshot%20clean%20white%20background&image_size=square',
      phone: '13800138000',
      email: 'zhangwei@example.com',
      wechat: 'zhangwei_product',
      company: '科技创新有限公司',
      title: '产品经理',
      bio: '5年互联网产品经理经验',
    },
  },
  silver: {
    token: 'mock_token_silver_002',
    user_id: 'u002',
    memberLevel: 'silver',
    userInfo: {
      id: 'u002',
      name: '李娜',
      avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20woman%20portrait%20headshot%20elegant%20clean%20white%20background&image_size=square',
      phone: '13900139000',
      email: 'lina@example.com',
      wechat: 'lina_finance',
      company: '金融投资集团',
      title: '投资总监',
      bio: '10年金融行业经验',
    },
  },
  gold: {
    token: 'mock_token_gold_003',
    user_id: 'u003',
    memberLevel: 'gold',
    userInfo: {
      id: 'u003',
      name: '王强',
      avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20tech%20leader%20man%20portrait%20headshot%20smart%20clean%20white%20background&image_size=square',
      phone: '13700137000',
      email: 'wangqiang@example.com',
      wechat: 'wangqiang_ai',
      company: '人工智能研究院',
      title: '首席技术官',
      bio: '15年人工智能领域经验',
    },
  },
}

const TEST_BROCHURES = [
  {
    id: 'b001',
    title: 'AI数智名片 - 张伟',
    cover: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20business%20man%20portrait%20headshot%20clean%20background&image_size=square',
    view_count: 128,
    pages_count: 5,
    user_name: '张伟',
    user_company: '科技创新有限公司',
    user_title: '产品经理',
    user_avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20man%20portrait%20headshot%20clean%20white%20background&image_size=square',
    purpose: 'partner',
    status: 'active',
    share_token: 'share_b001_token',
    user_id: 'u001',
    pages: [
      {
        type: 'cover',
        title: '张伟的AI数智名片',
        subtitle: '科技创新有限公司 · 产品经理',
        avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20man%20portrait%20headshot%20clean%20white%20background&image_size=square',
      },
      {
        type: 'profile',
        name: '张伟',
        title: '产品经理',
        company: '科技创新有限公司',
        bio: '5年互联网产品经理经验，擅长用户增长、产品策略和数据分析。曾负责多款千万级用户产品的设计与迭代，对用户体验有深刻理解。',
        contact: {
          phone: '13800138000',
          email: 'zhangwei@example.com',
          wechat: 'zhangwei_product',
        },
      },
      {
        type: 'resources',
        provides: ['产品设计', '用户研究', '数据分析', '增长策略'],
        needs: ['技术开发', '市场推广', '投资合作'],
        purpose: 'partner',
      },
      {
        type: 'company',
        name: '科技创新有限公司',
        industry: '互联网',
        size: '51-100人',
        desc: '科技创新有限公司专注于互联网产品研发和创新，致力于为用户提供优质的数字化解决方案。',
        development: '2020年：公司成立\n2022年：获得天使轮融资\n2024年：产品用户突破1000万',
        images: [
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=modern%20tech%20company%20office%20interior%20creative%20workspace&image_size=landscape_4_3',
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=startup%20team%20meeting%20brainstorming%20whiteboard&image_size=landscape_4_3',
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=digital%20product%20design%20wireframe%20mockup%20UI&image_size=landscape_4_3',
        ],
      },
      {
        type: 'contact',
        name: '张伟',
        phone: '13800138000',
        email: 'zhangwei@example.com',
        wechat: 'zhangwei_product',
        company: '科技创新有限公司',
      },
    ],
  },
  {
    id: 'b002',
    title: '投资总监名片 - 李娜',
    cover: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20business%20woman%20portrait%20headshot%20elegant%20clean%20background&image_size=square',
    view_count: 256,
    pages_count: 7,
    user_name: '李娜',
    user_company: '金融投资集团',
    user_title: '投资总监',
    user_avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20woman%20portrait%20headshot%20elegant%20clean%20white%20background&image_size=square',
    purpose: 'investor',
    status: 'active',
    share_token: 'share_b002_token',
    user_id: 'u002',
    pages: [
      {
        type: 'cover',
        title: '李娜的AI数智名片',
        subtitle: '金融投资集团 · 投资总监',
        avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20woman%20portrait%20headshot%20elegant%20clean%20white%20background&image_size=square',
      },
      {
        type: 'profile',
        name: '李娜',
        title: '投资总监',
        company: '金融投资集团',
        bio: '拥有10年金融行业经验，专注于股权投资、并购重组和资产管理领域。曾成功主导多个亿元级投资项目，帮助企业实现跨越式发展。',
        contact: {
          phone: '13900139000',
          email: 'lina@example.com',
          wechat: 'lina_finance',
        },
      },
      {
        type: 'resources',
        provides: ['资金投资', '并购重组', '资源对接', '投后管理'],
        needs: ['优质项目', '技术人才', '合作伙伴'],
        purpose: 'investor',
      },
      {
        type: 'company',
        name: '金融投资集团',
        industry: '金融投资',
        size: '501-1000人',
        desc: '金融投资集团是一家专注于股权投资和并购重组的综合性投资机构，管理资产规模超过500亿元人民币。公司致力于发现和培育具有高成长潜力的企业，为其提供资金支持和战略指导。',
        development: '2015年：公司成立，获得首轮融资\n2018年：管理规模突破100亿元\n2021年：完成IPO上市\n2024年：管理规模突破500亿元',
        images: [
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=luxury%20finance%20company%20office%20building%20modern%20architecture&image_size=landscape_4_3',
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=investment%20meeting%20boardroom%20professional%20business%20people&image_size=landscape_4_3',
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=stock%20market%20financial%20charts%20data%20visualization&image_size=landscape_4_3',
        ],
      },
      {
        type: 'case',
        index: 1,
        name: '科技企业A轮投资',
        date: '2023年',
        desc: '主导投资某科技创新企业A轮融资，投资金额5000万元。通过专业的投后管理，帮助企业实现技术突破和市场拓展，企业估值在两年内增长了300%。',
        images: [
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=tech%20startup%20team%20celebrating%20funding%20success&image_size=landscape_4_3',
        ],
      },
      {
        type: 'case',
        index: 2,
        name: '跨境并购项目',
        date: '2024年',
        desc: '成功完成某跨境并购项目，帮助国内企业收购海外优质资产。项目总金额达2亿美元，实现了企业国际化战略布局。',
        images: [
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=international%20business%20merger%20cross%20border%20deal&image_size=landscape_4_3',
        ],
      },
      {
        type: 'contact',
        name: '李娜',
        phone: '13900139000',
        email: 'lina@example.com',
        wechat: 'lina_finance',
        company: '金融投资集团',
      },
    ],
  },
  {
    id: 'b003',
    title: 'CTO个人名片 - 王强',
    cover: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20tech%20leader%20man%20portrait%20headshot%20smart%20clean%20background&image_size=square',
    view_count: 512,
    pages_count: 8,
    user_name: '王强',
    user_company: '人工智能研究院',
    user_title: '首席技术官',
    user_avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20tech%20leader%20man%20portrait%20headshot%20smart%20clean%20white%20background&image_size=square',
    purpose: 'employee',
    status: 'active',
    share_token: 'share_b003_token',
    user_id: 'u003',
    pages: [
      {
        type: 'cover',
        title: '王强的AI数智名片',
        subtitle: '人工智能研究院 · 首席技术官',
        avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20tech%20leader%20man%20portrait%20headshot%20smart%20clean%20white%20background&image_size=square',
      },
      {
        type: 'profile',
        name: '王强',
        title: '首席技术官',
        company: '人工智能研究院',
        bio: '15年人工智能领域经验，深度学习专家。曾在多家知名科技公司担任技术负责人，主导过多个AI核心项目的研发。在自然语言处理、计算机视觉等领域有深厚造诣。',
        contact: {
          phone: '13700137000',
          email: 'wangqiang@example.com',
          wechat: 'wangqiang_ai',
        },
      },
      {
        type: 'resources',
        provides: ['AI技术开发', '深度学习', '算法优化', '技术咨询'],
        needs: ['高端人才', '研发资金', '产业落地'],
        purpose: 'employee',
      },
      {
        type: 'company',
        name: '人工智能研究院',
        industry: '人工智能',
        size: '101-500人',
        desc: '人工智能研究院是一家专注于AI技术研发和产业应用的科研机构，拥有多项核心技术专利，致力于推动人工智能技术的创新与落地。',
        development: '2018年：研究院成立\n2020年：获得国家重点研发计划支持\n2022年：研发团队突破200人\n2024年：AI产品矩阵覆盖多个行业',
        images: [
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=AI%20research%20laboratory%20modern%20high%20tech%20facility&image_size=landscape_4_3',
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=data%20center%20server%20room%20artificial%20intelligence&image_size=landscape_4_3',
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=AI%20team%20working%20on%20computers%20innovation%20lab&image_size=landscape_4_3',
        ],
      },
      {
        type: 'case',
        index: 1,
        name: '智能客服系统',
        date: '2022年',
        desc: '主导研发新一代智能客服系统，采用先进的NLP技术，实现95%以上的问题自动解答率，帮助企业降低60%的客服成本。',
        images: [
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=AI%20chatbot%20customer%20service%20digital%20interface&image_size=landscape_4_3',
        ],
      },
      {
        type: 'case',
        index: 2,
        name: '计算机视觉平台',
        date: '2023年',
        desc: '打造一站式计算机视觉平台，支持图像识别、目标检测、图像分割等功能，已服务超过100家企业客户。',
        images: [
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=computer%20vision%20image%20recognition%20AI%20technology&image_size=landscape_4_3',
        ],
      },
      {
        type: 'case',
        index: 3,
        name: '大语言模型',
        date: '2024年',
        desc: '带领团队成功研发千亿参数大语言模型，在多项NLP基准测试中取得优异成绩，为行业提供智能化解决方案。',
        images: [
          'https://neeko-copilot.bytedance.net/api/text2image?prompt=large%20language%20model%20AI%20brain%20neural%20network&image_size=landscape_4_3',
        ],
      },
      {
        type: 'contact',
        name: '王强',
        phone: '13700137000',
        email: 'wangqiang@example.com',
        wechat: 'wangqiang_ai',
        company: '人工智能研究院',
      },
    ],
  },
]

const TEST_RECOMMEND_LIST = [
  {
    id: 'm001',
    name: '刘芳',
    avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20woman%20data%20analyst%20portrait%20headshot&image_size=square',
    company: '大数据科技公司',
    title: '数据分析师',
    matchScore: 92,
    tagMatchScore: 88,
    semanticScore: 95,
    commonTags: ['数据分析', 'Python', '机器学习'],
  },
  {
    id: 'm002',
    name: '陈明',
    avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20man%20incubator%20director%20portrait%20headshot&image_size=square',
    company: '创业孵化平台',
    title: '孵化总监',
    matchScore: 87,
    tagMatchScore: 90,
    semanticScore: 85,
    commonTags: ['创业指导', '资源对接', '投资'],
  },
  {
    id: 'm003',
    name: '赵丽',
    avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20tech%20woman%20CTO%20portrait%20headshot&image_size=square',
    company: '互联网公司',
    title: '技术总监',
    matchScore: 85,
    tagMatchScore: 82,
    semanticScore: 88,
    commonTags: ['技术开发', '团队管理', '架构设计'],
  },
  {
    id: 'm004',
    name: '王强',
    avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20man%20marketing%20director%20portrait%20headshot&image_size=square',
    company: '数字营销集团',
    title: '市场总监',
    matchScore: 90,
    tagMatchScore: 85,
    semanticScore: 93,
    commonTags: ['市场营销', '品牌策划', '数字营销'],
  },
  {
    id: 'm005',
    name: '林悦',
    avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20woman%20finance%20director%20portrait%20headshot&image_size=square',
    company: '金融科技公司',
    title: '财务总监',
    matchScore: 88,
    tagMatchScore: 86,
    semanticScore: 90,
    commonTags: ['财务管理', '投融资', '风险控制'],
  },
  {
    id: 'm006',
    name: '张明',
    avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20tech%20man%20product%20manager%20portrait%20headshot&image_size=square',
    company: '互联网科技公司',
    title: '产品总监',
    matchScore: 86,
    tagMatchScore: 84,
    semanticScore: 89,
    commonTags: ['产品设计', '用户增长', '敏捷开发'],
  },
  {
    id: 'm007',
    name: '李娜',
    avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20woman%20HR%20director%20portrait%20headshot&image_size=square',
    company: '人力资源咨询',
    title: 'HR总监',
    matchScore: 83,
    tagMatchScore: 80,
    semanticScore: 86,
    commonTags: ['人力资源', '组织发展', '人才招聘'],
  },
  {
    id: 'm008',
    name: '周伟',
    avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20man%20sales%20director%20portrait%20headshot&image_size=square',
    company: '国际贸易集团',
    title: '销售总监',
    matchScore: 89,
    tagMatchScore: 87,
    semanticScore: 91,
    commonTags: ['销售管理', '商务谈判', '渠道拓展'],
  },
  {
    id: 'm009',
    name: '黄婷',
    avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20tech%20woman%20AI%20researcher%20portrait%20headshot&image_size=square',
    company: 'AI实验室',
    title: 'AI研究员',
    matchScore: 95,
    tagMatchScore: 92,
    semanticScore: 97,
    commonTags: ['人工智能', '深度学习', 'NLP'],
  },
  {
    id: 'm010',
    name: '吴浩',
    avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20man%20operations%20director%20portrait%20headshot&image_size=square',
    company: '物流科技公司',
    title: '运营总监',
    matchScore: 84,
    tagMatchScore: 81,
    semanticScore: 87,
    commonTags: ['运营管理', '供应链', '流程优化'],
  },
  {
    id: 'm011',
    name: '杨雪',
    avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20woman%20legal%20counsel%20portrait%20headshot&image_size=square',
    company: '律师事务所',
    title: '法务总监',
    matchScore: 81,
    tagMatchScore: 79,
    semanticScore: 84,
    commonTags: ['法律咨询', '合规管理', '知识产权'],
  },
  {
    id: 'm012',
    name: '孙鹏',
    avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=professional%20asian%20business%20man%20strategic%20planner%20portrait%20headshot&image_size=square',
    company: '战略咨询公司',
    title: '战略顾问',
    matchScore: 91,
    tagMatchScore: 89,
    semanticScore: 93,
    commonTags: ['战略规划', '商业分析', '企业转型'],
  },
]

const TEST_TAGS = [
  '产品经理', '用户增长', '数据分析', '战略规划',
  '投资', '创业', '人工智能', '技术开发',
  '市场营销', '品牌策划', '财务管理', '人力资源',
]

const TEST_VISITOR_STATS = {
  total: 520,
  total_visits: 520,
  today: 23,
  week: 156,
  month: 520,
  trend: [12, 18, 15, 22, 19, 25, 23],
}

const TEST_TRUST_NETWORK = {
  trusting: [
    { id: 't001', name: '张三', avatar: '', relation: '同事', trustScore: 95 },
    { id: 't002', name: '李四', avatar: '', relation: '校友', trustScore: 88 },
    { id: 't003', name: '王五', avatar: '', relation: '合作伙伴', trustScore: 92 },
    { id: 't004', name: '赵六', avatar: '', relation: '下属', trustScore: 90 },
    { id: 't005', name: '孙七', avatar: '', relation: '朋友', trustScore: 85 },
    { id: 't006', name: '周八', avatar: '', relation: '客户', trustScore: 82 },
    { id: 't007', name: '吴九', avatar: '', relation: '投资人', trustScore: 89 },
    { id: 't008', name: '郑十', avatar: '', relation: '导师', trustScore: 93 },
    { id: 't009', name: '冯十一', avatar: '', relation: '同学', trustScore: 87 },
    { id: 't010', name: '陈十二', avatar: '', relation: '合伙人', trustScore: 96 },
    { id: 't011', name: '褚十三', avatar: '', relation: '同事', trustScore: 91 },
    { id: 't012', name: '卫十四', avatar: '', relation: '校友', trustScore: 86 },
    { id: 't013', name: '蒋十五', avatar: '', relation: '合作伙伴', trustScore: 93 },
    { id: 't014', name: '沈十六', avatar: '', relation: '下属', trustScore: 88 },
    { id: 't015', name: '韩十七', avatar: '', relation: '朋友', trustScore: 84 },
    { id: 't016', name: '杨十八', avatar: '', relation: '客户', trustScore: 90 },
    { id: 't017', name: '朱十九', avatar: '', relation: '投资人', trustScore: 92 },
    { id: 't018', name: '秦二十', avatar: '', relation: '导师', trustScore: 89 },
    { id: 't019', name: '许二十一', avatar: '', relation: '同学', trustScore: 87 },
    { id: 't020', name: '何二十二', avatar: '', relation: '合伙人', trustScore: 94 },
    { id: 't021', name: '吕二十三', avatar: '', relation: '同事', trustScore: 85 },
    { id: 't022', name: '施二十四', avatar: '', relation: '校友', trustScore: 91 },
    { id: 't023', name: '张二十五', avatar: '', relation: '合作伙伴', trustScore: 88 },
    { id: 't024', name: '孔二十六', avatar: '', relation: '下属', trustScore: 93 },
    { id: 't025', name: '曹二十七', avatar: '', relation: '朋友', trustScore: 86 },
  ],
  trusted_by: [
    { id: 't026', name: '严二十八', avatar: '', relation: '客户', trustScore: 89 },
    { id: 't027', name: '华二十九', avatar: '', relation: '投资人', trustScore: 95 },
    { id: 't028', name: '金三十', avatar: '', relation: '导师', trustScore: 90 },
    { id: 't029', name: '魏三十一', avatar: '', relation: '同学', trustScore: 87 },
    { id: 't030', name: '陶三十二', avatar: '', relation: '合伙人', trustScore: 92 },
    { id: 't031', name: '姜三十三', avatar: '', relation: '同事', trustScore: 85 },
    { id: 't032', name: '谢三十四', avatar: '', relation: '校友', trustScore: 91 },
    { id: 't033', name: '宋三十五', avatar: '', relation: '合作伙伴', trustScore: 88 },
    { id: 't034', name: '唐三十六', avatar: '', relation: '下属', trustScore: 93 },
    { id: 't035', name: '邓三十七', avatar: '', relation: '朋友', trustScore: 86 },
    { id: 't036', name: '冯三十八', avatar: '', relation: '客户', trustScore: 89 },
    { id: 't037', name: '韩三十九', avatar: '', relation: '投资人', trustScore: 94 },
    { id: 't038', name: '曹四十', avatar: '', relation: '导师', trustScore: 90 },
    { id: 't039', name: '钱四十一', avatar: '', relation: '同学', trustScore: 87 },
    { id: 't040', name: '孙四十二', avatar: '', relation: '合伙人', trustScore: 92 },
    { id: 't041', name: '李四十三', avatar: '', relation: '同事', trustScore: 85 },
    { id: 't042', name: '周四十四', avatar: '', relation: '校友', trustScore: 91 },
    { id: 't043', name: '吴四十五', avatar: '', relation: '合作伙伴', trustScore: 88 },
    { id: 't044', name: '郑四十六', avatar: '', relation: '下属', trustScore: 93 },
    { id: 't045', name: '王四十七', avatar: '', relation: '朋友', trustScore: 86 },
    { id: 't046', name: '冯四十八', avatar: '', relation: '客户', trustScore: 89 },
    { id: 't047', name: '陈四十九', avatar: '', relation: '投资人', trustScore: 94 },
    { id: 't048', name: '褚五十', avatar: '', relation: '导师', trustScore: 90 },
    { id: 't049', name: '卫五十一', avatar: '', relation: '同学', trustScore: 87 },
    { id: 't050', name: '蒋五十二', avatar: '', relation: '合伙人', trustScore: 92 },
  ],
}

// ===== 扩展好友关系图谱（用于BFS测试） =====
const TEST_FRIENDS_MAP = {
  // 当前用户的好友
  self: [
    { id: 't001', name: '张三' },
    { id: 't002', name: '李四' },
    { id: 't003', name: '王五' },
  ],
  // 张三的好友
  t001: [
    { id: 't002', name: '李四' },
    { id: 't004', name: '赵六' },
    { id: 't008', name: '周八' },
  ],
  // 李四的好友
  t002: [
    { id: 't001', name: '张三' },
    { id: 't005', name: '孙七' },
    { id: 't009', name: '吴九' },
  ],
  // 王五的好友
  t003: [
    { id: 't006', name: '郑十' },
    { id: 't007', name: '冯十一' },
  ],
  // 赵六的好友
  t004: [
    { id: 't001', name: '张三' },
    { id: 't010', name: '陈十二' },
  ],
  // 孙七的好友
  t005: [
    { id: 't002', name: '李四' },
    { id: 't011', name: '褚十三' },
  ],
  // 郑十的好友
  t006: [
    { id: 't003', name: '王五' },
    { id: 't012', name: '魏十四' },
    { id: 't013', name: '蒋十五' },
  ],
  // 冯十一的好友
  t007: [{ id: 't003', name: '王五' }],
  // 周八的好友
  t008: [{ id: 't001', name: '张三' }],
  // 吴九的好友
  t009: [{ id: 't002', name: '李四' }],
  // 陈十二的好友
  t010: [{ id: 't004', name: '赵六' }],
  // 褚十三的好友
  t011: [{ id: 't005', name: '孙七' }],
  // 魏十四的好友
  t012: [{ id: 't006', name: '郑十' }],
  // 蒋十五的好友
  t013: [{ id: 't006', name: '郑十' }],
}

// ===== 平台测试数据 =====
const TEST_PLATFORMS = [
  {
    id: 'p001',
    name: '长三角产业资源平台',
    platform_no: 'PT20240001',
    description: '汇聚长三角地区优质产业资源，促进区域经济协同发展',
    creator_id: 'u001',
    creator_name: '张伟',
    annual_fee: 999,
    industries: ['科技', '制造', '金融'],
    province: '上海市',
    city: '上海市',
    created_at: Date.now() - 86400000 * 30,
    member_count: 12,
    resource_count: 45,
    opportunity_count: 3,
    logo: '',
  },
  {
    id: 'p002',
    name: '粤港澳大湾区创新联盟',
    platform_no: 'PT20240002',
    description: '链接大湾区科技创新资源，打造国际创新生态圈',
    creator_id: 'u002',
    creator_name: '李娜',
    annual_fee: 1999,
    industries: ['科技', '金融'],
    province: '广东省',
    city: '深圳市',
    created_at: Date.now() - 86400000 * 15,
    member_count: 8,
    resource_count: 23,
    opportunity_count: 1,
    logo: '',
  },
  {
    id: 'p003',
    name: '京津冀AI技术协作平台',
    platform_no: 'PT20240003',
    description: 'AI技术开发·模型训练·数据标注，构建京津冀地区人工智能产业生态',
    creator_id: 'u003',
    creator_name: '王强',
    annual_fee: 0,
    industries: ['人工智能', '科技', '教育'],
    province: '北京市',
    city: '北京市',
    created_at: Date.now() - 86400000 * 45,
    member_count: 20,
    resource_count: 128,
    opportunity_count: 7,
    logo: '',
  },
  {
    id: 'p004',
    name: '供应链资源对接中心',
    platform_no: 'PT20240004',
    description: '供应商对接·物流配送·仓储服务，一站式供应链资源整合平台',
    creator_id: 'u002',
    creator_name: '李娜',
    annual_fee: 1499,
    industries: ['物流', '制造', '电商'],
    province: '浙江省',
    city: '杭州市',
    created_at: Date.now() - 86400000 * 60,
    member_count: 35,
    resource_count: 210,
    opportunity_count: 12,
    logo: '',
  },
  {
    id: 'p005',
    name: '投融资对接平台',
    platform_no: 'PT20240005',
    description: '天使投资·VC融资·并购重组，链接优质资本与创新项目',
    creator_id: 'u004',
    creator_name: '赵敏',
    annual_fee: 2999,
    industries: ['金融', '投资', '科技'],
    province: '上海市',
    city: '上海市',
    created_at: Date.now() - 86400000 * 20,
    member_count: 15,
    resource_count: 67,
    opportunity_count: 5,
    logo: '',
  },
  {
    id: 'p006',
    name: '市场营销资源共享平台',
    platform_no: 'PT20240006',
    description: '品牌推广·渠道拓展·流量获客，助力企业高效营销',
    creator_id: 'u005',
    creator_name: '周瑜',
    annual_fee: 799,
    industries: ['营销', '传媒', '电商'],
    province: '广东省',
    city: '广州市',
    created_at: Date.now() - 86400000 * 10,
    member_count: 42,
    resource_count: 156,
    opportunity_count: 8,
    logo: '',
  },
  {
    id: 'p007',
    name: '西部数字经济发展联盟',
    platform_no: 'PT20240007',
    description: '推动西部地区数字经济发展，促进产业数字化转型',
    creator_id: 'u006',
    creator_name: '吴用',
    annual_fee: 599,
    industries: ['科技', '教育', '农业'],
    province: '四川省',
    city: '成都市',
    created_at: Date.now() - 86400000 * 50,
    member_count: 18,
    resource_count: 34,
    opportunity_count: 2,
    logo: '',
  },
  {
    id: 'p008',
    name: '生物医药产业创新中心',
    platform_no: 'PT20240008',
    description: '汇聚生物医药领域优质资源，推动新药研发与产业化',
    creator_id: 'u007',
    creator_name: '郑和',
    annual_fee: 2499,
    industries: ['医疗', '生物', '科技'],
    province: '江苏省',
    city: '苏州市',
    created_at: Date.now() - 86400000 * 25,
    member_count: 25,
    resource_count: 89,
    opportunity_count: 4,
    logo: '',
  },
]

const TEST_PLATFORM_MEMBERS = {
  p001: [
    { id: 'u001', name: '张伟', role: 'secretary_general', joined_at: Date.now() - 86400000 * 30 },
    { id: 'u002', name: '李娜', role: 'secretariat', joined_at: Date.now() - 86400000 * 25 },
    { id: 'u003', name: '王强', role: 'secretariat', joined_at: Date.now() - 86400000 * 20 },
    { id: 'u004', name: '赵敏', role: 'member', joined_at: Date.now() - 86400000 * 18 },
    { id: 'u005', name: '周瑜', role: 'member', joined_at: Date.now() - 86400000 * 15 },
    { id: 'u006', name: '吴用', role: 'member', joined_at: Date.now() - 86400000 * 12 },
    { id: 'u007', name: '郑和', role: 'member', joined_at: Date.now() - 86400000 * 10 },
    { id: 'u008', name: '王昭君', role: 'member', joined_at: Date.now() - 86400000 * 8 },
    { id: 'u009', name: '孙膑', role: 'member', joined_at: Date.now() - 86400000 * 6 },
    { id: 'u010', name: '苏秦', role: 'member', joined_at: Date.now() - 86400000 * 5 },
    { id: 'u011', name: '张仪', role: 'member', joined_at: Date.now() - 86400000 * 3 },
    { id: 'u012', name: '范蠡', role: 'member', joined_at: Date.now() - 86400000 * 1 },
  ],
  p002: [
    { id: 'u002', name: '李娜', role: 'secretary_general', joined_at: Date.now() - 86400000 * 15 },
    { id: 'u003', name: '王强', role: 'secretariat', joined_at: Date.now() - 86400000 * 12 },
    { id: 'u001', name: '张伟', role: 'member', joined_at: Date.now() - 86400000 * 10 },
  ],
}

const TEST_PLATFORM_APPLICATIONS = {
  p001: [
    { id: 'a001', user_id: 'u013', user_name: '李白', status: 'pending', applied_at: Date.now() - 3600000 * 2 },
    { id: 'a002', user_id: 'u014', user_name: '杜甫', status: 'pending', applied_at: Date.now() - 3600000 * 5 },
  ],
  p002: [
    { id: 'a003', user_id: 'u015', user_name: '白居易', status: 'pending', applied_at: Date.now() - 3600000 },
  ],
}

const TEST_PLATFORM_OPPORTUNITIES = {
  p001: [
    { id: 'op001', title: '智能制造技术对接', type: '技术合作', industry: '制造', location: '上海市', desc: '寻求智能制造技术合作伙伴，共同开发工业4.0解决方案', publisher: '张伟', created_at: Date.now() - 86400000 * 3 },
    { id: 'op002', title: 'AI算法人才招聘', type: '招聘', industry: '科技', location: '杭州市', desc: '诚聘AI算法工程师，要求5年以上深度学习经验', publisher: '王强', created_at: Date.now() - 86400000 * 2 },
    { id: 'op003', title: '供应链金融服务', type: '金融', industry: '金融', location: '上海市', desc: '为中小企业提供供应链金融解决方案', publisher: '李娜', created_at: Date.now() - 86400000 },
  ],
  p003: [
    { id: 'op004', title: 'AI模型训练数据', type: '数据服务', industry: '人工智能', location: '北京市', desc: '提供高质量AI训练数据集，覆盖多个行业', publisher: '王强', created_at: Date.now() - 86400000 * 5 },
    { id: 'op005', title: 'AI应用落地咨询', type: '咨询服务', industry: '科技', location: '北京市', desc: '帮助企业实现AI技术落地应用', publisher: '张伟', created_at: Date.now() - 86400000 * 4 },
  ],
}

const TEST_PLATFORM_RESOURCE_UNITS = {
  p001: [
    { id: 'ru001', name: '科技创新有限公司', industry: '科技', location: '上海市', contact: '张伟', phone: '13800138000' },
    { id: 'ru002', name: '金融投资集团', industry: '金融', location: '上海市', contact: '李娜', phone: '13900139000' },
    { id: 'ru003', name: '人工智能研究院', industry: '人工智能', location: '北京市', contact: '王强', phone: '13700137000' },
  ],
  p003: [
    { id: 'ru004', name: 'AI技术开发公司', industry: '人工智能', location: '北京市', contact: '王强', phone: '13700137000' },
    { id: 'ru005', name: '数据服务平台', industry: '科技', location: '北京市', contact: '赵敏', phone: '13600136000' },
  ],
}

const TEST_AI_GENERATE_TEMPLATES = {
  intro: {
    professional: {
      title: '专业正式',
      desc: '适合商务场合',
      generate: (input) => `您好，我是【${input || '用户'}】。拥有丰富的行业经验和专业能力，致力于为客户提供优质的解决方案。期待与您的合作！`,
    },
    friendly: {
      title: '亲切友好',
      desc: '适合社交场合',
      generate: (input) => `大家好！我是${input || '用户'}，很高兴认识你！我热爱我的工作，喜欢结识新朋友。让我们一起交流学习，共同进步！`,
    },
    creative: {
      title: '创意活泼',
      desc: '适合设计行业',
      generate: (input) => `Hi~ 我是${input || '用户'}，一个充满创意和热情的设计师！我相信好的设计能够改变世界，期待与你一起创造精彩！`,
    },
  },
  tagline: {
    professional: {
      title: '专业口号',
      desc: '简洁有力',
      generate: (input) => `${input || '专业'}创造价值，创新引领未来`,
    },
    catchy: {
      title: '吸睛口号',
      desc: '容易记住',
      generate: (input) => `选择${input || '我们'}，成就非凡！`,
    },
  },
}

const TestData = {
  TEST_USERS,
  TEST_BROCHURES,
  TEST_RECOMMEND_LIST,
  TEST_TAGS,
  TEST_VISITOR_STATS,
  TEST_TRUST_NETWORK,
  TEST_AI_GENERATE_TEMPLATES,

  getTestUser(level = 'free') {
    return TEST_USERS[level] || TEST_USERS.free
  },

  getTestUserByToken() {
    const { token } = store.getState()
    if (!token) {
      console.warn('[TestData] token为空，返回free用户')
      return TEST_USERS.free
    }
    for (const [level, user] of Object.entries(TEST_USERS)) {
      if (user.token === token) {
        return user
      }
    }
    console.warn('[TestData] token不匹配，返回free用户')
    return TEST_USERS.free
  },

  getProfile(memberLevel) {
    const user = this.getTestUser(memberLevel)
    return {
      ...user.userInfo,
      memberLevel: user.memberLevel,
      tags: TEST_TAGS.slice(0, 8),
      brochure_count: TEST_BROCHURES.filter(b => b.user_id === user.user_id).length,
      match_count: TEST_RECOMMEND_LIST.length,
    }
  },

  loginAs(level = 'free') {
    const user = this.getTestUser(level)
    console.log('[TestData] 获取模拟用户:', user.userInfo.name, '会员等级:', user.memberLevel)
    return user
  },
}

module.exports = {
  TEST_USERS,
  TEST_BROCHURES,
  TEST_RECOMMEND_LIST,
  TEST_TAGS,
  TEST_VISITOR_STATS,
  TEST_TRUST_NETWORK,
  TEST_FRIENDS_MAP,
  TEST_PLATFORMS,
  TEST_PLATFORM_MEMBERS,
  TEST_PLATFORM_APPLICATIONS,
  TEST_PLATFORM_OPPORTUNITIES,
  TEST_PLATFORM_RESOURCE_UNITS,
  TEST_AI_GENERATE_TEMPLATES,
  TestData,
}