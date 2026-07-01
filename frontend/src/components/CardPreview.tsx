import { User, Briefcase, Building2, Phone, Mail, MapPin, Globe } from 'lucide-react';

export interface CardFields {
  name?: string;
  position?: string;
  company?: string;
  phone?: string;
  email?: string;
  address?: string;
  website?: string;
  cover_image?: string;
}

interface CardPreviewProps {
  fields: CardFields;
  template?: string;
  compact?: boolean;
}

const TEMPLATES: Record<string, { bg: string; main: string; accent: string; text: string }> = {
  default: { bg: 'bg-gradient-to-br from-blue-500 to-blue-700', main: 'bg-blue-600', accent: '#60A5FA', text: 'text-white' },
  purple: { bg: 'bg-gradient-to-br from-purple-500 to-indigo-800', main: 'bg-purple-600', accent: '#A78BFA', text: 'text-white' },
  dark: { bg: 'bg-gradient-to-br from-gray-800 to-gray-950', main: 'bg-gray-700', accent: '#6B7280', text: 'text-white' },
};

export default function CardPreview({ fields, template = 'default', compact = false }: CardPreviewProps) {
  const tpl = TEMPLATES[template] || TEMPLATES.default;
  const { name, position, company, phone, email, address, website } = fields;

  const items = [
    { icon: Briefcase, label: position },
    { icon: Building2, label: company },
    { icon: Phone, label: phone },
    { icon: Mail, label: email },
    { icon: MapPin, label: address },
    { icon: Globe, label: website },
  ].filter((i) => i.label);

  return (
    <div
      data-testid="card-preview"
      className={`rounded-2xl overflow-hidden shadow-lg ${tpl.bg} ${tpl.text} ${compact ? 'w-64' : 'w-80'}`}
    >
      {/* Avatar area */}
      <div className="flex flex-col items-center pt-6 pb-4 px-4">
        <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mb-3" aria-hidden="true">
          <User className="w-8 h-8 text-white/80" />
        </div>
        {name ? (
          <h3 className="text-lg font-bold text-center">{name}</h3>
        ) : (
          <h3 className="text-lg font-bold text-center text-white/50">未命名名片</h3>
        )}
      </div>

      {/* Info fields */}
      {!compact && items.length > 0 && (
        <div className="px-4 pb-5 space-y-2">
          {items.map((item, idx) => (
            <div key={idx} className="flex items-center gap-2 text-sm text-white/90">
              <item.icon className="w-4 h-4 shrink-0" aria-hidden="true" />
              <span className="truncate">{item.label}</span>
            </div>
          ))}
        </div>
      )}

      {!compact && items.length === 0 && (
        <div className="px-4 pb-5 text-center text-sm text-white/50">
          暂无资料
        </div>
      )}
    </div>
  );
}
