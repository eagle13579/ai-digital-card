/**
 * 名片详情 Screen — 查看完整名片信息 + 操作 + 信任网络 + 最近互动
 * 导航: CardScreen -> CardDetailScreen (params: { cardId })
 *
 * 功能:
 *  - 展示完整名片信息 (头像/姓名/公司/职位/电话/邮箱/标签)
 *  - 操作按钮 (分享/保存/编辑/数据)
 *  - 信任网络 (信任分/联系数/亲密度)
 *  - 最近互动列表
 *  - API: GET /mobile/card/:id
 */

import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  RefreshControl,
  ActivityIndicator,
  Platform,
  Share,
  Alert,
} from 'react-native';
import { useTheme } from '../theme/theme-context';
import { api } from '../api/client';

// ── Types ───────────────────────────────────────────────────────────────────

interface CardData {
  id: string;
  name: string;
  title: string;
  company: string;
  email: string;
  phone: string;
  website: string;
  tags: string[];
  avatarUrl?: string;
  qrValue?: string;

  // Trust network
  trustScore: number;
  contactCount: number;
  intimacy: string;

  // Stat cards
  todayVisits: number;
  monthUnlocks: number;
  totalShares: number;

  // Recent interactions
  recentInteractions: Array<{
    who: string;
    action: string;
    time: string;
    avatar?: string;
  }>;
}

const DEFAULT_CARD: CardData = {
  id: '1',
  name: '海容 · 向',
  title: 'AI 数字名片创始人',
  company: '链客宝科技有限公司',
  email: 'hirongxiang@ncard.ai',
  phone: '+86 138-0000-8888',
  website: 'https://ai-digital-card.com',
  tags: ['AI', '数字名片', 'SaaS', 'Web3', '信任网络'],
  trustScore: 9.2,
  contactCount: 248,
  intimacy: '高',
  todayVisits: 128,
  monthUnlocks: 47,
  totalShares: 72,
  recentInteractions: [
    { who: '张总', action: '查看了你的名片', time: '2 分钟前', avatar: '👤' },
    { who: '李博士', action: '与你的 AI 分身对话', time: '12 分钟前', avatar: '👨‍💼' },
    { who: '王总', action: '解锁了 AI 产品手册', time: '1 小时前', avatar: '👨‍🚀' },
    { who: 'Lina', action: '转发了你的名片到团队', time: '3 小时前', avatar: '👩‍🎨' },
    { who: '赵总', action: '保存了你的联系方式', time: '5 小时前', avatar: '👨‍💻' },
  ],
};

// ── CardDetailScreen ────────────────────────────────────────────────────────

