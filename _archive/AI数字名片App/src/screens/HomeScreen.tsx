/**
 * 首页 Screen — 动态流 / 控制台
 * 功能:
 *  - 调用 GET /api/v1/mobile/feed 获取动态数据
 *  - 展示 AI 数字名片摘要、今日访客统计、推荐AI分身、最近互动
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
} from 'react-native';
import { useTheme } from '../theme/theme-context';
import { api } from '../api/client';

// ── Types ───────────────────────────────────────────────────────────────────

interface FeedData {
  greeting: string;
  todayVisits: number;
  trustScore: number;
  monthUnlocks: number;
  stats: Array<{ label: string; value: string; delta: string; color: string }>;
  recommendedAvatars: Array<{ id: string; name: string; desc: string; emoji: string }>;
  recentActivity: Array<{ who: string; action: string; time: string }>;
}

const defaultFeed: FeedData = {
  greeting: '早上好 👋',
  todayVisits: 128,
  trustScore: 9.2,
  monthUnlocks: 47,
  stats: [
    { label: '访问', value: '128', delta: '+12%', color: '#6366f1' },
    { label: '解锁', value: '34', delta: '+8%', color: '#22c55e' },
    { label: '成交', value: '5', delta: '+25%', color: '#f59e0b' },
    { label: '转发', value: '72', delta: '+18%', color: '#3b82f6' },
  ],
  recommendedAvatars: [
    { id: '1', name: '金融顾问', desc: '李博士', emoji: '💼' },
    { id: '2', name: '产品专家', desc: '王总', emoji: '🚀' },
    { id: '3', name: '心理咨询师', desc: '陈医生', emoji: '🧠' },
    { id: '4', name: '品牌设计师', desc: 'Lina', emoji: '🎨' },
  ],
  recentActivity: [
    { who: '张总', action: '查看了你的名片', time: '2 分钟前' },
    { who: '李博士', action: '与你的 AI 分身对话', time: '12 分钟前' },
    { who: '王总', action: '解锁了 AI 产品手册', time: '1 小时前' },
    { who: 'Lina', action: '转发了你的名片', time: '3 小时前' },
  ],
};

// ── HomeScreen ──────────────────────────────────────────────────────────────

export default function HomeScreen() {
  const { colors, spacing: s, radius: r, isDark } = useTheme();
  const [feed, setFeed] = useState<FeedData>(defaultFeed);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFeed = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const data = await api.get<FeedData>('/mobile/feed');
      setFeed(data);
    } catch (err: any) {
      console.warn('[HomeScreen] Feed fetch failed, using defaults:', err.message);
      if (!isRefresh) setError('加载失败，显示默认数据');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchFeed();
  }, [fetchFeed]);

  // ── Render ──

  if (loading && !refreshing) {
    return (
      <View style={[styles.center, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>加载中...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: colors.background }]}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={() => fetchFeed(true)} tintColor={colors.primary} />
      }
    >
      {/* 头部 */}
      <View style={[styles.headerRow, { marginBottom: s.xl }]}>
        <View>
          <Text style={[styles.greeting, { color: colors.textSecondary }]}>{feed.greeting}</Text>
          <Text style={[styles.name, { color: colors.textPrimary }]}>数字名片 · 控制台</Text>
        </View>
        <Pressable
          style={[styles.notifBtn, { backgroundColor: colors.glassBgStrong }]}
          onPress={() => {}}
        >
          <Text style={[styles.notifIcon, { color: colors.textPrimary }]}>🔔</Text>
          <View style={[styles.badge, { backgroundColor: colors.danger }]} />
        </Pressable>
      </View>

      {/* Hero 名片摘要卡 */}
      <View style={[styles.heroCard, { backgroundColor: colors.primary }]}>
        <View style={styles.heroInner}>
          <Text style={styles.heroKicker}>你的 AI 名片</Text>
          <Text style={styles.heroName}>海容 · 链客宝</Text>
          <Text style={styles.heroDesc}>让信任自动流动，让价值即时连接</Text>
          <View style={styles.heroStats}>
            <View style={styles.heroStat}>
              <Text style={styles.heroStatValue}>{feed.todayVisits}</Text>
              <Text style={styles.heroStatLabel}>今日访客</Text>
            </View>
            <View style={[styles.divider, { backgroundColor: 'rgba(255,255,255,0.2)' }]} />
            <View style={styles.heroStat}>
              <Text style={styles.heroStatValue}>{feed.trustScore}</Text>
              <Text style={styles.heroStatLabel}>信任分</Text>
            </View>
            <View style={[styles.divider, { backgroundColor: 'rgba(255,255,255,0.2)' }]} />
            <View style={styles.heroStat}>
              <Text style={styles.heroStatValue}>{feed.monthUnlocks}</Text>
              <Text style={styles.heroStatLabel}>本月解锁</Text>
            </View>
          </View>
          <Pressable style={styles.heroCta}>
            <Text style={styles.heroCtaText}>查看 AI 分身</Text>
          </Pressable>
        </View>
      </View>

      {/* 报错提示 */}
      {error && (
        <View style={[styles.errorBanner, { backgroundColor: colors.danger + '20' }]}>
          <Text style={[styles.errorText, { color: colors.danger }]}>{error}</Text>
        </View>
      )}

      {/* 今日动态统计 */}
      <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>今日动态</Text>
      <View style={styles.statsGrid}>
        {feed.stats.map((stat) => (
          <View
            key={stat.label}
            style={[
              styles.statCard,
              { backgroundColor: colors.glassBgStrong, borderRadius: r.md },
            ]}
          >
            <Text style={[styles.statValue, { color: colors.textPrimary }]}>{stat.value}</Text>
            <Text style={[styles.statLabel, { color: colors.textSecondary }]}>{stat.label}</Text>
            <View style={[styles.deltaBadge, { backgroundColor: stat.color + '20' }]}>
              <Text style={[styles.deltaText, { color: stat.color }]}>{stat.delta}</Text>
            </View>
          </View>
        ))}
      </View>

      {/* 推荐的 AI 分身 */}
      <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>推荐的 AI 分身</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.avatarRow}>
        {feed.recommendedAvatars.map((a) => (
          <Pressable
            key={a.id}
            onPress={() => {}}
            style={[styles.avatarCard, { backgroundColor: colors.glassBgStrong, borderRadius: r.lg }]}
          >
            <Text style={styles.avatarEmoji}>{a.emoji}</Text>
            <Text style={[styles.avatarName, { color: colors.textPrimary }]}>{a.name}</Text>
            <Text style={[styles.avatarDesc, { color: colors.textTertiary }]}>{a.desc}</Text>
          </Pressable>
        ))}
      </ScrollView>

      {/* 最近互动 */}
      <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>最近互动</Text>
      <View style={[styles.activityCard, { backgroundColor: colors.glassBg, borderRadius: r.md }]}>
        {feed.recentActivity.map((item, idx) => (
          <View
            key={idx}
            style={[
              styles.activityItem,
              idx > 0 && { borderTopWidth: 1, borderTopColor: colors.glassBorder },
            ]}
          >
            <View style={[styles.activityAvatar, { backgroundColor: colors.primaryGlow }]}>
              <Text style={[styles.activityInitial, { color: colors.primary }]}>{item.who[0]}</Text>
            </View>
            <View style={styles.activityBody}>
              <Text style={[styles.activityText, { color: colors.textPrimary }]}>
                <Text style={{ fontWeight: '700' }}>{item.who}</Text> {item.action}
              </Text>
              <Text style={[styles.activityTime, { color: colors.textTertiary }]}>{item.time}</Text>
            </View>
            <Text style={{ color: colors.textTertiary }}>›</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

// ── Styles ──────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16, paddingBottom: 32 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { marginTop: 12, fontSize: 14 },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  greeting: { fontSize: 13, marginBottom: 4 },
  name: { fontSize: 22, fontWeight: '800' },
  notifBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  notifIcon: { fontSize: 20 },
  badge: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  heroCard: {
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 24,
  },
  heroInner: { padding: 24 },
  heroKicker: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.75)',
    fontWeight: '600',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  heroName: { fontSize: 26, color: '#fff', fontWeight: '800', marginBottom: 4 },
  heroDesc: { fontSize: 14, color: 'rgba(255,255,255,0.85)', marginBottom: 20 },
  heroStats: { flexDirection: 'row', alignItems: 'center', marginBottom: 20 },
  heroStat: { flex: 1, alignItems: 'center' },
  heroStatValue: { fontSize: 22, color: '#fff', fontWeight: '800' },
  heroStatLabel: { fontSize: 11, color: 'rgba(255,255,255,0.7)' },
  divider: { width: 1, height: 32 },
  heroCta: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
  },
  heroCtaText: { color: '#fff', fontSize: 15, fontWeight: '700' },
  errorBanner: { padding: 12, borderRadius: 10, marginBottom: 16 },
  errorText: { fontSize: 13, fontWeight: '500' },
  sectionTitle: { fontSize: 17, fontWeight: '700', marginBottom: 12, paddingHorizontal: 4 },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 28,
  },
  statCard: {
    width: '48%',
    marginBottom: 10,
    padding: 16,
  },
  statValue: { fontSize: 24, fontWeight: '800' },
  statLabel: { fontSize: 12, marginTop: 4 },
  deltaBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    marginTop: 8,
  },
  deltaText: { fontSize: 11, fontWeight: '700' },
  avatarRow: { gap: 12, paddingRight: 4 },
  avatarCard: {
    width: 110,
    height: 140,
    padding: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  avatarEmoji: { fontSize: 36, marginBottom: 6 },
  avatarName: { fontSize: 13, fontWeight: '700', textAlign: 'center' },
  avatarDesc: { fontSize: 11, textAlign: 'center', marginTop: 2 },
  activityCard: { padding: 16, marginBottom: 16 },
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
  activityInitial: { fontSize: 14, fontWeight: '800' },
  activityBody: { flex: 1 },
  activityText: { fontSize: 14, lineHeight: 20 },
  activityTime: { fontSize: 11, marginTop: 2 },
});
