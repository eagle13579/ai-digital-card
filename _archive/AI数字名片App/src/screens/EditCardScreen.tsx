/**
 * 名片编辑 Screen — 编辑名片信息表单
 * 导航: CardDetailScreen -> EditCardScreen (params: { cardId })
 *
 * 功能:
 *  - 头像选择 (头像区域可点击)
 *  - 姓名/公司/职位/电话/邮箱/网站 文本输入
 *  - 标签管理 (添加/删除标签)
 *  - 保存/取消操作
 *  - API: PUT /mobile/card/:id
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  TextInput,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useTheme } from '../theme/theme-context';
import { api } from '../api/client';

// ── Types ───────────────────────────────────────────────────────────────────

interface CardFormData {
  name: string;
  title: string;
  company: string;
  email: string;
  phone: string;
  website: string;
  tags: string[];
}

// ── EditCardScreen ──────────────────────────────────────────────────────────

export default function EditCardScreen({ route, navigation }: any) {
  const { colors, spacing: s, radius: r, isDark } = useTheme();
  const cardId = route?.params?.cardId ?? '1';

  // ── Form State ──
  const [form, setForm] = useState<CardFormData>({
    name: '海容 · 向',
    title: 'AI 数字名片创始人',
    company: '链客宝科技有限公司',
    email: 'hirongxiang@ncard.ai',
    phone: '+86 138-0000-8888',
    website: 'https://ai-digital-card.com',
    tags: ['AI', '数字名片', 'SaaS', 'Web3', '信任网络'],
  });

  const [newTag, setNewTag] = useState('');
  const [saving, setSaving] = useState(false);

  // ── Form Helpers ──

  const updateField = (field: keyof CardFormData, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const addTag = () => {
    const tag = newTag.trim();
    if (!tag) return;
    if (form.tags.includes(tag)) {
      Alert.alert('标签已存在', `"${tag}" 已经在标签列表中`);
      return;
    }
    if (form.tags.length >= 10) {
      Alert.alert('标签上限', '最多添加 10 个标签');
      return;
    }
    setForm((prev) => ({ ...prev, tags: [...prev.tags, tag] }));
    setNewTag('');
  };

  const removeTag = (tag: string) => {
    setForm((prev) => ({
      ...prev,
      tags: prev.tags.filter((t) => t !== tag),
    }));
  };

  // ── Validation ──

  const validate = (): boolean => {
    if (!form.name.trim()) {
      Alert.alert('请填写姓名');
      return false;
    }
    if (!form.email.trim() || !form.email.includes('@')) {
      Alert.alert('请填写有效的邮箱地址');
      return false;
    }
    if (!form.phone.trim()) {
      Alert.alert('请填写电话');
      return false;
    }
    return true;
  };

  // ── Save ──

  const handleSave = useCallback(async () => {
    if (!validate()) return;

    setSaving(true);
    try {
      await api.put(`/mobile/card/${cardId}`, form);
      Alert.alert('保存成功', '名片信息已更新', [
        { text: '返回', onPress: () => navigation.goBack() },
      ]);
    } catch (err: any) {
      console.warn('[EditCardScreen] Save failed:', err.message);
      Alert.alert('保存失败', '网络错误，请在设置中检查网络连接后重试');
    } finally {
      setSaving(false);
    }
  }, [form, cardId, navigation]);

  const handleCancel = () => {
    Alert.alert('放弃编辑？', '未保存的修改将丢失', [
      { text: '继续编辑', style: 'cancel' },
      { text: '放弃', style: 'destructive', onPress: () => navigation.goBack() },
    ]);
  };

  // ── Render ──

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: colors.background }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      {/* 顶部操作栏 */}
      <View style={[styles.topBar, { borderBottomColor: colors.glassBorder }]}>
        <Pressable onPress={handleCancel} style={styles.topBarBtn}>
          <Text style={[styles.cancelText, { color: colors.textSecondary }]}>取消</Text>
        </Pressable>
        <Text style={[styles.topBarTitle, { color: colors.textPrimary }]}>编辑名片</Text>
        <Pressable
          onPress={handleSave}
          disabled={saving}
          style={[
            styles.saveBtn,
            { backgroundColor: saving ? colors.textTertiary : colors.primary, borderRadius: r.sm },
          ]}
        >
          <Text style={styles.saveBtnText}>{saving ? '保存中...' : '保存'}</Text>
        </Pressable>
      </View>

      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        {/* ── 头像区域 ── */}
        <View style={styles.avatarSection}>
          <Pressable
            style={[styles.avatarCircle, { backgroundColor: colors.primary }]}
            onPress={() => Alert.alert('更换头像', '头像上传功能即将上线')}
          >
            <Text style={styles.avatarText}>{form.name[0] || '?'}</Text>
          </Pressable>
          <Text style={[styles.avatarHint, { color: colors.textTertiary }]}>
            点击更换头像
          </Text>
        </View>

        {/* ── 基本信息 ── */}
        <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>基本信息</Text>
        <View style={[styles.formCard, { backgroundColor: colors.glassBg, borderRadius: r.md }]}>
          <FormField
            label="姓名"
            value={form.name}
            onChangeText={(v) => updateField('name', v)}
            placeholder="请输入您的姓名"
            colors={colors}
            r={r}
          />
          <FormDivider colors={colors} />
          <FormField
            label="职位"
            value={form.title}
            onChangeText={(v) => updateField('title', v)}
            placeholder="如: 创始人 / CEO"
            colors={colors}
            r={r}
          />
          <FormDivider colors={colors} />
          <FormField
            label="公司"
            value={form.company}
            onChangeText={(v) => updateField('company', v)}
            placeholder="公司/机构名称"
            colors={colors}
            r={r}
          />
        </View>

        {/* ── 联系方式 ── */}
        <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>联系方式</Text>
        <View style={[styles.formCard, { backgroundColor: colors.glassBg, borderRadius: r.md }]}>
          <FormField
            label="电话"
            value={form.phone}
            onChangeText={(v) => updateField('phone', v)}
            placeholder="+86 138-0000-8888"
            keyboardType="phone-pad"
            colors={colors}
            r={r}
          />
          <FormDivider colors={colors} />
          <FormField
            label="邮箱"
            value={form.email}
            onChangeText={(v) => updateField('email', v)}
            placeholder="your@email.com"
            keyboardType="email-address"
            autoCapitalize="none"
            colors={colors}
            r={r}
          />
          <FormDivider colors={colors} />
          <FormField
            label="网站"
            value={form.website}
            onChangeText={(v) => updateField('website', v)}
            placeholder="https://your-site.com"
            keyboardType="url"
            autoCapitalize="none"
            colors={colors}
            r={r}
          />
        </View>

        {/* ── 标签 ── */}
        <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>标签</Text>
        <View style={[styles.formCard, { backgroundColor: colors.glassBg, borderRadius: r.md }]}>
          {/* 已添加的标签 */}
          <View style={styles.tagsWrap}>
            {form.tags.map((tag) => (
              <View key={tag} style={[styles.tagChip, { backgroundColor: colors.primaryGlow }]}>
                <Text style={[styles.tagText, { color: colors.primary }]}>{tag}</Text>
                <Pressable onPress={() => removeTag(tag)} style={styles.tagRemove}>
                  <Text style={[styles.tagRemoveText, { color: colors.danger }]}>✕</Text>
                </Pressable>
              </View>
            ))}
          </View>

          {/* 添加新标签 */}
          <View style={[styles.addTagRow, { borderTopColor: colors.glassBorder }]}>
            <TextInput
              style={[styles.tagInput, { color: colors.textPrimary }]}
              placeholder="输入新标签后点击添加"
              placeholderTextColor={colors.textTertiary}
              value={newTag}
              onChangeText={setNewTag}
              onSubmitEditing={addTag}
              returnKeyType="done"
            />
            <Pressable
              onPress={addTag}
              style={[styles.addTagBtn, { backgroundColor: colors.primary, borderRadius: r.sm }]}
            >
              <Text style={styles.addTagBtnText}>添加</Text>
            </Pressable>
          </View>
          <Text style={[styles.tagHint, { color: colors.textTertiary }]}>
            最多 10 个标签，回车或点击"添加"
          </Text>
        </View>

        {/* ── 底部间距 ── */}
        <View style={{ height: 48 }} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// ── Subcomponents ──────────────────────────────────────────────────────────

