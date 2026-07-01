import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import CardPreview from '../components/CardPreview';

describe('CardPreview', () => {
  it('renders with all fields', () => {
    const fields = {
      name: '张三',
      position: '工程师',
      company: '测试公司',
      phone: '13800138000',
      email: 'test@example.com',
      address: '北京市朝阳区',
      website: 'https://example.com',
    };

    render(<CardPreview fields={fields} />);

    const card = screen.getByTestId('card-preview');
    expect(card).toBeInTheDocument();

    expect(screen.getByText('张三')).toBeInTheDocument();
    expect(screen.getByText('工程师')).toBeInTheDocument();
    expect(screen.getByText('测试公司')).toBeInTheDocument();
    expect(screen.getByText('13800138000')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    expect(screen.getByText('北京市朝阳区')).toBeInTheDocument();
    expect(screen.getByText('https://example.com')).toBeInTheDocument();
  });

  it('renders fallback name when name is empty', () => {
    render(<CardPreview fields={{}} />);

    expect(screen.getByText('未命名名片')).toBeInTheDocument();
  });

  it('shows "暂无资料" when no info fields provided and not compact', () => {
    render(<CardPreview fields={{ name: '李四' }} />);

    expect(screen.getByText('暂无资料')).toBeInTheDocument();
  });

  it('hides info section in compact mode', () => {
    const fields = {
      name: '王五',
      position: '设计师',
    };

    render(<CardPreview fields={fields} compact />);

    expect(screen.getByText('王五')).toBeInTheDocument();
    expect(screen.queryByText('设计师')).not.toBeInTheDocument();
    expect(screen.queryByText('暂无资料')).not.toBeInTheDocument();
  });

  it('applies compact width class in compact mode', () => {
    const { container } = render(
      <CardPreview fields={{ name: 'Test' }} compact />
    );

    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('w-64');
  });

  it('applies default width when not compact', () => {
    const { container } = render(
      <CardPreview fields={{ name: 'Test' }} />
    );

    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('w-80');
  });

  it('supports different templates', () => {
    const { container: defaultCard } = render(
      <CardPreview fields={{ name: 'Test' }} template="default" />
    );
    const { container: purpleCard } = render(
      <CardPreview fields={{ name: 'Test' }} template="purple" />
    );

    expect(defaultCard.firstChild?.className).toContain('from-blue-500');
    expect(purpleCard.firstChild?.className).toContain('from-purple-500');
  });

  it('falls back to default template for unknown template', () => {
    const { container } = render(
      <CardPreview fields={{ name: 'Test' }} template="nonexistent" />
    );

    expect(container.firstChild?.className).toContain('from-blue-500');
  });
});
