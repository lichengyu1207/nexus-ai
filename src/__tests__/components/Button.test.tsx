import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/components/ui/Button';

describe('Button Component', () => {
  test('renders with default props', () => {
    render(<Button>Test Button</Button>);
    const button = screen.getByText('Test Button');
    expect(button).toBeInTheDocument();
  });

  test('renders with primary variant', () => {
    render(<Button variant="primary">Primary Button</Button>);
    const button = screen.getByText('Primary Button');
    expect(button).toBeInTheDocument();
  });

  test('renders with secondary variant', () => {
    render(<Button variant="secondary">Secondary Button</Button>);
    const button = screen.getByText('Secondary Button');
    expect(button).toBeInTheDocument();
  });

  test('renders with ghost variant', () => {
    render(<Button variant="ghost">Ghost Button</Button>);
    const button = screen.getByText('Ghost Button');
    expect(button).toBeInTheDocument();
  });

  test('renders with danger variant', () => {
    render(<Button variant="danger">Danger Button</Button>);
    const button = screen.getByText('Danger Button');
    expect(button).toBeInTheDocument();
  });

  test('renders with small size', () => {
    render(<Button size="sm">Small Button</Button>);
    const button = screen.getByText('Small Button');
    expect(button).toBeInTheDocument();
  });

  test('renders with medium size', () => {
    render(<Button size="md">Medium Button</Button>);
    const button = screen.getByText('Medium Button');
    expect(button).toBeInTheDocument();
  });

  test('renders with large size', () => {
    render(<Button size="lg">Large Button</Button>);
    const button = screen.getByText('Large Button');
    expect(button).toBeInTheDocument();
  });

  test('renders with icon', () => {
    render(
      <Button icon={<span>📋</span>}>
        Button with Icon
      </Button>
    );
    const button = screen.getByText('Button with Icon');
    expect(button).toBeInTheDocument();
  });

  test('handles click events', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click Me</Button>);
    const button = screen.getByText('Click Me');
    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled Button</Button>);
    const button = screen.getByText('Disabled Button');
    expect(button).toBeDisabled();
  });
});
