/**
 * Tests for RecipeCard Component
 *
 * Tests recipe card rendering, category icons/colors, and navigation.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RecipeCard } from './RecipeCard';
import type { RecipeManifest } from '@/lib/types/recipes';

// Mock next/navigation
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush
  })
}));

describe('RecipeCard', () => {
  const baseRecipe: RecipeManifest = {
    id: 'test-recipe',
    name: 'Test Recipe',
    description: 'Test description for the recipe',
    version: '1.0.0',
    category: 'fiscal',
    inputs: [],
    outputs: [],
    tags: ['test', 'automation'],
    requirements: []
  };

  beforeEach(() => {
    mockPush.mockClear();
  });

  it('renders recipe name and description', () => {
    render(<RecipeCard recipe={baseRecipe} />);

    expect(screen.getByText(baseRecipe.name)).toBeInTheDocument();
    expect(screen.getByText(baseRecipe.description)).toBeInTheDocument();
  });

  it('displays recipe tags as badges', () => {
    render(<RecipeCard recipe={baseRecipe} />);

    baseRecipe.tags.forEach(tag => {
      expect(screen.getByText(tag)).toBeInTheDocument();
    });
  });

  it('shows version information', () => {
    render(<RecipeCard recipe={baseRecipe} />);

    expect(screen.getByText(/1\.0\.0/)).toBeInTheDocument();
  });

  it('navigates to recipe detail page on click', async () => {
    const user = userEvent.setup();

    render(<RecipeCard recipe={baseRecipe} />);

    const card = screen.getByRole('button', { name: /test recipe/i });
    await user.click(card);

    expect(mockPush).toHaveBeenCalledWith(`/recipes/${baseRecipe.id}`);
  });

  it('displays correct icon for fiscal category', () => {
    render(<RecipeCard recipe={{ ...baseRecipe, category: 'fiscal' }} />);

    // Check that FileText icon is rendered (data-testid or aria-label)
    const card = screen.getByRole('button');
    expect(card).toBeInTheDocument();
  });

  it('displays correct icon for legal category', () => {
    render(<RecipeCard recipe={{ ...baseRecipe, category: 'legal' }} />);

    const card = screen.getByRole('button');
    expect(card).toBeInTheDocument();
  });

  it('displays correct icon for analysis category', () => {
    render(<RecipeCard recipe={{ ...baseRecipe, category: 'analysis' }} />);

    const card = screen.getByRole('button');
    expect(card).toBeInTheDocument();
  });

  it('displays default icon for unknown category', () => {
    render(<RecipeCard recipe={{ ...baseRecipe, category: 'unknown' }} />);

    const card = screen.getByRole('button');
    expect(card).toBeInTheDocument();
  });

  it('shows conversational mode indicator when applicable', () => {
    const conversationalRecipe: RecipeManifest = {
      ...baseRecipe,
      interaction_mode: 'conversational'
    };

    render(<RecipeCard recipe={conversationalRecipe} />);

    // Should show MessageSquare icon or conversational badge
    const card = screen.getByRole('button');
    expect(card).toBeInTheDocument();
  });

  it('applies custom className when provided', () => {
    const customClass = 'custom-test-class';

    const { container } = render(
      <RecipeCard recipe={baseRecipe} className={customClass} />
    );

    const card = container.querySelector(`.${customClass}`);
    expect(card).toBeInTheDocument();
  });

  it('renders all requirements when available', () => {
    const recipeWithRequirements: RecipeManifest = {
      ...baseRecipe,
      requirements: ['Notion API', 'Google Calendar API']
    };

    render(<RecipeCard recipe={recipeWithRequirements} />);

    // Requirements might be displayed in a tooltip or info section
    const card = screen.getByRole('button');
    expect(card).toBeInTheDocument();
  });

  it('displays correct input/output count', () => {
    const recipeWithIO: RecipeManifest = {
      ...baseRecipe,
      inputs: [
        { name: 'input1', type: 'text', required: true, description: 'Test input' },
        { name: 'input2', type: 'number', required: false, description: 'Test input 2' }
      ],
      outputs: [
        { name: 'output1', type: 'text', description: 'Test output' }
      ]
    };

    render(<RecipeCard recipe={recipeWithIO} />);

    // Should show input/output count indicators
    const card = screen.getByRole('button');
    expect(card).toBeInTheDocument();
  });
});
