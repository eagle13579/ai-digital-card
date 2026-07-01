import { Search, X } from 'lucide-react';

interface SearchBarProps {
  value?: string;
  onChange?: (value: string) => void;
  onClear?: () => void;
  placeholder?: string;
  disabled?: boolean;
}

export default function SearchBar({
  value = '',
  onChange,
  onClear,
  placeholder = '搜索名片...',
  disabled = false,
}: SearchBarProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange?.(e.target.value);
  };

  const handleClear = () => {
    onChange?.('');
    onClear?.();
  };

  return (
    <div
      data-testid="search-bar"
      className="relative flex items-center w-full max-w-md"
      role="search"
    >
      <Search
        className="absolute left-3 w-4 h-4 text-text-muted pointer-events-none"
        aria-hidden="true"
      />
      <input
        type="text"
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        disabled={disabled}
        aria-label={placeholder}
        className="w-full pl-9 pr-9 py-2.5 rounded-xl bg-slate-50 border border-border-light text-sm text-on-surface placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      />
      {value && (
        <button
          onClick={handleClear}
          className="absolute right-2.5 p-1 rounded-md hover:bg-slate-200 transition-colors"
          aria-label="清除搜索"
        >
          <X className="w-4 h-4 text-text-muted" />
        </button>
      )}
    </div>
  );
}
