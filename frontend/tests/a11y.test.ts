import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import CardPreview from '../src/components/CardPreview';
import SearchBar from '../src/components/SearchBar';

expect.extend(toHaveNoViolations);

describe('Accessibility (a11y) tests', () => {
  // ── CardPreview ──
  it('CardPreview default should have no a11y violations', async () => {
    const { container } = render(
      <CardPreview fields={{ name: '张三', position: 'PM', company: 'AI Tech' }} />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('CardPreview empty state should have no a11y violations', async () => {
    const { container } = render(<CardPreview fields={{}} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('CardPreview full profile should have no a11y violations', async () => {
    const { container } = render(
      <CardPreview
        fields={{
          name: '李四',
          position: 'CTO',
          company: 'Tech Co',
          phone: '13800008888',
          email: 'li@example.com',
          address: 'Beijing',
          website: 'https://li.dev',
        }}
      />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  // ── SearchBar ──
  it('SearchBar default should have no a11y violations', async () => {
    const { container } = render(<SearchBar />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('SearchBar with text should have no a11y violations', async () => {
    const { container } = render(<SearchBar value="test" />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('SearchBar disabled should have no a11y violations', async () => {
    const { container } = render(<SearchBar disabled placeholder="搜索" />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
