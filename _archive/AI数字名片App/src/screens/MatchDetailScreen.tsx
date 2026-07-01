/**
 * 匹配详情 Screen — 查看匹配人脉详细信息
 * 导航: MatchScreen -> MatchDetailScreen (params: { matchId })
 *
 * 功能:
 *  - 用户信息 (头像/姓名/职位/公司/标签)
 *  - 匹配评分展示 (匹配度/信任分/共同性)
 *  - 共同联系人列表
 *  - 发起沟通 (发送消息/交换名片/预约会议)
 *  - API: GET /mobile/match/:id
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
  Alert,
  Share,
} from 'react-native';
import { useTheme } from '../theme/theme-context';
import { api } from '../api/client';

// ── Types ───────────────────────────────────────────────────────────────────

interface MatchDetailData {
  id: string;
  name: string;
  title: string;
  company: string;
  tags: string[];
  avatar: string;
  bio: string;

  // Match scores
  matchRate: number;
  trustScore: number;
  commonality: string;
  matchBreakdown: Array<{ label: string; score: number; color: string }>;

  // Mutual contacts
  mutualContacts: Array<{
    id: string;
    name: string;
    title: string;
    avatar: string;
  }>;

  // Recent activity on this person
  recentActivity: string;
}

const DEFAULT_MATCH: MatchDetailData = {
  id: '1',
  name: '李博士',
  title: '金融科技 VP',
  company: '链客宝战略合作伙伴',
  tags: ['金融', '区块链', '高净值客户', '创新'],
  avatar: '👨‍💼',
  bio: '专注金融科技领域15年，曾主导多个区块链落地项目，对AI+金融有深入研究和独到见解。',

  matchRate: 92,
  trustScore: 8.9,
  commonality: '高度一致',
  matchBreakdown: [
    { label: '行业匹配', score: 95, color: '#6366f1' },
    { label: '信任网络', score: 88, color: '#22c55e' },
    { label: '兴趣标签', score: 90, color: '#f59e0b' },
    { label: '地理位置', score: 72, color: '#3b82f6' },
  ],

  mutualContacts: [
    { id: 'c1', name: '海容 · 向', title: 'AI 数字名片创始人', avatar: '👤' },
    { id: 'c2', name: '王总', title: '产品创新总监', avatar: '👨‍🚀' },
    { id: 'c3', name: '陈医生', title: 'AI 心理咨询创始人', avatar: '🧑‍⚕️' },
    { id: 'c4', name: 'Lina', title: '品牌设计师', avatar: '👩‍🎨' },
  ],

  recentActivity: '3 天前更新了个人资料 · 活跃度高',
};

// ── MatchDetailScreen ──────────────────────────────────────────────────────

export default function MatchDetailScreen({ route, navigation }: any) {
  const { colors, spacing: s, radius: r, isDark } = useTheme();
  const matchId = route?.params?.matchId ?? '1';

  const [detail, setDetail] = useState<MatchDetailData>(DEFAULT_MATCH);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const data = await api.get<MatchDetailData>(`/mobile/match/${matchId}`);
      setDetail(data);
    } catch (err: any) {
      console.warn('[MatchDetailScreen] Fetch failed, using defaults:', err.message);
      if (!isRefresh) setError('加载失败，显示默认数据');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [matchId]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  // ── Actions ──

  const handleSendMessage = () => {
    Alert.alert('发送消息', `即将与 ${detail.name} 开始聊天 💬`);
  };

  const handleExchangeCard = async () => {
    try {
      await Share.share({
        message: `你好！我是海容 · 向，很高兴认识你！这是我的数字名片：https://ncard.ai/card/1`,
      });
    } catch (err: any) {
      console.warn('Share failed:', err.message);
    }
  };

  const handleScheduleMeeting = () => {
    Alert.alert('预约会议', `即将与 ${detail.name} 预约会议时间 📅`);
  };

  // ── Loading ──

  if (loading && !refreshing) {
    return (
      <View style={[styles.center, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>加载匹配详情...</Text>
      </View>
    );
  }

  // ── Render ──

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: colors.background }]}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={() => fetchDetail(true)} tintColor={colors.primary} />
      }
    >
      {/* ── 用户信息头部 ── */}
      <View style={[styles.profileHeader, { backgroundColor: colors.glassBg, borderRadius: r.lg }]}>
        <Pressable
          style={styles.backBtn}
          onPress={() => navigation.goBack()}
        >
          <Text style={{ fontSize: 20, color: colors.textSecondary }}>‹ 返回</Text>
        </Pressable>
        <View style={styles.profileAvatarSection}>
          <View style={[styles.profileAvatar, { backgroundColor: colors.primaryGlow }]}>
            <Text style={{ fontSize: 48 }}>{detail.avatar}</Text>
          </View>
          <Text style={[styles.profileName, { color: colors.textPrimary }]}>{detail.name}</Text>
          <Text style={[styles.profileTitle, { color: colors.textSecondary }]}>{detail.title}</Text>
          <Text style={[styles.profileCompany, { color: colors.textTertiary }]}>{detail.company}</Text>
        </View>
        {/* 标签 */}
        <View style={styles.profileTags}>
          {detail.tags.map((tag) => (
            <View key={tag} style={[styles.tag, { backgroundColor: colors.primaryGlow }]}>
              <Text style={[styles.tagText, { color: colors.primary }]}>{tag}</Text>
            </View>
          ))}
        </View>
        {/* 简介 */}
        <Text style={[styles.bio, { color: colors.textSecondary }]}>{detail.bio}</Text>
        {/* 最近动态 */}
        <Text style={[styles.recentActivity, { color: colors.textTertiary }]}>
          {detail.recentActivity}
        </Text>
      </View>

      {/* ── 报错提示 ── */}
      {error && (
        <View style={[styles.errorBanner, { backgroundColor: colors.danger + '20' }]}>
          <Text style={[styles.errorText, { color: colors.danger }]}>{error}</Text>
        </View>
      )}

      {/* ── 匹配评分 ── */}
      <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>匹配评分</Text>
      <View style={[styles.matchScoreCard, { backgroundColor: colors.glassBg, borderRadius: r.md }]}>
        <View style={styles.matchScoreBig}>
          <Text style={[styles.matchScoreValue, { color: colors.primary }]}>{detail.matchRate}%</Text>
          <Text style={[styles.matchScoreLabel, { color: colors.textTertiary }]}>综合匹配度</Text>
        </View>
        <View style={styles.matchBreakdownContainer}>
          {detail.matchBreakdown.map((item) => (
            <View key={item.label} style={styles.breakdownRow}>
              <Text style={[styles.breakdownLabel, { color: colors.textSecondary }]}>{item.label}</Text>
              <View style={[styles.breakdownBar, { backgroundColor: colors.glassBgStrong }]}>
                <View
                  style={[
                    styles.breakdownFill,
                    {
                      backgroundColor: item.color,
                      width: `${item.score}%`,
                    },
                  ]}
                />
              </View>
              <Text style={[styles.breakdownScore, { color: item.color }]}>{item.score}%</Text>
            </View>
          ))}
        </View>
        {/* 信任分 */}
        <View style={[styles.trustRow, { borderTopColor: colors.glassBorder }]}>
          <Text style={[styles.trustLabel, { color: colors.textSecondary }]}>信任分</Text>
          <View style={styles.trustRight}>
            <Text style={[styles.trustScore, { color: colors.success }]}>{detail.trustScore}</Text>
            <Text style={[styles.commonality, { color: colors.textTertiary }]}>
              · 共同性 {detail.commonality}
            </Text>
          </View>
        </View>
      </View>

      {/* ── 共同联系人 ── */}
      <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>
        共同联系人 ({detail.mutualContacts.length})
      </Text>
      <View style={[styles.mutualCard, { backgroundColor: colors.glassBg, borderRadius: r.md }]}>
        {detail.mutualContacts.map((contact, idx) => (
          <Pressable
            key={contact.id}
            style={[
              styles.mutualRow,
              idx > 0 && { borderTopWidth: 1, borderTopColor: colors.glassBorder },
            ]}
            onPress={() => {}}
          >
            <View style={[styles.mutualAvatar, { backgroundColor: colors.primaryGlow }]}>
              <Text style={{ fontSize: 18 }}>{contact.avatar}</Text>
            </View>
            <View style={styles.mutualBody}>
              <Text style={[styles.mutualName, { color: colors.textPrimary }]}>{contact.name}</Text>
              <Text style={[styles.mutualTitle, { color: colors.textTertiary }]}>{contact.title}</Text>
            </View>
            <Text style={{ color: colors.textTertiary, fontSize: 18 }}>›</Text>
          </Pressable>
        ))}
      </View>

      {/* ── 操作按钮 ── */}
      <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>发起沟通</Text>
      <View style={styles.actionRow}>
        <Pressable
          style={[styles.actionBtn, { backgroundColor: colors.primary, borderRadius: r.md }]}
          onPress={handleSendMessage}
        >
          <Text style={{ fontSize: 22 }}>💬</Text>
          <Text style={[styles.actionLabel, { color: '#fff' }]}>发送消息</Text>
        </Pressable>
        <Pressable
          style={[styles.actionBtn, { backgroundColor: colors.glassBgStrong, borderRadius: r.md }]}
          onPress={handleExchangeCard}
        >
          <Text style={{ fontSize: 22 }}>📇</Text>
          <Text style={[styles.actionLabel, { color: colors.textPrimary }]}>交换名片</Text>
        </Pressable>
        <Pressable
          style={[styles.actionBtn, { backgroundColor: colors.glassBgStrong, borderRadius: r.md }]}
          onPress={handleScheduleMeeting}
        >
          <Text style={{ fontSize: 22 }}>📅</Text>
          <Text style={[styles.actionLabel, { color: colors.textPrimary }]}>预约会议</Text>
        </Pressable>
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

  // Profile Header
  profileHeader: { padding: 20, marginBottom: 20, overflow: 'hidden' },
  backBtn: { marginBottom: 12, alignSelf: 'flex-start' },
  profileAvatarSection: { alignItems: 'center', marginBottom: 16 },
  profileAvatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  profileName: { fontSize: 24, fontWeight: '800' },
  profileTitle: { fontSize: 14, marginTop: 4 },
  profileCompany: { fontSize: 12, marginTop: 2 },
  profileTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 12,
  },
  tag: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  tagText: { fontSize: 11, fontWeight: '700' },
  bio: { fontSize: 13, lineHeight: 20, textAlign: 'center', marginBottom: 8 },
  recentActivity: { fontSize: 11, textAlign: 'center' },

  // Error
  errorBanner: { padding: 12, borderRadius: 10, marginBottom: 16 },
  errorText: { fontSize: 13, fontWeight: '500' },

  // Match Score
  sectionTitle: { fontSize: 17, fontWeight: '700', marginBottom: 12, paddingHorizontal: 4 },
  matchScoreCard: { padding: 16, marginBottom: 24 },
  matchScoreBig: { alignItems: 'center', marginBottom: 16 },
  matchScoreValue: { fontSize: 40, fontWeight: '800' },
  matchScoreLabel: { fontSize: 12, marginTop: 4 },
  matchBreakdownContainer: { gap: 10, marginBottom: 16 },
  breakdownRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  breakdownLabel: { width: 64, fontSize: 12, fontWeight: '600' },
  breakdownBar: {
    flex: 1,
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  breakdownFill: { height: '100%', borderRadius: 4 },
  breakdownScore: { width: 36, fontSize: 12, fontWeight: '700', textAlign: 'right' },
  trustRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
  },
  trustLabel: { fontSize: 13, fontWeight: '600' },
  trustRight: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  trustScore: { fontSize: 15, fontWeight: '800' },
  commonality: { fontSize: 12 },

  // Mutual Contacts
  mutualCard: { padding: 16, marginBottom: 24 },
  mutualRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
  mutualAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  mutualBody: { flex: 1 },
  mutualName: { fontSize: 14, fontWeight: '700' },
  mutualTitle: { fontSize: 11, marginTop: 2 },

  // Actions
  actionRow: {
    flexDirection: 'row',
    gap: 10,
  },
  actionBtn: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 16,
    gap: 8,
  },
  actionLabel: { fontSize: 13, fontWeight: '700' },
});