export default function CardDetailScreen({ route, navigation }: any) {
  const { colors, spacing: s, radius: r, isDark } = useTheme();
  const cardId = route?.params?.cardId ?? '1';

  const [card, setCard] = useState<CardData>(DEFAULT_CARD);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCard = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const data = await api.get<CardData>(`/mobile/card/${cardId}`);
      setCard(data);
    } catch (err: any) {
      console.warn('[CardDetailScreen] Fetch failed, using defaults:', err.message);
      if (!isRefresh) setError('加载失败，显示默认数据');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [cardId]);

  useEffect(() => {
    fetchCard();
  }, [fetchCard]);

  // ── Handlers ──

  const handleShare = async () => {
    try {
      await Share.share({
        message: `认识一下 ${card.name} — ${card.title} @ ${card.company}\n${card.website}`,
      });
    } catch (err: any) {
      console.warn('Share failed:', err.message);
    }
  };

  const handleSaveContact = () => {
    Alert.alert('保存联系人', '联系人信息已保存到本地通讯录 📇');
  };

  const handleEdit = () => {
    navigation.navigate('EditCard', { cardId: card.id });
  };

  const handleViewData = () => {
    Alert.alert('名片数据', `今日访问: ${card.todayVisits}\n本月解锁: ${card.monthUnlocks}\n总转发: ${card.totalShares}`);
  };

  // ── Loading State ──

  if (loading && !refreshing) {
    return (
      <View style={[styles.center, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>加载名片详情...</Text>
      </View>
    );
  }

  // ── Render ──

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: colors.background }]}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={() => fetchCard(true)} tintColor={colors.primary} />
      }
    >
      {/* ── 名片展示卡 ── */}
      <View style={[styles.cardWrap, { backgroundColor: colors.primary, borderRadius: r.lg }]}>
        <View style={styles.cardInner}>
          {/* 顶部行 */}
          <View style={styles.cardTopRow}>
            <Text style={styles.cardKicker}>AI · Digital Business Card</Text>
            <Pressable onPress={() => navigation.goBack()} style={styles.closeBtn}>
              <Text style={{ fontSize: 18, color: '#fff' }}>✕</Text>
            </Pressable>
          </View>

          {/* 头像 + 姓名 */}
          <View style={styles.avatarSection}>
            <View style={[styles.avatarCircle, { backgroundColor: 'rgba(255,255,255,0.2)' }]}>
              <Text style={styles.avatarText}>{card.name[0]}</Text>
            </View>
            <Text style={styles.cardName}>{card.name}</Text>
            <Text style={styles.cardTitle}>{card.title}</Text>
            <Text style={styles.cardCompany}>{card.company}</Text>
          </View>

          {/* 联系信息 */}
          <View style={[styles.contactSection, { backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: r.sm }]}>
            <View style={styles.contactRow}>
              <Text style={styles.contactIcon}>📧</Text>
              <Text style={styles.contactText}>{card.email}</Text>
            </View>
            <View style={[styles.contactDivider, { backgroundColor: 'rgba(255,255,255,0.15)' }]} />
            <View style={styles.contactRow}>
              <Text style={styles.contactIcon}>📞</Text>
              <Text style={styles.contactText}>{card.phone}</Text>
            </View>
            <View style={[styles.contactDivider, { backgroundColor: 'rgba(255,255,255,0.15)' }]} />
            <View style={styles.contactRow}>
              <Text style={styles.contactIcon}>🌐</Text>
              <Text style={styles.contactText}>{card.website}</Text>
            </View>
          </View>

          {/* 标签 */}
          <View style={styles.tagRow}>
            {card.tags.map((tag) => (
              <View key={tag} style={[styles.tag, { backgroundColor: 'rgba(255,255,255,0.18)' }]}>
                <Text style={styles.tagText}>{tag}</Text>
              </View>
            ))}
          </View>

          {/* 底部二维码 */}
          <View style={styles.cardBottomRow}>
            <View>
              <Text style={styles.cardTagline}>扫码查看我的 AI 分身</Text>
              <Text style={styles.cardSubtagline}>支持 10 种语言实时对话</Text>
            </View>
            <View style={[styles.qrBox, { backgroundColor: '#fff', borderRadius: r.sm }]}>
              <Text style={{ fontSize: 28 }}>🔲</Text>
            </View>
          </View>
        </View>
      </View>

      {/* ── 报错提示 ── */}
      {error && (
        <View style={[styles.errorBanner, { backgroundColor: colors.danger + '20' }]}>
          <Text style={[styles.errorText, { color: colors.danger }]}>{error}</Text>
        </View>
      )}

      {/* ── 操作按钮组 ── */}
      <View style={styles.actionRow}>
        <Pressable style={[styles.actionBtn, { backgroundColor: colors.glassBgStrong, borderRadius: r.md }]} onPress={handleShare}>
          <Text style={{ fontSize: 22 }}>📤</Text>
          <Text style={[styles.actionLabel, { color: colors.textPrimary }]}>分享</Text>
        </Pressable>
        <Pressable style={[styles.actionBtn, { backgroundColor: colors.glassBgStrong, borderRadius: r.md }]} onPress={handleSaveContact}>
          <Text style={{ fontSize: 22 }}>💾</Text>
          <Text style={[styles.actionLabel, { color: colors.textPrimary }]}>保存</Text>
        </Pressable>
        <Pressable style={[styles.actionBtn, { backgroundColor: colors.glassBgStrong, borderRadius: r.md }]} onPress={handleEdit}>
          <Text style={{ fontSize: 22 }}>✏️</Text>
          <Text style={[styles.actionLabel, { color: colors.textPrimary }]}>编辑</Text>
        </Pressable>
        <Pressable style={[styles.actionBtn, { backgroundColor: colors.glassBgStrong, borderRadius: r.md }]} onPress={handleViewData}>
          <Text style={{ fontSize: 22 }}>📊</Text>
          <Text style={[styles.actionLabel, { color: colors.textPrimary }]}>数据</Text>
        </Pressable>
      </View>

      {/* ── 快捷统计 ── */}
      <View style={[styles.statsRow, { backgroundColor: colors.glassBg, borderRadius: r.md }]}>
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: colors.primary }]}>{card.todayVisits}</Text>
          <Text style={[styles.statLabel, { color: colors.textTertiary }]}>今日访问</Text>
        </View>
        <View style={[styles.statDivider, { backgroundColor: colors.glassBorder }]} />
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: colors.success }]}>{card.monthUnlocks}</Text>
          <Text style={[styles.statLabel, { color: colors.textTertiary }]}>本月解锁</Text>
        </View>
        <View style={[styles.statDivider, { backgroundColor: colors.glassBorder }]} />
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: colors.info }]}>{card.totalShares}</Text>
          <Text style={[styles.statLabel, { color: colors.textTertiary }]}>总转发</Text>
        </View>
      </View>

      {/* ── 信任网络 ── */}
      <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>信任网络</Text>
      <View style={[styles.trustCard, { backgroundColor: colors.glassBg, borderRadius: r.md }]}>
        <View style={styles.trustStats}>
          <View style={{ flex: 1, alignItems: 'center' }}>
            <Text style={[styles.trustValue, { color: colors.textPrimary }]}>{card.trustScore}</Text>
            <Text style={[styles.trustLabel, { color: colors.textTertiary }]}>信任分</Text>
          </View>
          <View style={{ flex: 1, alignItems: 'center' }}>
            <Text style={[styles.trustValue, { color: colors.textPrimary }]}>{card.contactCount}</Text>
            <Text style={[styles.trustLabel, { color: colors.textTertiary }]}>联系数</Text>
          </View>
          <View style={{ flex: 1, alignItems: 'center' }}>
            <Text style={[styles.trustValue, { color: colors.textPrimary }]}>{card.intimacy}</Text>
            <Text style={[styles.trustLabel, { color: colors.textTertiary }]}>亲密度</Text>
          </View>
        </View>
        <View style={[styles.trustBar, { backgroundColor: colors.glassBgStrong }]}>
          <View style={[styles.trustBarFill, { backgroundColor: colors.success, width: '92%' }]} />
        </View>
        <Text style={[styles.trustNote, { color: colors.textTertiary }]}>
          超过 92% 的同行，信任分极高 ✓
        </Text>
      </View>

      {/* ── 最近互动 ── */}
      <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>最近互动</Text>
      <View style={[styles.activityCard, { backgroundColor: colors.glassBg, borderRadius: r.md }]}>
        {card.recentInteractions.map((item, idx) => (
          <Pressable
            key={idx}
            style={[
              styles.activityItem,
              idx > 0 && { borderTopWidth: 1, borderTopColor: colors.glassBorder },
            ]}
            onPress={() => {}}
          >
            <View style={[styles.activityAvatar, { backgroundColor: colors.primaryGlow }]}>
              <Text style={{ fontSize: 16 }}>{item.avatar || item.who[0]}</Text>
            </View>
            <View style={styles.activityBody}>
              <Text style={[styles.activityText, { color: colors.textPrimary }]}>
                <Text style={{ fontWeight: '700' }}>{item.who}</Text> {item.action}
              </Text>
              <Text style={[styles.activityTime, { color: colors.textTertiary }]}>{item.time}</Text>
            </View>
            <Text style={{ color: colors.textTertiary, fontSize: 18 }}>›</Text>
          </Pressable>
        ))}
      </View>

      {/* ── 底部间距 ── */}
      <View style={{ height: 32 }} />
    </ScrollView>
  );
}

