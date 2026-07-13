import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Users, Settings, UserPlus, Shield, Trash2,
  Loader2, Check, X, Mail, Phone, Clock, Building2,
  Edit3, Copy, AlertCircle, LogOut, User, Crown,
  MoreVertical, Link, Plus,
} from 'lucide-react';
import { api } from '../api/client';
import { useT } from '../i18n';

// ─── 类型定义 ─────────────────────────────────────

interface TeamDetail {
  id: number;
  name: string;
  slug: string;
  description: string;
  logo: string;
  website: string;
  industry: string;
  size: string;
  owner_id: number;
  max_members: number;
  member_count: number;
  invite_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface Member {
  id: number;
  user_id: number;
  name: string;
  avatar: string;
  phone: string;
  company: string;
  title: string;
  role: string;
  title_in_team: string;
  joined_at: string | null;
  invited_by: number | null;
}

interface Invite {
  id: number;
  invitee_email: string;
  invitee_phone: string;
  invitee_id: number | null;
  role: string;
  status: string;
  token: string;
  message: string;
  expires_at: string;
  created_at: string;
}

interface ApprovalRequest {
  id: number;
  user_id: number;
  applicant_name: string;
  applicant_avatar: string;
  action: string;
  reason: string;
  status: string;
  reject_reason: string;
  created_at: string;
  updated_at: string;
}

// ─── 工具 ─────────────────────────────────────────

const ROLE_LABELS: Record<string, string> = {
  owner: '所有者',
  admin: '管理员',
  member: '成员',
  viewer: '查看者',
};

const ROLE_COLORS: Record<string, string> = {
  owner: 'bg-yellow-100 text-yellow-700',
  admin: 'bg-blue-100 text-blue-700',
  member: 'bg-gray-100 text-gray-700',
  viewer: 'bg-green-100 text-green-700',
};

const STATUS_LABELS: Record<string, string> = {
  pending: '待处理',
  accepted: '已接受',
  declined: '已拒绝',
  expired: '已过期',
};

function formatDate(iso: string | null) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
}

// ─── 子组件 ───────────────────────────────────────

