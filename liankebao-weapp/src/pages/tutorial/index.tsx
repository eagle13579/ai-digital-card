import { FC, useState, useCallback } from 'react'
import { View, Text, Image, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import './index.scss'

/* ========================================================================== */
/*  类型                                                                       */
/* ========================================================================== */

interface TutorialItem {
  id: string
  title: string
  summary: string
  cover?: string
  category: string
  content: string[]
  related?: { title: string; id: string }[]
}

/* ========================================================================== */
/*  Demo 数据 — 教程列表                                                       */
/* ========================================================================== */

const DEMO_TUTORIALS: TutorialItem[] = [
  {
    id: 't_1',
    title: '如何使用AI数字名片',
    summary: '快速上手AI数字名片，从创建到分享全流程指南。',
    cover: PLACEHOLDER.cover280x180,
    category: '入门指南',
    content: [
      '第一步：打开链客宝小程序，点击首页「AI 帮我创建名片」按钮。',
      '第二步：填写个人基本信息，包括姓名、职位、公司、联系方式等。',
      '第三步：选择喜欢的名片模板样式，AI将自动生成个性化名片。',
      '第四步：预览名片效果，确认无误后点击发布。',
      '第五步：分享名片到微信好友、朋友圈或微信群，建立您的数字社交形象。',
      '',
      '小贴士：您可以创建多张名片用于不同场景，如商务名片、社交名片等。',
    ],
    related: [
      { title: '如何推广您的名片', id: 't_2' },
      { title: 'AI智能匹配功能详解', id: 't_3' },
    ],
  },
  {
    id: 't_2',
    title: '如何推广您的AI名片',
    summary: '学会多渠道推广技巧，让更多人看到您的名片。',
    cover: PLACEHOLDER.cover280x180,
    category: '推广技巧',
    content: [
      '一、社交分享：将名片直接分享到微信好友和朋友圈，是最直接的推广方式。',
      '二、群聊推广：将名片发送到行业交流群、商会群等目标群体聚集的社群。',
      '三、线下场景：将名片二维码打印在纸质名片或海报上，扫码即查看。',
      '四、个人资料：将名片链接放在微信个人签名、公众号简介等处。',
      '五、平台推广：在链客宝供需大厅和产品池中关联名片，增加曝光。',
      '',
      '小贴士：定期更新名片信息，保持活跃度可以提升推荐权重。',
    ],
    related: [
      { title: '如何使用AI数字名片', id: 't_1' },
      { title: '如何提高匹配成功率', id: 't_4' },
    ],
  },
  {
    id: 't_3',
    title: 'AI智能匹配功能详解',
    summary: '了解链客宝AI如何为您精准推荐商业伙伴。',
    cover: PLACEHOLDER.cover280x180,
    category: '功能说明',
    content: [
      '什么是AI智能匹配？',
      '链客宝AI匹配引擎基于深度学习的商业匹配算法，分析您的名片信息、行业标签、供需意向等多维数据，为您推荐最合适的潜在合作伙伴。',
      '',
      '匹配机制：',
      '• 行业匹配：根据您的行业标签匹配同领域或上下游企业。',
      '• 需求匹配：分析您的供需信息，找到有合作意向的对象。',
      '• 关系匹配：通过社交网络分析，发现间接联系。',
      '• 行为匹配：结合浏览和交互行为，推荐高意向用户。',
      '',
      '如何提高匹配成功率？',
      '完善个人信息、添加详细标签、发布真实供需需求，系统将更精准地为您推荐。',
    ],
    related: [
      { title: '如何提高匹配成功率', id: 't_4' },
      { title: '如何使用AI数字名片', id: 't_1' },
    ],
  },
  {
    id: 't_4',
    title: '如何提高匹配成功率',
    summary: '优化您的名片和需求，获取更多高质量合作机会。',
    cover: PLACEHOLDER.cover280x180,
    category: '进阶技巧',
    content: [
      '1. 完善个人信息：',
      '上传真实头像，填写完整的公司信息和职位，让推荐更精准。',
      '',
      '2. 设置精准标签：',
      '在名片中添加行业、技能、需求标签，帮助AI理解您的业务方向。',
      '',
      '3. 发布有效供需：',
      '在供需大厅发布详细的合作需求或供给信息，附带具体描述。',
      '',
      '4. 保持活跃互动：',
      '定期查看推荐列表，主动与推荐对象沟通，系统会记录互动行为。',
      '',
      '5. 多场景使用：',
      '为不同的商务场景创建专属名片，增加匹配覆盖范围。',
    ],
    related: [
      { title: 'AI智能匹配功能详解', id: 't_3' },
      { title: '如何推广您的AI名片', id: 't_2' },
    ],
  },
  {
    id: 't_5',
    title: '供需大厅使用指南',
    summary: '在供需大厅发布和寻找合作资源，高效对接。',
    cover: PLACEHOLDER.cover280x180,
    category: '平台指南',
    content: [
      '什么是供需大厅？',
      '供需大厅是链客宝用户发布和寻找商业合作的信息平台，涵盖技术合作、资源对接、人才招聘等多种场景。',
      '',
      '发布供需信息：',
      '1. 选择供给或需求类型。',
      '2. 填写标题、描述和联系方式。',
      '3. 添加相关标签，方便搜索匹配。',
      '4. 发布后可在"我的发布"中管理。',
      '',
      '寻找合作机会：',
      '使用搜索功能筛选关键词和分类，快速找到感兴趣的供需信息。',
    ],
    related: [
      { title: '如何提高匹配成功率', id: 't_4' },
      { title: '如何推广您的AI名片', id: 't_2' },
    ],
  },
]

const CATEGORIES = [
  { key: 'all', label: '全部' },
  { key: '入门指南', label: '入门指南' },
  { key: '推广技巧', label: '推广技巧' },
  { key: '功能说明', label: '功能说明' },
  { key: '进阶技巧', label: '进阶技巧' },
  { key: '平台指南', label: '平台指南' },
]

/* ========================================================================== */
/*  主组件                                                                     */
/* ========================================================================== */

const Tutorial: FC = () => {
  /* ---- 状态 ---- */
  const [activeCategory, setActiveCategory] = useState('all')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  /* ---- 筛选 ---- */
  const filtered =
    activeCategory === 'all'
      ? DEMO_TUTORIALS
      : DEMO_TUTORIALS.filter((t) => t.category === activeCategory)

  /* ---- 切换分类 ---- */
  const switchCategory = useCallback((key: string) => {
    setActiveCategory(key)
    setExpandedId(null)
  }, [])

  /* ---- 展开/收起 ---- */
  const toggleExpand = useCallback((id: string) => {
    setExpandedId((prev) => (prev === id ? null : id))
  }, [])

  /* ---- 跳转相关教程 ---- */
  const goToTutorial = useCallback((id: string) => {
    setExpandedId(id)
    // 滚动到顶部（通过展开对应内容）
    Taro.pageScrollTo({ scrollTop: 0, duration: 300 })
  }, [])

  /* ================================================================ */
  /*  渲染                                                                  */
  /* ================================================================ */

  return (
    <View className='tutorial'>
      {/* ================ 页面标题 ================ */}
      <View className='tutorial__header'>
        <Text className='tutorial__header-title'>📚 使用教程</Text>
        <Text className='tutorial__header-desc'>
          手把手教您使用链客宝各项功能
        </Text>
      </View>

      {/* ================ 分类筛选 ================ */}
      <View className='tutorial__categories'>
        <ScrollView
          className='tutorial__categories-scroll'
          scrollX
          enhanced
          showScrollbar={false}
        >
          {CATEGORIES.map((cat) => (
            <View
              key={cat.key}
              className={`tutorial__category-tab ${activeCategory === cat.key ? 'tutorial__category-tab--active' : ''}`}
              onClick={() => switchCategory(cat.key)}
            >
              <Text className='tutorial__category-label'>{cat.label}</Text>
            </View>
          ))}
        </ScrollView>
      </View>

      {/* ================ 教程列表 ================ */}
      <ScrollView
        className='tutorial__scroll'
        scrollY
        enhanced
        showScrollbar={false}
        lowerThreshold={50}
      >
        {filtered.length > 0 ? (
          <View className='tutorial__list'>
            {filtered.map((tutorial) => {
              const isExpanded = expandedId === tutorial.id

              return (
                <View
                  key={tutorial.id}
                  className={`tutorial__card ${isExpanded ? 'tutorial__card--expanded' : ''}`}
                >
                  {/* 封面 */}
                  {tutorial.cover && (
                    <Image
                      className='tutorial__card-cover'
                      src={tutorial.cover}
                      mode='aspectFill'
                      onClick={() => toggleExpand(tutorial.id)}
                    />
                  )}

                  {/* 摘要信息 */}
                  <View
                    className='tutorial__card-summary'
                    onClick={() => toggleExpand(tutorial.id)}
                  >
                    <View className='tutorial__card-top'>
                      <Text className='tutorial__card-category'>
                        {tutorial.category}
                      </Text>
                    </View>
                    <Text className='tutorial__card-title'>
                      {tutorial.title}
                    </Text>
                    <Text
                      className='tutorial__card-summary-text'
                      numberOfLines={2}
                    >
                      {tutorial.summary}
                    </Text>
                    <View className='tutorial__card-expand-hint'>
                      <Text className='tutorial__card-expand-icon'>
                        {isExpanded ? '收起 ▲' : '展开详情 ▼'}
                      </Text>
                    </View>
                  </View>

                  {/* 展开的详细内容 */}
                  {isExpanded && (
                    <View className='tutorial__card-detail'>
                      <View className='tutorial__card-divider' />
                      {tutorial.content.map((line, idx) => {
                        // 空行渲染为间距
                        if (!line.trim()) {
                          return (
                            <View key={idx} className='tutorial__content-spacer' />
                          )
                        }
                        // 判断是否为标题行（以标点或特殊字符开头）
                        const isTitle =
                          line.startsWith('一、') ||
                          line.startsWith('二、') ||
                          line.startsWith('三、') ||
                          line.startsWith('四、') ||
                          line.startsWith('五、') ||
                          line.startsWith('第一步') ||
                          line.startsWith('第二步') ||
                          line.startsWith('第三步') ||
                          line.startsWith('第四步') ||
                          line.startsWith('第五步') ||
                          line.startsWith('什么') ||
                          line.match(/^[•·]/)

                        // 判断是否为小标题
                        const isSubTitle =
                          line.startsWith('•') ||
                          line.match(/^\d+\.\s/)

                        return (
                          <Text
                            key={idx}
                            className={`tutorial__content-line ${
                              isTitle ? 'tutorial__content-line--title' : ''
                            } ${isSubTitle ? 'tutorial__content-line--subtitle' : ''}`}
                          >
                            {line}
                          </Text>
                        )
                      })}

                      {/* 相关教程 */}
                      {tutorial.related && tutorial.related.length > 0 && (
                        <View className='tutorial__related'>
                          <Text className='tutorial__related-title'>
                            相关教程
                          </Text>
                          <View className='tutorial__related-list'>
                            {tutorial.related.map((rel) => (
                              <View
                                key={rel.id}
                                className='tutorial__related-item'
                                onClick={() => goToTutorial(rel.id)}
                              >
                                <Text className='tutorial__related-icon'>
                                  📖
                                </Text>
                                <Text className='tutorial__related-text'>
                                  {rel.title}
                                </Text>
                                <Text className='tutorial__related-arrow'>
                                  ›
                                </Text>
                              </View>
                            ))}
                          </View>
                        </View>
                      )}
                    </View>
                  )}
                </View>
              )
            })}
          </View>
        ) : (
          <View className='tutorial__empty'>
            <Text className='tutorial__empty-icon'>📚</Text>
            <Text className='tutorial__empty-title'>暂无教程</Text>
            <Text className='tutorial__empty-desc'>
              换个分类看看
            </Text>
          </View>
        )}

        <View className='tutorial__bottom-spacer' />
      </ScrollView>
    </View>
  )
}

export default Tutorial
