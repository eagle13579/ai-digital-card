/**
 * 匹配 Screen — 发现 / 人脉匹配 / AI 推荐
 * 功能:
 *  - 展示匹配推荐列表
 *  - 基于信任分的智能匹配算法入口
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  TextInput,
} from 'react-native';
import { useTheme } from '../theme/theme-context';

interface MatchUser {
  id: string;
  name: string;
  title: string;
  trustScore: number;
  matchRate: number;
  tags: string[];
  avatar: string;
  mutualContacts?: number;
}

const MOCK_MATCHES: MatchUser[] = [
  {
    id: '1',
    name: '李博士',
    title: '金融科技 VP · 链客宝战略伙伴',
    trustScore: 8.9,
    matchRate: 92,
    tags: ['金融', '区块链', '高净值'],
    avatar: '👨‍💼',
    mutualContacts: 7,
  },
  {
    id: '2',
    name: '王总',
    title: '产品创新总监 · 前阿里',
    trustScore: 8.5,
    matchRate: 88,
    tags: ['产品', 'SaaS', 'AI'],
    avatar: '👨‍🚀',
    mutualContacts: 12,
  },
  {
    id: '3',
    name: '陈医生',
    title: 'AI 心理咨询创始人',
    trustScore: 9.1,
    matchRate: 85,
    tags: ['心理', 'AI', '健康'],
    avatar: '🧑‍⚕️',
    mutualContacts: 3,
  },
  {
    id: '4',
    name: 'Lina',
    title: '品牌设计师 · 曾获红点奖',
    trustScore: 7.8,
    matchRate: 79,
    tags: ['设计', '品牌', '创意'],
    avatar: '👩‍🎨',
    mutualContacts: 5,
  },
  {
    id: '5',
    name: '赵总',
    title: '连续创业者 · AI 赛道',
    trustScore: 8.2,
    matchRate: 76,
    tags: ['创业', 'AI', '投资'],
    avatar: '👨‍💻',
    mutualContacts: 1,
  },
];

export default function MatchScreen({ navigation }: any) {
  const { colors, spacing: s, radius: r } = useTheme();
  const [search, setSearch] = useState('');
  const [matches] = useState<MatchUser[]>(MOCK_MATCHES);

  const filtered = search
    ? matches.filter(
        (m) =>
          m.name.includes(search) ||
          m.title.includes(search) ||
          m.tags.some((t) => t.includes(search)),
      )
    : matches;

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: colors.background }]}
      contentContainerStyle={styles.content}
    >
      {/* 搜索栏 */}
      <TextInput
        style={[
          styles.searchInput,
          {
            backgroundColor: colors.glassBgStrong,
            color: colors.textPrimary,
            borderRadius: r.md,
            borderColor: colors.glassBorder,
          },
        ]}
        placeholder="搜索姓名、行业、标签..."
        placeholderTextColor={colors.textTertiary}
        value={search}
        onChangeText={setSearch}
      />

      {/* 匹配概览 */}
      <View style={[styles.summaryCard, { backgroundColor: colors.glassBg, borderRadius: r.md }]}>
        <Text style={[styles.summaryTitle, { color: colors.textPrimary }]}>
          今日推荐匹配
        </Text>
        <Text style={[styles.summarySub, { color: colors.textSecondary }]}>
          基于你的信任网络和 AI 算法，为你推荐以下人脉
        </Text>
        <View style={styles.summaryStats}>
          <View style={styles.summaryStat}>
            <Text style={[styles.summaryValue, { color: colors.primary }]}>5</Text>
            <Text style={[styles.summaryLabel, { color: colors.textTertiary }]}>今日推荐</Text>
          </View>
          <View style={styles.summaryStat}>
            <Text style={[styles.summaryValue, { color: colors.success }]}>92%</Text>
            <Text style={[styles.summaryLabel, { color: colors.textTertiary }]}>最高匹配</Text>
          </View>
          <View style={styles.summaryStat}>
            <Text style={[styles.summaryValue, { color: colors.info }]}>28</Text>
            <Text style={[styles.summaryLabel, { color: colors.textTertiary }]}>共同联系人</Text>
          </View>
        </View>
      </View>

      {/* 匹配列表 */}
      <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>
        推荐人脉 ({filtered.length})
      </Text>
      {filtered.map((user) => (
        <Pressable
          key={user.id}
          style={[
            styles.matchCard,
            { backgroundColor: colors.glassBgStrong, borderRadius: r.lg },
          ]}
          onPress={() => navigation.navigate('MatchDetail', { matchId: user.id })}
        >
          <View style={styles.matchLeft}>
            <Text style={styles.matchAvatar}>{user.avatar}</Text>
            <View style={styles.matchRateBadge}>
              <Text style={styles.matchRateText}>{user.matchRate}%</Text>
            </View>
          </View>
          <View style={styles.matchBody}>
            <Text style={[styles.matchName, { color: colors.textPrimary }]}>{user.name}</Text>
            <Text style={[styles.matchTitle, { color: colors.textSecondary }]}>{user.title}</Text>
            <View style={styles.matchTags}>
              {user.tags.map((tag) => (
                <View
                  key={tag}
                  style={[styles.tag, { backgroundColor: colors.primaryGlow }]}
                >
                  <Text style={[styles.tagText, { color: colors.primary }]}>{tag}</Text>
                </View>
              ))}
            </View>
            <View style={styles.matchFooter}>
              <Text style={[styles.matchTrust, { color: colors.success }]}>
                信任分 {user.trustScore}
              </Text>
              {user.mutualContacts && (
                <Text style={[styles.matchMutual, { color: colors.textTertiary }]}>
                  {user.mutualContacts} 个共同联系人
                </Text>
              )}
            </View>
          </View>
          <Pressable
            style={[styles.connectBtn, { backgroundColor: colors.primary }]}
            onPress={() => navigation.navigate('MatchDetail', { matchId: user.id })}
          >
            <Text style={styles.connectBtnText}>连接</Text>
          </Pressable>
        </Pressable>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16, paddingBottom: 32 },
  searchInput: {
    height: 44,
    paddingHorizontal: 16,
    fontSize: 15,
    borderWidth: 1,
    marginBottom: 20,
  },
  summaryCard: { padding: 20, marginBottom: 24 },
  summaryTitle: { fontSize: 18, fontWeight: '800', marginBottom: 6 },
  summarySub: { fontSize: 13, lineHeight: 18, marginBottom: 16 },
  summaryStats: { flexDirection: 'row' },
  summaryStat: { flex: 1, alignItems: 'center' },
  summaryValue: { fontSize: 24, fontWeight: '800' },
  summaryLabel: { fontSize: 11, marginTop: 4 },
  sectionTitle: { fontSize: 17, fontWeight: '700', marginBottom: 12, paddingHorizontal: 4 },
  matchCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginBottom: 12,
  },
  matchLeft: { alignItems: 'center', marginRight: 14 },
  matchAvatar: { fontSize: 36, marginBottom: 4 },
  matchRateBadge: {
    backgroundColor: '#6366f1',
    borderRadius: 8,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  matchRateText: { color: '#fff', fontSize: 11, fontWeight: '800' },
  matchBody: { flex: 1 },
  matchName: { fontSize: 16, fontWeight: '700' },
  matchTitle: { fontSize: 12, marginTop: 2, lineHeight: 16 },
  matchTags: { flexDirection: 'row', gap: 6, marginTop: 6, flexWrap: 'wrap' },
  tag: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8 },
  tagText: { fontSize: 10, fontWeight: '700' },
  matchFooter: { flexDirection: 'row', gap: 12, marginTop: 6 },
  matchTrust: { fontSize: 11, fontWeight: '700' },
  matchMutual: { fontSize: 11 },
  connectBtn: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    marginLeft: 8,
  },
  connectBtnText: { color: '#fff', fontSize: 13, fontWeight: '700' },
});