function InviteMemberModal({ teamId, onClose }: { teamId: number; onClose: () => void }) {
  const t = useT();
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [role, setRole] = useState('member');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async () => {
    if (!email && !phone) { setError(t('settings.inviteEmailOrPhone')); return; }
    setLoading(true);
    setError('');
    setSuccess('');
    const res = await api.post(`/api/teams/${teamId}/invites`, {
      email, phone, role, message,
    });
    setLoading(false);
    if (res.code === 201 || res.code === 200) {
      setSuccess(t('settings.inviteSent'));
      setTimeout(onClose, 1500);
    } else {
      setError(res.message || t('settings.inviteSendFailed'));
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-surface rounded-2xl p-6 w-full max-w-md shadow-modal" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold flex items-center gap-2"><UserPlus className="w-5 h-5" />邀请成员</h2>
          <button onClick={onClose} className="p-1 hover:bg-neutral-bg rounded-lg" aria-label={t('button.close')}><X className="w-5 h-5" /></button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">邮箱</label>
            <input
              value={email} onChange={e => setEmail(e.target.value)}
              className="w-full px-3 py-2 bg-neutral-bg border border-border rounded-lg text-sm focus:outline-none focus:border-primary"
              placeholder="email@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">手机号</label>
            <input
              value={phone} onChange={e => setPhone(e.target.value)}
              className="w-full px-3 py-2 bg-neutral-bg border border-border rounded-lg text-sm focus:outline-none focus:border-primary"
              placeholder="13800138000"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">角色</label>
            <select
              value={role} onChange={e => setRole(e.target.value)}
              className="w-full px-3 py-2 bg-neutral-bg border border-border rounded-lg text-sm focus:outline-none focus:border-primary"
            >
              <option value="member">成员</option>
              <option value="admin">管理员</option>
              <option value="viewer">查看者</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">邀请附言（可选）</label>
            <textarea
              value={message} onChange={e => setMessage(e.target.value)}
              className="w-full px-3 py-2 bg-neutral-bg border border-border rounded-lg text-sm focus:outline-none focus:border-primary resize-none"
              rows={2} placeholder="欢迎加入我们的团队！"
            />
          </div>
          {error && <p className="text-sm text-red-500 flex items-center gap-1"><AlertCircle className="w-4 h-4" />{error}</p>}
          {success && <p className="text-sm text-green-600 flex items-center gap-1"><Check className="w-4 h-4" />{success}</p>}
          <button
            onClick={handleSubmit} disabled={loading}
            className="w-full py-2.5 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
            发送邀请
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── 主页面 ───────────────────────────────────────

export default function TeamSettings() {
  const { teamId } = useParams<{ teamId: string }>();
  const navigate = useNavigate();
  const t = useT();
  const tid = parseInt(teamId || '0');

  const [team, setTeam] = useState<TeamDetail | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'members' | 'invites' | 'approvals' | 'settings'>('members');
  const [showInvite, setShowInvite] = useState(false);
  const [editingName, setEditingName] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editWebsite, setEditWebsite] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState('');
  const [rejectModal, setRejectModal] = useState<{ id: number } | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [rejecting, setRejecting] = useState(false);

  const loadData = useCallback(async () => {
    if (!tid) return;
    setLoading(true);
    const [teamRes, membersRes, invitesRes, approvalsRes] = await Promise.all([
      api.get<TeamDetail>(`/api/teams/${tid}`),
      api.get<Member[]>(`/api/teams/${tid}/members`),
      api.get<Invite[]>(`/api/teams/${tid}/invites`),
      api.get<ApprovalRequest[]>(`/api/teams/${tid}/approval-requests`),
    ]);
    if (teamRes.data) {
      setTeam(teamRes.data);
      setEditName(teamRes.data.name);
      setEditDesc(teamRes.data.description);
      setEditWebsite(teamRes.data.website);
    }
    if (membersRes.data) setMembers(membersRes.data);
    if (invitesRes.data) setInvites(invitesRes.data);
    if (approvalsRes.data) setApprovals(approvalsRes.data);
    setLoading(false);
  }, [tid]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleUpdateTeam = async () => {
    setSaving(true);
    setSaveMsg('');
    const res = await api.put(`/api/teams/${tid}`, {
      name: editName, description: editDesc, website: editWebsite,
    });
    setSaving(false);
    if (res.code === 200) {
      setSaveMsg('保存成功');
      if (res.data) setTeam({ ...team!, ...res.data });
    } else {
      setSaveMsg(res.message || '保存失败');
    }
  };

  const handleRemoveMember = async (userId: number) => {
    if (!confirm('确定移除该成员？')) return;
    const res = await api.request(`/api/teams/${tid}/members/${userId}`, { method: 'DELETE' });
    if (res.code === 204 || res.code === 200) {
      await loadData();
    } else {
      alert(res.message || '操作失败');
    }
  };

  const handleRoleChange = async (userId: number, role: string) => {
    const res = await api.put(`/api/teams/${tid}/members/${userId}/role`, { role });
    if (res.code === 200) {
      await loadData();
    } else {
      alert(res.message || '角色更新失败');
    }
  };

  const handleCancelInvite = async (inviteId: number) => {
    const res = await api.request(`/api/teams/${tid}/invites/${inviteId}`, { method: 'DELETE' });
    if (res.code === 204 || res.code === 200) {
      await loadData();
    } else {
      alert(res.message || '取消失败');
    }
  };

  const handleApprove = async (requestId: number) => {
    const res = await api.put(`/api/teams/${tid}/approval-requests/${requestId}`, { status: 'approved' });
    if (res.code === 200) {
      await loadData();
    } else {
      alert(res.message || '审批通过失败');
    }
  };

  const handleRejectSubmit = async () => {
    if (!rejectModal) return;
    if (!rejectReason.trim()) { alert('请填写拒绝原因'); return; }
    setRejecting(true);
    const res = await api.put(`/api/teams/${tid}/approval-requests/${rejectModal.id}`, {
      status: 'rejected', reject_reason: rejectReason.trim(),
    });
    setRejecting(false);
    if (res.code === 200) {
      setRejectModal(null);
      setRejectReason('');
      await loadData();
    } else {
      alert(res.message || '审批拒绝失败');
    }
  };

  const handleDeleteTeam = async () => {
    if (!confirm('确定删除团队？此操作不可撤销。')) return;
    const res = await api.request(`/api/teams/${tid}`, { method: 'DELETE' });
    if (res.code === 204 || res.code === 200) {
      navigate('/teams');
    } else {
      alert(res.message || '删除失败');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-bg flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!team) {
    return (
      <div className="min-h-screen bg-neutral-bg flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 mx-auto text-on-surface/30 mb-3" />
          <p className="text-on-surface/60">团队不存在或已删除</p>
          <button onClick={() => navigate('/teams')} className="mt-4 text-primary text-sm">返回团队列表</button>
        </div>
      </div>
    );
  }

  const isAdmin = team.owner_id === 1; // simplified: current user check

  return (
    <div className="min-h-screen bg-neutral-bg">
      {/* Header */}
      <header className="bg-surface border-b border-border px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/teams')} className="p-2 hover:bg-neutral-bg rounded-xl" aria-label={t('button.back')}>
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-lg font-semibold">{team.name}</h1>
              <p className="text-xs text-on-surface/50">{team.member_count} 成员 · {team.invite_count} 待处理邀请</p>
            </div>
          </div>
          <button
            onClick={() => setShowInvite(true)}
            className="flex items-center gap-1.5 px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90"
          >
            <UserPlus className="w-4 h-4" /> 邀请成员
          </button>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b border-border bg-surface">
        <div className="max-w-4xl mx-auto flex">
          {([
            { key: 'members', label: '成员', icon: Users },
            { key: 'invites', label: '邀请', icon: Mail },
            { key: 'approvals', label: '审批', icon: Shield },
            { key: 'settings', label: '设置', icon: Settings },
          ] as const).map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-primary text-primary'
                  : 'border-transparent text-on-surface/50 hover:text-on-surface'
              }`}
            >
              <tab.icon className="w-4 h-4" /> {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        {activeTab === 'members' && (
          <div className="space-y-2">
            {members.map(m => (
              <div key={m.id} className="bg-surface rounded-xl p-4 border border-border flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center overflow-hidden">
                    {m.avatar ? (
                      <img src={m.avatar} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <User className="w-5 h-5 text-primary" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{m.name}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${ROLE_COLORS[m.role] || 'bg-gray-100'}`}>
                        {ROLE_LABELS[m.role] || m.role}
                      </span>
                    </div>
                    <p className="text-xs text-on-surface/50">{m.title_in_team || m.title || m.company || m.phone}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {m.role !== 'owner' && (
                    <>
                      <select
                        value={m.role}
                        onChange={e => handleRoleChange(m.user_id, e.target.value)}
                        className="text-xs px-2 py-1 border border-border rounded-lg bg-neutral-bg"
                      >
                        <option value="member">成员</option>
                        <option value="admin">管理员</option>
                        <option value="viewer">查看者</option>
                      </select>
                      <button
                        onClick={() => handleRemoveMember(m.user_id)}
                        className="p-1.5 hover:bg-red-50 rounded-lg text-red-500"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
            {members.length === 0 && (
              <div className="text-center py-10 text-on-surface/50">
                <Users className="w-10 h-10 mx-auto mb-2 opacity-40" />
                <p>暂无成员</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'invites' && (
          <div className="space-y-2">
            {invites.map(inv => (
              <div key={inv.id} className="bg-surface rounded-xl p-4 border border-border flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Mail className="w-8 h-8 p-1.5 rounded-lg bg-primary/10 text-primary" />
                  <div>
                    <p className="text-sm font-medium">{inv.invitee_email || inv.invitee_phone || '未知'}</p>
                    <div className="flex items-center gap-2 text-xs text-on-surface/50 mt-1">
                      <span className={`px-1.5 py-0.5 rounded text-xs ${STATUS_LABELS[inv.status] ? 'bg-gray-100' : ''}`}>
                        {STATUS_LABELS[inv.status] || inv.status}
                      </span>
                      <span>{ROLE_LABELS[inv.role] || inv.role}</span>
                      <span>{formatDate(inv.created_at)}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {inv.status === 'pending' && (
                    <>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(`${window.location.origin}/invite/${inv.token}`);
                        }}
                        className="p-1.5 hover:bg-neutral-bg rounded-lg text-on-surface/50"
                        title="复制邀请链接"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleCancelInvite(inv.id)}
                        className="p-1.5 hover:bg-red-50 rounded-lg text-red-500"
                        title="取消邀请"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
            {invites.length === 0 && (
              <div className="text-center py-10 text-on-surface/50">
                <Mail className="w-10 h-10 mx-auto mb-2 opacity-40" />
                <p>暂无邀请记录</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'approvals' && (
          <div className="space-y-2">
            {approvals.filter(a => a.status === 'pending').map(req => (
              <div key={req.id} className="bg-surface rounded-xl p-4 border border-border">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center overflow-hidden">
                      {req.applicant_avatar ? (
                        <img src={req.applicant_avatar} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <User className="w-5 h-5 text-primary" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{req.applicant_name}</p>
                      <p className="text-xs text-on-surface/50">{formatDate(req.created_at)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleApprove(req.id)}
                      className="flex items-center gap-1 px-3 py-1.5 bg-green-500 text-white text-xs rounded-lg hover:bg-green-600"
                    >
                      <Check className="w-3.5 h-3.5" /> 通过
                    </button>
                    <button
                      onClick={() => setRejectModal({ id: req.id })}
                      className="flex items-center gap-1 px-3 py-1.5 bg-red-500 text-white text-xs rounded-lg hover:bg-red-600"
                    >
                      <X className="w-3.5 h-3.5" /> 拒绝
                    </button>
                  </div>
                </div>
                <div className="text-xs text-on-surface/60 space-y-1">
                  <p><span className="font-medium">动作：</span>{req.action}</p>
                  {req.reason && <p><span className="font-medium">原因：</span>{req.reason}</p>}
                </div>
              </div>
            ))}
            {approvals.filter(a => a.status === 'pending').length === 0 && (
              <div className="text-center py-10 text-on-surface/50">
                <Shield className="w-10 h-10 mx-auto mb-2 opacity-40" />
                <p>暂无待审批请求</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="space-y-6 max-w-lg">
            {/* 基本信息 */}
            <div className="bg-surface rounded-xl p-5 border border-border">
              <h3 className="text-sm font-semibold mb-4 flex items-center gap-2"><Settings className="w-4 h-4" /> 基本设置</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium mb-1">团队名称</label>
                  <input
                    value={editName} onChange={e => setEditName(e.target.value)}
                    className="w-full px-3 py-2 bg-neutral-bg border border-border rounded-lg text-sm focus:outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">简介</label>
                  <textarea
                    value={editDesc} onChange={e => setEditDesc(e.target.value)}
                    className="w-full px-3 py-2 bg-neutral-bg border border-border rounded-lg text-sm focus:outline-none focus:border-primary resize-none"
                    rows={2}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1">网站</label>
                  <input
                    value={editWebsite} onChange={e => setEditWebsite(e.target.value)}
                    className="w-full px-3 py-2 bg-neutral-bg border border-border rounded-lg text-sm focus:outline-none focus:border-primary"
                    placeholder="https://"
                  />
                </div>
                <button
                  onClick={handleUpdateTeam} disabled={saving}
                  className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                  保存设置
                </button>
                {saveMsg && <p className="text-xs text-green-600">{saveMsg}</p>}
              </div>
            </div>

            {/* 危险操作 */}
            <div className="bg-surface rounded-xl p-5 border border-red-200">
              <h3 className="text-sm font-semibold mb-2 text-red-600 flex items-center gap-2"><AlertCircle className="w-4 h-4" /> 危险区域</h3>
              <p className="text-xs text-on-surface/50 mb-4">删除团队后所有数据和成员关系将被移除，此操作不可撤销。</p>
              <button
                onClick={handleDeleteTeam}
                className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" /> 删除团队
              </button>
            </div>
          </div>
        )}
      </main>

      {showInvite && <InviteMemberModal teamId={tid} onClose={() => { setShowInvite(false); loadData(); }} />}

      {rejectModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => { setRejectModal(null); setRejectReason(''); }}>
          <div className="bg-surface rounded-2xl p-6 w-full max-w-md shadow-modal" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold flex items-center gap-2"><X className="w-5 h-5" />拒绝审批</h2>
              <button onClick={() => { setRejectModal(null); setRejectReason(''); }} className="p-1 hover:bg-neutral-bg rounded-lg" aria-label={t('button.close')}><X className="w-5 h-5" /></button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">拒绝原因 <span className="text-red-500">*</span></label>
                <textarea
                  value={rejectReason}
                  onChange={e => setRejectReason(e.target.value)}
                  className="w-full px-3 py-2 bg-neutral-bg border border-border rounded-lg text-sm focus:outline-none focus:border-primary resize-none"
                  rows={3}
                  placeholder="请输入拒绝原因..."
                />
              </div>
              <button
                onClick={handleRejectSubmit}
                disabled={rejecting || !rejectReason.trim()}
                className="w-full py-2.5 bg-red-500 text-white rounded-lg font-medium hover:bg-red-600 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {rejecting ? <Loader2 className="w-4 h-4 animate-spin" /> : <X className="w-4 h-4" />}
                确认拒绝
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
