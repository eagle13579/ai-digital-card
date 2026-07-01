/**
 * 设置 Screen — 账户 / 外观 / 隐私 / 支持
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  Switch,
} from 'react-native';
import { useTheme } from '../theme/theme-context';

interface SettingItemProps {
  icon: string;
  label: string;
  hasToggle?: boolean;
  toggleValue?: boolean;
  onToggle?: (val: boolean) => void;
  onPress?: () => void;
  colors: any;
  r: any;
}

const SettingItem: React.FC<SettingItemProps> = ({
  icon,
  label,
  hasToggle,
  toggleValue,
  onToggle,
  onPress,
  colors,
  r,
}) => (
  <View style={[styles.settingItem, { borderBottomColor: colors.glassBorder }]}>
    <View style={[styles.settingIcon, { backgroundColor: colors.primaryGlow, borderRadius: r.sm }]}>
      <Text style={{ fontSize: 16 }}>{icon}</Text>
    </View>
    <Text style={[styles.settingLabel, { color: colors.textPrimary }]}>{label}</Text>
    {hasToggle ? (
      <Switch
        value={toggleValue}
        onValueChange={onToggle}
        trackColor={{ false: colors.glassBorder, true: colors.primary }}
        thumbColor="#fff"
      />
    ) : (
      <Pressable onPress={onPress}>
        <Text style={{ color: colors.textTertiary, fontSize: 18 }}>›</Text>
      </Pressable>
    )}
  </View>
);

export default function SettingsScreen() {
  const { colors, spacing: s, radius: r, isDark, toggleTheme, themeMode, setThemeMode } = useTheme();

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: colors.background }]}
      contentContainerStyle={styles.content}
    >
      {/* 用户信息头部 */}
      <View style={styles.profileHeader}>
        <View style={[styles.avatar, { backgroundColor: colors.primary }]}>
          <Text style={styles.avatarInitial}>海</Text>
        </View>
        <View style={styles.profileInfo}>
          <Text style={[styles.name, { color: colors.textPrimary }]}>海容 · 向</Text>
          <Text style={[styles.bio, { color: colors.textSecondary }]}>AI 数字名片创始人</Text>
          <View style={[styles.proBadge, { backgroundColor: colors.primaryGlow }]}>
            <Text style={[styles.proBadgeText, { color: colors.primary }]}>PRO 会员 · 至 2027/12</Text>
          </View>
        </View>
      </View>

      {/* 快捷统计 */}
      <View style={[styles.statsRow, { borderBottomColor: colors.glassBorder }]}>
        <View style={{ flex: 1, alignItems: 'center' }}>
          <Text style={[styles.statValue, { color: colors.textPrimary }]}>1</Text>
          <Text style={[styles.statLabel, { color: colors.textTertiary }]}>名片</Text>
        </View>
        <View style={[styles.statsDivider, { backgroundColor: colors.glassBorder }]} />
        <View style={{ flex: 1, alignItems: 'center' }}>
          <Text style={[styles.statValue, { color: colors.textPrimary }]}>12</Text>
          <Text style={[styles.statLabel, { color: colors.textTertiary }]}>AI 分身</Text>
        </View>
        <View style={[styles.statsDivider, { backgroundColor: colors.glassBorder }]} />
        <View style={{ flex: 1, alignItems: 'center' }}>
          <Text style={[styles.statValue, { color: colors.textPrimary }]}>2,384</Text>
          <Text style={[styles.statLabel, { color: colors.textTertiary }]}>访客</Text>
        </View>
        <View style={[styles.statsDivider, { backgroundColor: colors.glassBorder }]} />
        <View style={{ flex: 1, alignItems: 'center' }}>
          <Text style={[styles.statValue, { color: colors.textPrimary }]}>147</Text>
          <Text style={[styles.statLabel, { color: colors.textTertiary }]}>解锁</Text>
        </View>
      </View>

      {/* 外观设置 */}
      <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>外观设置</Text>
      <View style={[styles.settingsCard, { backgroundColor: colors.glassBg, borderRadius: r.md }]}>
        <View style={styles.themeRow}>
          <View style={styles.themeInfo}>
            <Text style={{ fontSize: 20, marginRight: 12 }}>🎨</Text>
            <View>
              <Text style={[styles.themeTitle, { color: colors.textPrimary }]}>主题模式</Text>
              <Text style={[styles.themeSub, { color: colors.textTertiary }]}>
                当前：{themeMode === 'system' ? '跟随系统' : themeMode === 'dark' ? '深色' : '浅色'}
              </Text>
            </View>
          </View>
        </View>
        <View style={[styles.themeOptions, { borderTopColor: colors.glassBorder }]}>
          {(['system', 'dark', 'light'] as const).map((m) => (
            <Pressable
              key={m}
              onPress={() => setThemeMode(m)}
              style={[
                styles.themeOption,
                {
                  backgroundColor: themeMode === m ? colors.primaryGlow : 'transparent',
                  borderColor: themeMode === m ? colors.primary : colors.glassBorder,
                  borderRadius: r.sm,
                },
              ]}
            >
              <Text style={{ fontSize: 16 }}>
                {m === 'system' ? '📱' : m === 'dark' ? '🌙' : '☀️'}
              </Text>
              <Text
                style={{
                  color: themeMode === m ? colors.primary : colors.textSecondary,
                  fontSize: 12,
                  fontWeight: themeMode === m ? '700' : '500',
                }}
              >
                {m === 'system' ? '跟随系统' : m === 'dark' ? '深色' : '浅色'}
              </Text>
            </Pressable>
          ))}
        </View>
        <Pressable
          onPress={toggleTheme}
          style={[styles.quickToggle, { borderTopColor: colors.glassBorder }]}
        >
          <Text style={{ color: colors.textPrimary, fontSize: 14, fontWeight: '600' }}>
            快速切换
          </Text>
          <Text style={{ fontSize: 18 }}>{isDark ? '☀️' : '🌙'}</Text>
        </Pressable>
      </View>

      {/* 账户与隐私 */}
      <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>账户与隐私</Text>
      <View style={[styles.settingsCard, { backgroundColor: colors.glassBg, borderRadius: r.md }]}>
        <SettingItem icon="🔔" label="推送通知" hasToggle toggleValue={true} colors={colors} r={r} />
        <SettingItem icon="🛡️" label="双因素认证" hasToggle toggleValue={true} colors={colors} r={r} />
        <SettingItem icon="🔒" label="隐私设置" colors={colors} r={r} />
        <SettingItem icon="☁️" label="数据备份与同步" colors={colors} r={r} />
      </View>

      {/* 支持与帮助 */}
      <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>支持与帮助</Text>
      <View style={[styles.settingsCard, { backgroundColor: colors.glassBg, borderRadius: r.md }]}>
        <SettingItem icon="❓" label="帮助中心" colors={colors} r={r} />
        <SettingItem icon="💬" label="联系客服" colors={colors} r={r} />
        <SettingItem icon="📄" label="条款与协议" colors={colors} r={r} />
        <SettingItem icon="ℹ️" label="关于 · v1.0.0" colors={colors} r={r} />
      </View>

      {/* 退出登录 */}
      <Pressable
        style={[styles.logoutBtn, { borderColor: colors.danger }]}
        onPress={() => {}}
      >
        <Text style={[styles.logoutText, { color: colors.danger }]}>退出登录</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16, paddingBottom: 32 },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    paddingHorizontal: 4,
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInitial: { color: '#fff', fontSize: 22, fontWeight: '800' },
  profileInfo: { flex: 1, marginLeft: 14 },
  name: { fontSize: 20, fontWeight: '800' },
  bio: { fontSize: 13, marginTop: 4 },
  proBadge: { alignSelf: 'flex-start', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 10, marginTop: 8 },
  proBadgeText: { fontSize: 11, fontWeight: '700' },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 8,
    marginBottom: 24,
    borderBottomWidth: 0.5,
  },
  statValue: { fontSize: 20, fontWeight: '800' },
  statLabel: { fontSize: 11, marginTop: 4 },
  statsDivider: { width: 1, height: 24, marginHorizontal: 4 },
  sectionTitle: { fontSize: 15, fontWeight: '700', marginBottom: 12, paddingHorizontal: 4 },
  settingsCard: { marginBottom: 24, overflow: 'hidden' },
  themeRow: { padding: 16 },
  themeInfo: { flexDirection: 'row', alignItems: 'center' },
  themeTitle: { fontSize: 15, fontWeight: '700' },
  themeSub: { fontSize: 12, marginTop: 2 },
  themeOptions: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingBottom: 16,
    borderTopWidth: 1,
    gap: 10,
  },
  themeOption: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderWidth: 1,
    gap: 6,
  },
  quickToggle: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderTopWidth: 1,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 0.5,
  },
  settingIcon: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  settingLabel: { flex: 1, fontSize: 14, fontWeight: '500' },
  logoutBtn: {
    borderWidth: 1,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 20,
  },
  logoutText: { fontSize: 15, fontWeight: '700' },
});