// ── Styles ──────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16, paddingBottom: 32 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { marginTop: 12, fontSize: 14 },

  // Card
  cardWrap: { marginBottom: 20, overflow: 'hidden' },
  cardInner: { padding: 24 },
  cardTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardKicker: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.85)',
    letterSpacing: 2,
    fontWeight: '600',
  },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(255,255,255,0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarSection: { alignItems: 'center', marginBottom: 20 },
  avatarCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  avatarText: { color: '#fff', fontSize: 28, fontWeight: '800' },
  cardName: { fontSize: 26, color: '#fff', fontWeight: '800' },
  cardTitle: { fontSize: 14, color: 'rgba(255,255,255,0.85)', marginTop: 4 },
  cardCompany: { fontSize: 12, color: 'rgba(255,255,255,0.7)', marginTop: 2 },

  // Contact
  contactSection: { padding: 14, marginBottom: 16 },
  contactRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 6 },
  contactIcon: { fontSize: 14, marginRight: 10 },
  contactText: { fontSize: 13, color: '#fff' },
  contactDivider: { height: 1, marginVertical: 2 },

  // Tags
  tagRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 },
  tag: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 10 },
  tagText: { color: '#fff', fontSize: 11, fontWeight: '600' },

  // Bottom
  cardBottomRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardTagline: { fontSize: 13, color: '#fff', fontWeight: '700' },
  cardSubtagline: { fontSize: 11, color: 'rgba(255,255,255,0.75)', marginTop: 2 },
  qrBox: { width: 64, height: 64, alignItems: 'center', justifyContent: 'center' },

  // Error
  errorBanner: { padding: 12, borderRadius: 10, marginBottom: 16 },
  errorText: { fontSize: 13, fontWeight: '500' },

  // Actions
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  actionBtn: {
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 4,
    flex: 1,
    marginHorizontal: 4,
    gap: 6,
  },
  actionLabel: { fontSize: 12, fontWeight: '600' },

  // Stats Row
  statsRow: {
    flexDirection: 'row',
    padding: 16,
    marginBottom: 24,
  },
  statItem: { flex: 1, alignItems: 'center' },
  statValue: { fontSize: 22, fontWeight: '800' },
  statLabel: { fontSize: 11, marginTop: 4 },
  statDivider: { width: 1, height: 28, marginHorizontal: 8 },

  // Trust
  sectionTitle: { fontSize: 17, fontWeight: '700', marginBottom: 12, paddingHorizontal: 4 },
  trustCard: { padding: 16, marginBottom: 24 },
  trustStats: { flexDirection: 'row', marginBottom: 16 },
  trustValue: { fontSize: 22, fontWeight: '800' },
  trustLabel: { fontSize: 11, marginTop: 4 },
  trustBar: { height: 8, borderRadius: 4, overflow: 'hidden' },
  trustBarFill: { height: '100%', borderRadius: 4 },
  trustNote: { fontSize: 12, marginTop: 8 },

  // Activity
  activityCard: { padding: 16 },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
  },
  activityAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  activityBody: { flex: 1 },
  activityText: { fontSize: 14, lineHeight: 20 },
  activityTime: { fontSize: 11, marginTop: 2 },
});
