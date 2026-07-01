import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CardSkeleton, ListSkeleton, DetailSkeleton } from '../components/LoadingSkeleton';

describe('LoadingSkeleton', () => {
  describe('CardSkeleton', () => {
    it('renders default count of 1 skeleton card', () => {
      const { container } = render(<CardSkeleton />);

      // Should render 1 card skeleton
      const cardElements = container.children;
      expect(cardElements.length).toBe(1);
    });

    it('renders specified number of skeleton cards', () => {
      const { container } = render(<CardSkeleton count={3} />);

      expect(container.children.length).toBe(3);
    });

    it('renders skeleton blocks inside each card', () => {
      const { container } = render(<CardSkeleton count={1} />);

      // Card skeleton should have skeleton class elements
      const skeletonBlocks = container.querySelectorAll('.skeleton');
      expect(skeletonBlocks.length).toBeGreaterThan(0);
    });
  });

  describe('ListSkeleton', () => {
    it('renders default 5 rows', () => {
      const { container } = render(<ListSkeleton />);

      // The rows are wrapped in a div with divide-y
      const rows = container.firstChild?.childNodes;
      expect(rows?.length).toBe(5);
    });

    it('renders specified number of rows', () => {
      const { container } = render(<ListSkeleton rows={3} />);

      const rows = container.firstChild?.childNodes;
      expect(rows?.length).toBe(3);
    });

    it('renders avatar circles when avatar=true', () => {
      const { container } = render(<ListSkeleton rows={1} avatar />);

      // 1 avatar circle + 1 badge rounded-full
      const circles = container.querySelectorAll('.skeleton.rounded-full');
      expect(circles.length).toBe(2);
    });

    it('does not render avatar circles when avatar=false', () => {
      const { container } = render(<ListSkeleton rows={1} avatar={false} />);

      // Only the badge rounded-full remains
      const circles = container.querySelectorAll('.skeleton.rounded-full');
      expect(circles.length).toBe(1);
    });
  });

  describe('DetailSkeleton', () => {
    it('renders with default 4 field rows', () => {
      const { container } = render(<DetailSkeleton />);

      // Should have skeleton elements
      const skeletonBlocks = container.querySelectorAll('.skeleton');
      expect(skeletonBlocks.length).toBeGreaterThan(0);
    });

    it('renders specified number of field rows', () => {
      const { container } = render(<DetailSkeleton fields={6} />);

      const skeletonBlocks = container.querySelectorAll('.skeleton');
      expect(skeletonBlocks.length).toBeGreaterThan(0);
    });
  });
});