interface FormFieldProps {
  label: string;
  value: string;
  onChangeText: (text: string) => void;
  placeholder: string;
  keyboardType?: 'default' | 'email-address' | 'phone-pad' | 'url';
  autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters';
  colors: any;
  r: any;
}

function FormField({
  label,
  value,
  onChangeText,
  placeholder,
  keyboardType = 'default',
  autoCapitalize = 'sentences',
  colors,
  r,
}: FormFieldProps) {
  return (
    <View style={styles.fieldRow}>
      <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>{label}</Text>
      <TextInput
        style={[styles.fieldInput, { color: colors.textPrimary }]}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={colors.textTertiary}
        keyboardType={keyboardType}
        autoCapitalize={autoCapitalize}
      />
    </View>
  );
}

function FormDivider({ colors }: { colors: any }) {
  return <View style={[styles.formDivider, { backgroundColor: colors.glassBorder }]} />;
}

// ── Styles ──────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  // Top Bar
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    paddingTop: Platform.OS === 'ios' ? 52 : 12,
  },
  topBarBtn: { paddingVertical: 6, paddingHorizontal: 4 },
  cancelText: { fontSize: 16, fontWeight: '500' },
  topBarTitle: { fontSize: 17, fontWeight: '700' },
  saveBtn: { paddingHorizontal: 16, paddingVertical: 8 },
  saveBtnText: { color: '#fff', fontSize: 14, fontWeight: '700' },

  // Content
  content: { padding: 16, paddingTop: 8 },

  // Avatar
  avatarSection: { alignItems: 'center', marginBottom: 24, marginTop: 12 },
  avatarCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { color: '#fff', fontSize: 30, fontWeight: '800' },
  avatarHint: { fontSize: 12, marginTop: 8 },

  // Section
  sectionTitle: { fontSize: 15, fontWeight: '700', marginBottom: 10, paddingHorizontal: 4 },

  // Form Card
  formCard: { marginBottom: 24, overflow: 'hidden' },
  fieldRow: {
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  fieldLabel: { fontSize: 12, fontWeight: '600', marginBottom: 6 },
  fieldInput: {
    fontSize: 16,
    paddingVertical: 4,
    paddingHorizontal: 0,
  },
  formDivider: { height: 1, marginHorizontal: 16 },

  // Tags
  tagsWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    padding: 16,
    paddingBottom: 8,
  },
  tagChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingLeft: 10,
    paddingRight: 6,
    paddingVertical: 6,
    borderRadius: 8,
  },
  tagText: { fontSize: 12, fontWeight: '600', marginRight: 4 },
  tagRemove: {
    width: 20,
    height: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tagRemoveText: { fontSize: 12, fontWeight: '700' },
  addTagRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    gap: 8,
  },
  tagInput: {
    flex: 1,
    fontSize: 15,
    paddingVertical: 8,
    paddingHorizontal: 0,
  },
  addTagBtn: {
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  addTagBtnText: { color: '#fff', fontSize: 13, fontWeight: '700' },
  tagHint: { fontSize: 11, paddingHorizontal: 16, paddingBottom: 12 },
});
