/**
 * 名片 Screen — 我的电子名片 / 分享 / 信任网络
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
} from 'react-native';
import { useTheme } from '../theme/theme-context';

export default function CardScreen({ navigation }: any) {
  const { colors, radius: r } = useTheme();

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: colors.background }]}
      contentContainerStyle={styles.content}
    >
      {/* 3D 名片卡 — 点击进入详情 */}
      <Pressable
        onPress={() => navigation.navigate('CardDetail', { cardId: '1' })}
        activeOpacity={0.9}
      >
        <View style={[styles.cardWrap, { backgroundColor: colors.primary, borderRadius: r.lg }]}>
          <View style={styles.cardInner}>
            <View style={styles.cardTopRow}>
              <Text style={styles.cardKicker}>AI · Digital · Business Card</Text>
              <Text style={{ fontSize: 20 }}>✨</Text>
            </View>
            <View style={styles.cardNameBlock}>
              <Text style={styles.cardName}>海容 · 向</Text>
              <Text style={styles.cardTitle}>AI 数字名片创始人 · 链客宝</Text>
            </View>
            <Text style={styles.cardSlogan}>让信任自动流动，让价值即时连接</Text>
            <View style={styles.cardMeta}>
              <View style={styles.metaItem}>
                <Text style={styles.metaText}>📧 hirongxiang@ncard.ai</Text>
              </View>
              <View style={styles.metaItem}>
                <Text style={styles.metaText}>📞 +86 138-****-8888</Text>
              </View>
              <View style={styles.metaItem}>
                <Text style={styles.metaText}>🌐 ai-digital-card.com</Text>
              </View>
            </View>
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
      </Pressable>

      {/* 操作按钮组 */}
      <View style={styles.actionRow}>
        {[
          { icon: '📤', label: '分享' },
          { icon: '💾', label: '保存' },
          { icon: '✏️', label: '编辑', screen: 'EditCard' },
          { icon: '📊', label: '数据' },
        ].map((a) => (
          <Pressable
            key={a.label}
            style={[styles.actionBtn, { backgroundColor: colors.glassBgStrong, borderRadius: r.md }]}
            onPress={() => {
              if (a.screen) {
                navigation.navigate(a.screen, { cardId: '1' });
              }
            }}
          >
            <Text style={{ fontSize: 22 }}>{a.icon}</Text>
            <Text style={[styles.actionLabel, { color: colors.textPrimary }]}>{a.label}</Text>
          </Pressable>
        ))}
      </View>

      {/* 信任网络 */}
      <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>我的信任网络</Text>
      <View style={[styles.trustCard, { backgroundColor: colors.glassBg, borderRadius: r.md }]}>
        <View style={styles.trustStats}>
          <View style={{ flex: 1, alignItems: 'center' }}>
            <Text style={[styles.trustValue, { color: colors.textPrimary }]}>9.2</Text>
            <Text style={[styles.trustLabel, { color: colors.textTertiary }]}>信任分</Text>
          </View>
          <View style={{ flex: 1, alignItems: 'center' }}>
            <Text style={[styles.trustValue, { color: colors.textPrimary }]}>248</Text>
            <Text style={[styles.trustLabel, { color: colors.textTertiary }]}>联系数</Text>
          </View>
          <View style={{ flex: 1, alignItems: 'center' }}>
            <Text style={[styles.trustValue, { color: colors.textPrimary }]}>高</Text>
            <Text style={[styles.trustLabel, { color: colors.textTertiary }]}>亲密度</Text>
          </View>
        </View>
        <View style={[styles.trustBar, { backgroundColor: colors.glassBg }]}>
          <View style={[styles.trustBarFill, { backgroundColor: colors.success, width: '92%' }]} />
        </View>
        <Text style={[styles.trustNote, { color: colors.textTertiary }]}>
          超过 92% 的同行，信任分极高
        </Text>
      </View>

      {/* 多端设备 */}
      <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>多端设备</Text>
      <View style={[styles.deviceCard, { backgroundColor: colors.glassBg, borderRadius: r.md }]}>
        {[
          { device: 'iPhone 15 Pro', last: '2 分钟前', icon: '📱' },
          { device: 'MacBook Pro', last: '5 小时前', icon: '💻' },
          { device: 'iPad Pro', last: '昨天', icon: '📟' },
        ].map((d, i) => (
          <View
            key={i}
            style={[
              styles.deviceRow,
              i > 0 && { borderTopWidth: 1, borderTopColor: colors.glassBorder },
            ]}
          >
            <View style={[styles.deviceIcon, { backgroundColor: colors.primaryGlow, borderRadius: r.sm }]}>
              <Text style={{ fontSize: 18 }}>{d.icon}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[styles.deviceName, { color: colors.textPrimary }]}>{d.device}</Text>
              <Text style={[styles.deviceLast, { color: colors.textTertiary }]}>最近同步：{d.last}</Text>
            </View>
            <Text style={{ color: colors.success, fontSize: 18 }}>✅</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16, paddingBottom: 32 },
  cardWrap: { marginBottom: 20, overflow: 'hidden' },
  cardInner: { padding: 28 },
  cardTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardKicker: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.85)',
    letterSpacing: 2,
    fontWeight: '600',
  },
  cardNameBlock: { marginTop: 12 },
  cardName: { fontSize: 28, color: '#fff', fontWeight: '800' },
  cardTitle: { fontSize: 13, color: 'rgba(255,255,255,0.85)', marginTop: 4 },
  cardSlogan: { fontSize: 13, color: 'rgba(255,255,255,0.85)', fontStyle: 'italic', marginTop: 4 },
  cardMeta: { gap: 8, marginTop: 12 },
  metaItem: { flexDirection: 'row', alignItems: 'center' },
  metaText: { fontSize: 12, color: 'rgba(255,255,255,0.9)' },
  cardBottomRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 16,
  },
  cardTagline: { fontSize: 13, color: '#fff', fontWeight: '700' },
  cardSubtagline: { fontSize: 11, color: 'rgba(255,255,255,0.75)', marginTop: 2 },
  qrBox: { width: 64, height: 64, alignItems: 'center', justifyContent: 'center' },
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 28,
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
  sectionTitle: { fontSize: 17, fontWeight: '700', marginBottom: 12, paddingHorizontal: 4 },
  trustCard: { padding: 16, marginBottom: 28 },
  trustStats: { flexDirection: 'row', marginBottom: 16 },
  trustValue: { fontSize: 22, fontWeight: '800' },
  trustLabel: { fontSize: 11, marginTop: 4 },
  trustBar: { height: 8, borderRadius: 4, overflow: 'hidden' },
  trustBarFill: { height: '100%', borderRadius: 4 },
  trustNote: { fontSize: 12, marginTop: 8 },
  deviceCard: { padding: 16 },
  deviceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
  },
  deviceIcon: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  deviceName: { fontSize: 14, fontWeight: '600' },
  deviceLast: { fontSize: 11, marginTop: 2 },
});
