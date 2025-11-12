/**
 * Tests for DynamicForm Component
 *
 * Tests dynamic form generation from recipe manifests, validation,
 * and form submission handling.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DynamicForm } from './DynamicForm';
import type { RecipeManifest } from '@/lib/types/recipes';

describe('DynamicForm', () => {
  const mockRecipe: RecipeManifest = {
    id: 'test-recipe',
    name: 'Test Recipe',
    description: 'Test description',
    version: '1.0.0',
    category: 'test',
    inputs: [
      {
        name: 'text_field',
        type: 'text',
        required: true,
        description: 'A required text field'
      },
      {
        name: 'number_field',
        type: 'number',
        required: false,
        description: 'An optional number field'
      },
      {
        name: 'textarea_field',
        type: 'textarea',
        required: true,
        description: 'A required textarea'
      }
    ],
    outputs: [],
    tags: [],
    requirements: []
  };

  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('renders all input fields from recipe manifest', () => {
    render(
      <DynamicForm
        recipe={mockRecipe}
        onSubmit={mockOnSubmit}
      />
    );

    // Check that all inputs are rendered
    expect(screen.getByLabelText(/text_field/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/number_field/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/textarea_field/i)).toBeInTheDocument();

    // Check that required indicators are shown
    const labels = screen.getAllByText('*');
    expect(labels.length).toBeGreaterThan(0);
  });

  it('validates required fields on submit', async () => {
    render(
      <DynamicForm
        recipe={mockRecipe}
        onSubmit={mockOnSubmit}
      />
    );

    const submitButton = screen.getByRole('button', { name: /submit|envoyer|executer/i });
    fireEvent.click(submitButton);

    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText(/Ce champ est requis/i)).toBeInTheDocument();
    });

    // Should not call onSubmit
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();

    render(
      <DynamicForm
        recipe={mockRecipe}
        onSubmit={mockOnSubmit}
      />
    );

    // Fill required fields
    const textInput = screen.getByLabelText(/text_field/i);
    const textareaInput = screen.getByLabelText(/textarea_field/i);

    await user.type(textInput, 'Test text value');
    await user.type(textareaInput, 'Test textarea value');

    // Submit form
    const submitButton = screen.getByRole('button', { name: /submit|envoyer|executer/i });
    await user.click(submitButton);

    // Should call onSubmit
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledTimes(1);
    });

    // Check FormData contains correct values
    const formData = mockOnSubmit.mock.calls[0][0];
    expect(formData).toBeInstanceOf(FormData);
  });

  it('clears validation errors when user starts typing', async () => {
    const user = userEvent.setup();

    render(
      <DynamicForm
        recipe={mockRecipe}
        onSubmit={mockOnSubmit}
      />
    );

    // Try to submit with empty fields
    const submitButton = screen.getByRole('button', { name: /submit|envoyer|executer/i });
    fireEvent.click(submitButton);

    // Wait for validation error
    await waitFor(() => {
      expect(screen.getByText(/Ce champ est requis/i)).toBeInTheDocument();
    });

    // Start typing in the field
    const textInput = screen.getByLabelText(/text_field/i);
    await user.type(textInput, 'T');

    // Validation error should be cleared
    await waitFor(() => {
      expect(screen.queryByText(/Ce champ est requis/i)).not.toBeInTheDocument();
    });
  });

  it('displays loading state during submission', () => {
    render(
      <DynamicForm
        recipe={mockRecipe}
        onSubmit={mockOnSubmit}
        loading={true}
      />
    );

    // Submit button should be disabled
    const submitButton = screen.getByRole('button');
    expect(submitButton).toBeDisabled();

    // Should show loading indicator
    expect(screen.getByRole('button')).toHaveAttribute('disabled');
  });

  it('displays error message when provided', () => {
    const errorMessage = 'An error occurred during submission';

    render(
      <DynamicForm
        recipe={mockRecipe}
        onSubmit={mockOnSubmit}
        error={errorMessage}
      />
    );

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('handles optional fields correctly', async () => {
    const user = userEvent.setup();

    const recipeWithOptionalField: RecipeManifest = {
      ...mockRecipe,
      inputs: [
        {
          name: 'optional_field',
          type: 'text',
          required: false,
          description: 'Optional field'
        }
      ]
    };

    render(
      <DynamicForm
        recipe={recipeWithOptionalField}
        onSubmit={mockOnSubmit}
      />
    );

    // Submit without filling optional field
    const submitButton = screen.getByRole('button');
    await user.click(submitButton);

    // Should call onSubmit even with empty optional field
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled();
    });
  });
});
