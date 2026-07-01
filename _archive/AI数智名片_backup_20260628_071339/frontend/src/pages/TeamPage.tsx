import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users, Settings, Plus, UserPlus, LogOut, Shield,
  User, Mail, Phone, Clock, ChevronRight, X,
  Loader2, Check, AlertCircle, Building2, Link,
  Trash2, Edit3, MoreVertical, Upload, FileText,
  Download, Table2,
} from 'lucide-react';
import { api } from '../api/client';
import { PageSkeleton } from '../components/LoadingSkeleton';
import ErrorBoundary from '../components/ErrorBoundary';
import { useT } from '../i18n';

// ─── 类型定义 ─────────────────────────────────────

interface Team {
  id: number;
  name: string;
  slug: string;
  description: string;
  logo: string;
  owner_id: number;
  max_members: number;
  member_count: number;
  invite_count: number;
  is_active: boolean;
  created_at: string;
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
}

interface Invite {
  id: number;
  invitee_email: string;
  invitee_phone: string;
  role: string;
  status: string;
  token: string;
  message: string;
  created_at: string;
  expires_at: string;
}

// ─── 子组件 ───────────────────────────────────────

function TeamCard({ team, onClick }: { team: Team; onClick: () => void }) {
  const t = useT();
  const roleLabel = (id: number) => id === 1 ? t('team.owner') : t('team.member');
  return (
    <div
      className="bg-surface rounded-xl p-5 border border-border hover:border-primary/50 cursor-pointer transition-all duration-200 shadow-sm hover:shadow-md"
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
            {team.logo ? (
              <img src={team.logo} alt="" className="w-10 h-10 rounded-lg object-cover" />
            ) : (
              <Building2 className="w-6 h-6 text-primary" />
            )}
          </div>
          <div>
            <h3 className="font-semibold text-base text-on-surface">{team.name}</h3>
            <p className="text-sm text-on-surface/60">{team.description || team.slug}</p>
          </div>
        </div>
        <ChevronRight className="w-5 h-5 text-on-surface/30" />
      </div>
      <div className="flex items-center gap-4 mt-4 text-sm text-on-surface/50">
        <span className="flex items-center gap-1"><Users className="w-4 h-4" /> {team.member_count}/{team.max_members}</span>
        <span className="flex items-center gap-1"><Clock className="w-4 h-4" /> {t('team.createdAt')} {new Date(team.created_at).toLocaleDateString()}</span>
      </div>
    </div>
  );
}

function CreateTeamModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const t = useT();
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [description, setDescription] = useState('');
  const [industry, setIndustry] = useState('');
  const [size, setSize] = useState('1-10');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const generateSlug = (n: string) => n.toLowerCase().replace(/[^a-z0-9\-]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');

  const handleNameChange = (v: string) => {
    setName(v);
    if (!slug || slug === generateSlug(name)) {
      setSlug(generateSlug(v));
    }
  };

  const handleSubmit = async () => {
    if (!name || !slug) { setError(t('team.nameSlugRequired')); return; }
    setLoading(true);
    setError('');
    const res = await api.post('/api/teams', { name, slug, description, industry, size });
    setLoading(false);
    if (res.code === 201 || res.code === 200) {
      onCreated();
      onClose();
    } else {
      setError(res.message || t('team.createFailed'));
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-surface rounded-2xl p-6 w-full max-w-md shadow-xl" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold">{t('team.createTeam')}</h2>
          <button onClick={onClose} className="p-1 hover:bg-neutral-bg rounded-lg"><X className="w-5 h-5" /></button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">{t('team.nameLabel')}</label>
            <input
              value={name} onChange={e => handleNameChange(e.target.value)}
              className="w-full px-3 py-2 bg-neutral-bg border border-border rounded-lg text-sm focus:outline-none focus:border-primary"
              placeholder={t('team.namePlaceholder')} maxLength={128}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">{t('team.slugLabel')}</label>
            <div className="flex items-center gap-1 px-3 py-2 bg-neutral-bg border border-border rounded-lg text-sm">
              <span className="text-on-surface/40">/</span>
              <input
                value={slug} onChange={e => setSlug(generateSlug(e.target.value))}
                className="flex-1 bg-transparent outline-none"
                placeholder="my-team" maxLength={64}
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">{t('team.descriptionLabel')}</label>
            <textarea
              value={description} onChange={e => setDescription(e.target.value)}
              className="w-full px-3 py-2 bg-neutral-bg border border-border rounded-lg text-sm focus:outline-none focus:border-primary resize-none"
              rows={2} placeholder={t('team.descriptionPlaceholder')} maxLength={500}
            />
          </div>
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-1">{t('team.industry')}</label>
              <input
                value={industry} onChange={e => setIndustry(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-bg border border-border rounded-lg text-sm focus:outline-none focus:border-primary"
                placeholder={t('team.industryPlaceholder')}
              />
            </div>
            <div className="w-28">
              <label className="block text-sm font-medium mb-1">{t('team.size')}</label>
              <select
                value={size} onChange={e => setSize(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-bg border border-border rounded-lg text-sm focus:outline-none focus:border-primary"
              >
                <option value="1-10">{t('team.size1')}</option>
                <option value="11-50">{t('team.size2')}</option>
                <option value="51-200">{t('team.size3')}</option>
                <option value="201-500">{t('team.size4')}</option>
                <option value="500+">{t('team.size5')}</option>
              </select>
            </div>
          </div>
          {error && <p className="text-sm text-red-500 flex items-center gap-1"><AlertCircle className="w-4 h-4" />{error}</p>}
          <button
            onClick={handleSubmit} disabled={loading}
            className="w-full py-2.5 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            {t('team.createTeam')}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── 批量导入 Modal ───────────────────────────────

interface PreviewRow {
  [key: string]: string;
}

interface ImportResult {
  success: number;
  duplicate: number;
  failed: number;
  errors?: string[];
}

function parseCSV(text: string): { columns: string[]; rows: Record<string, string>[] } {
  const lines = text.split('\n').filter(l => l.trim().length > 0);
  if (lines.length === 0) return { columns: [], rows: [] };

  const parseLine = (line: string): string[] => {
    const result: string[] = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') {
        if (inQuotes && line[i + 1] === '"') { current += '"'; i++; }
        else { inQuotes = !inQuotes; }
      } else if (ch === ',' && !inQuotes) {
        result.push(current.trim());
        current = '';
      } else {
        current += ch;
      }
    }
    result.push(current.trim());
    return result;
  };

  const headers = parseLine(lines[0]).map(h => h.replace(/^"|"$/g, ''));
  const rows = lines.slice(1).map(line => {
    const values = parseLine(line).map(v => v.replace(/^"|"$/g, ''));
    const row: Record<string, string> = {};
    headers.forEach((h, i) => { row[h] = values[i] || ''; });
    return row;
  });

  return { columns: headers, rows };
}

function parseJSON(text: string): { columns: string[]; rows: Record<string, string>[] } {
  const data = JSON.parse(text);
  if (!Array.isArray(data)) throw new Error(t('team.jsonFormatError'));
  const rows = data.map((item: any) => {
    const row: Record<string, string> = {};
    Object.keys(item).forEach(k => { row[k] = String(item[k] ?? ''); });
    return row;
  });
  const columns = rows.length > 0 ? Object.keys(rows[0]) : [];
  return { columns, rows };
}

function BatchImportModal({ onClose, onImported }: { onClose: () => void; onImported: () => void }) {
  const t = useT();
  const [file, setFile] = useState<File | null>(null);
  const [previewColumns, setPreviewColumns] = useState<string[]>([]);
  const [previewRows, setPreviewRows] = useState<PreviewRow[]>([]);
  const [totalRows, setTotalRows] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState('');
  const [result, setResult] = useState<ImportResult | null>(null);
  const [importError, setImportError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (f: File) => {
    setParseError('');
    setResult(null);
    setImportError('');

    const ext = f.name.split('.').pop()?.toLowerCase();
    if (!['csv', 'json'].includes(ext || '')) {
      setParseError(t('team.formatNotSupported'));
      return;
    }

    setParsing(true);
    setFile(f);

    try {
      const text = await f.text();
      let columns: string[];
      let rows: Record<string, string>[];

      if (ext === 'json') {
        ({ columns, rows } = parseJSON(text));
      } else {
        ({ columns, rows } = parseCSV(text));
      }

      if (columns.length === 0) {
        setParseError(t('team.fileEmptyOrInvalid'));
        setParsing(false);
        return;
      }

      setPreviewColumns(columns);
      setPreviewRows(rows.slice(0, 5));
      setTotalRows(rows.length);
    } catch (e: any) {
      setParseError(t('team.parseFailed') + (e.message || t('team.unknownError')));
    }

    setParsing(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  };

  const handleImport = async () => {
    if (!file) return;
    setUploading(true);
    setImportError('');

    const formData = new FormData();
    formData.append('file', file);

    const res = await api.request('/api/brochures/batch-import', {
      method: 'POST',
      body: formData,
    });

    setUploading(false);

    if (res.code === 200 || res.code === 201) {
      const r = res.data as ImportResult;
      setResult(r);
      if (r.success > 0) onImported();
    } else {
      setImportError(res.message || t('team.importFailed'));
    }
  };

  const resetFile = () => {
    setFile(null);
    setPreviewColumns([]);
    setPreviewRows([]);
    setTotalRows(0);
    setParseError('');
    setResult(null);
    setImportError('');
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-surface rounded-2xl p-6 w-full max-w-2xl shadow-xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <Upload className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold">{t('team.batchImport')}</h2>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-neutral-bg rounded-lg"><X className="w-5 h-5" /></button>
        </div>

        {/* State: result shown */}
        {result ? (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-center">
              <Check className="w-10 h-10 text-green-500 mx-auto mb-2" />
              <h3 className="text-base font-semibold text-green-800">{t('team.importComplete')}</h3>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-green-50 rounded-xl p-3 text-center">
                <p className="text-2xl font-bold text-green-600">{result.success}</p>
                <p className="text-xs text-green-700 mt-1">{t('team.success')}</p>
              </div>
              <div className="bg-yellow-50 rounded-xl p-3 text-center">
                <p className="text-2xl font-bold text-yellow-600">{result.duplicate}</p>
                <p className="text-xs text-yellow-700 mt-1">{t('team.duplicate')}</p>
              </div>
              <div className="bg-red-50 rounded-xl p-3 text-center">
                <p className="text-2xl font-bold text-red-600">{result.failed}</p>
                <p className="text-xs text-red-700 mt-1">{t('team.failed')}</p>
              </div>
            </div>
            {result.errors && result.errors.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-3 max-h-32 overflow-y-auto">
                <p className="text-xs font-medium text-red-700 mb-1">{t('team.errorDetails')}：</p>
                {result.errors.map((err, i) => (
                  <p key={i} className="text-xs text-red-600 leading-relaxed">· {err}</p>
                ))}
              </div>
            )}
            <button
              onClick={onClose}
              className="w-full py-2.5 bg-primary text-white rounded-lg font-medium hover:bg-primary/90"
            >
              {t('team.close')}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {/* File upload area */}
            {!file ? (
              <div
                className={`relative border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200 ${
                  dragOver ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50 hover:bg-neutral-bg'
                }`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.json"
                  className="hidden"
                  onChange={handleFileSelect}
                />
                {parsing ? (
                  <div className="flex flex-col items-center gap-2">
                    <Loader2 className="w-8 h-8 text-primary animate-spin" />
                    <p className="text-sm text-on-surface/60">{t('team.parsingFile')}</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <FileText className="w-10 h-10 text-on-surface/30" />
                    <p className="text-sm font-medium text-on-surface">{t('team.dropFileHint')}</p>
                    <p className="text-xs text-on-surface/40">{t('team.supportedFormats')}</p>
                  </div>
                )}
              </div>
            ) : (
              /* File selected — show info + preview */
              <div className="space-y-3">
                <div className="flex items-center justify-between bg-neutral-bg rounded-lg px-4 py-2.5">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText className="w-5 h-5 text-primary shrink-0" />
                    <span className="text-sm font-medium truncate">{file.name}</span>
                    <span className="text-xs text-on-surface/40">({(file.size / 1024).toFixed(1)} KB, {totalRows} {t('team.records')})</span>
                  </div>
                  <button onClick={resetFile} className="p-1 hover:bg-surface rounded-lg shrink-0">
                    <X className="w-4 h-4 text-on-surface/50" />
                  </button>
                </div>

                {/* Parse error */}
                {parseError && (
                  <div className="flex items-center gap-2 text-sm text-red-500 bg-red-50 rounded-lg px-3 py-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    {parseError}
                  </div>
                )}

                {/* Preview table */}
                {previewColumns.length > 0 && (
                  <div>
                    <div className="flex items-center gap-1.5 mb-2">
                      <Table2 className="w-4 h-4 text-on-surface/50" />
                      <span className="text-xs font-medium text-on-surface/50">
                        {t('team.preview', { count: Math.min(5, totalRows), total: totalRows })}
                      </span>
                    </div>
                    <div className="overflow-x-auto border border-border rounded-lg">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="bg-neutral-bg">
                            <th className="px-3 py-2 text-left font-medium text-on-surface/60 whitespace-nowrap">#</th>
                            {previewColumns.map(col => (
                              <th key={col} className="px-3 py-2 text-left font-medium text-on-surface/60 whitespace-nowrap">
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {previewRows.map((row, ri) => (
                            <tr key={ri} className="border-t border-border hover:bg-neutral-bg/50">
                              <td className="px-3 py-2 text-on-surface/40">{ri + 1}</td>
                              {previewColumns.map(col => (
                                <td key={col} className="px-3 py-2 text-on-surface truncate max-w-[160px]" title={row[col]}>
                                  {row[col] || <span className="text-on-surface/20">-</span>}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Import error */}
                {importError && (
                  <div className="flex items-center gap-2 text-sm text-red-500 bg-red-50 rounded-lg px-3 py-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    {importError}
                  </div>
                )}

                {/* Confirm button */}
                <button
                  onClick={handleImport}
                  disabled={uploading || !!parseError || previewColumns.length === 0}
                  className="w-full py-2.5 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {uploading ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> {t('team.importing')}...</>
                  ) : (
                    <><Upload className="w-4 h-4" /> {t('team.confirmImport')}</>
                  )}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── 主页面 ───────────────────────────────────────

export default function TeamPage() {
  const navigate = useNavigate();
  const t = useT();
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [showImport, setShowImport] = useState(false);

  const loadTeams = useCallback(async () => {
    setLoading(true);
    const res = await api.get<Team[]>('/api/teams');
    if (res.data) setTeams(res.data);
    setLoading(false);
  }, []);

  useEffect(() => { loadTeams(); }, [loadTeams]);

  return (
    <div className="min-h-screen bg-neutral-bg">
      {/* Header */}
      <header className="bg-surface border-b border-border px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/')} className="p-2 hover:bg-neutral-bg rounded-xl">
              <Users className="w-5 h-5 text-on-surface" />
            </button>
            <h1 className="text-lg font-semibold">{t('team.management')}</h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowImport(true)}
              className="flex items-center gap-1.5 px-4 py-2 border border-border rounded-lg text-sm font-medium text-on-surface hover:bg-neutral-bg"
            >
              <Upload className="w-4 h-4" /> {t('team.batchImport')}
            </button>
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-1.5 px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90"
            >
              <Plus className="w-4 h-4" /> 创建团队
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : teams.length === 0 ? (
          <div className="text-center py-20">
            <Building2 className="w-16 h-16 mx-auto text-on-surface/20 mb-4" />
            <h2 className="text-xl font-semibold text-on-surface mb-2">{t('team.noTeams')}</h2>
            <p className="text-on-surface/50 mb-6">{t('team.noTeamsDesc')}</p>
            <button
              onClick={() => setShowCreate(true)}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-white rounded-lg font-medium hover:bg-primary/90"
            >
              <Plus className="w-4 h-4" /> {t('team.createTeam')}
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {teams.map(team => (
              <TeamCard
                key={team.id}
                team={team}
                onClick={() => navigate(`/team/${team.id}/settings`)}
              />
            ))}
          </div>
        )}
      </main>

      {showCreate && <CreateTeamModal onClose={() => setShowCreate(false)} onCreated={loadTeams} />}
    </div>
  );
}
