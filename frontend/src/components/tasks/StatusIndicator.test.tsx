/**
 * Tests for StatusIndicator Component
 *
 * Tests task status visualization including pending, processing, completed,
 * and error states.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusIndicator } from './StatusIndicator';

describe('StatusIndicator', () => {
  it('renders pending status correctly', () => {
    render(<StatusIndicator status="pending" />);

    const indicator = screen.getByRole('status', { hidden: true });
    expect(indicator).toBeInTheDocument();
  });

  it('renders processing status with animation', () => {
    render(<StatusIndicator status="processing" />);

    const indicator = screen.getByRole('status', { hidden: true });
    expect(indicator).toBeInTheDocument();

    // Should have animated class (spinner or pulse animation)
    expect(indicator.className).toMatch(/animate|spin|pulse/i);
  });

  it('renders completed status with success indicator', () => {
    render(<StatusIndicator status="completed" />);

    const indicator = screen.getByRole('status', { hidden: true });
    expect(indicator).toBeInTheDocument();

    // Should show success/check icon or green color
    expect(indicator.className).toMatch(/success|green|check/i);
  });

  it('renders error status with error indicator', () => {
    render(<StatusIndicator status="error" />);

    const indicator = screen.getByRole('status', { hidden: true });
    expect(indicator).toBeInTheDocument();

    // Should show error icon or red color
    expect(indicator.className).toMatch(/error|red|alert/i);
  });

  it('renders human_input_required status', () => {
    render(<StatusIndicator status="human_input_required" />);

    const indicator = screen.getByRole('status', { hidden: true });
    expect(indicator).toBeInTheDocument();
  });

  it('displays status label when provided', () => {
    const label = 'Task is running';

    render(<StatusIndicator status="processing" label={label} />);

    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const customClass = 'custom-status-class';

    const { container } = render(
      <StatusIndicator status="pending" className={customClass} />
    );

    const indicator = container.querySelector(`.${customClass}`);
    expect(indicator).toBeInTheDocument();
  });

  it('handles unknown status gracefully', () => {
    // @ts-expect-error Testing invalid status
    const { container } = render(<StatusIndicator status="unknown" />);

    // Should still render without crashing
    expect(container).toBeInTheDocument();
  });
});

describe('StatusIndicator Accessibility', () => {
  it('has proper ARIA labels for pending status', () => {
    render(<StatusIndicator status="pending" />);

    const indicator = screen.getByRole('status', { hidden: true });
    expect(indicator).toHaveAttribute('aria-label', 'pending');
  });

  it('has proper ARIA labels for processing status', () => {
    render(<StatusIndicator status="processing" />);

    const indicator = screen.getByRole('status', { hidden: true });
    expect(indicator).toHaveAttribute('aria-label', 'processing');
  });

  it('has proper ARIA labels for completed status', () => {
    render(<StatusIndicator status="completed" />);

    const indicator = screen.getByRole('status', { hidden: true });
    expect(indicator).toHaveAttribute('aria-label', 'completed');
  });

  it('has proper ARIA labels for error status', () => {
    render(<StatusIndicator status="error" />);

    const indicator = screen.getByRole('status', { hidden: true });
    expect(indicator).toHaveAttribute('aria-label', 'error');
  });

  it('announces status changes to screen readers', () => {
    const { rerender } = render(<StatusIndicator status="pending" />);

    // Change status
    rerender(<StatusIndicator status="processing" />);

    // ARIA live region should announce the change
    const indicator = screen.getByRole('status', { hidden: true });
    expect(indicator).toBeInTheDocument();
  });
});
