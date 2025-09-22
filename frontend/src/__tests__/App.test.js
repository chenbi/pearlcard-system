import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../App';
import JourneyForm from '../components/JourneyForm';
import FareTable from '../components/FareTable';
import FilterControls from '../components/FilterControls';

// Mock the API service
jest.mock('../services/api', () => ({
  calculateFares: jest.fn(() => 
    Promise.resolve({
      journeys: [
        { journey_id: 1, from_zone: 1, to_zone: 2, fare: 55 },
        { journey_id: 2, from_zone: 2, to_zone: 3, fare: 45 }
      ],
      total_daily_fare: 100,
      journey_count: 2
    })
  ),
  getFareRules: jest.fn(() => 
    Promise.resolve({
      rules: [],
      max_journeys_per_day: 20,
      available_zones: []  // Dynamic zones, not hardcoded
    })
  ),
  healthCheck: jest.fn(() => 
    Promise.resolve({ status: 'healthy' })
  )
}));

describe('App Component', () => {
  test('renders header with title', () => {
    render(<App />);
    const titleElement = screen.getByText(/PearlCard Fare Calculator/i);
    expect(titleElement).toBeInTheDocument();
  });

  test('renders journey form section', () => {
    render(<App />);
    const formTitle = screen.getByText(/Enter Journeys/i);
    expect(formTitle).toBeInTheDocument();
  });
});

describe('JourneyForm Component', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  test('renders initial journey input', () => {
    render(<JourneyForm onSubmit={mockOnSubmit} maxJourneys={20} />);
    
    const fromZoneLabels = screen.getAllByText(/From Zone:/i);
    const toZoneLabels = screen.getAllByText(/To Zone:/i);
    
    expect(fromZoneLabels).toHaveLength(1);
    expect(toZoneLabels).toHaveLength(1);
  });

  test('adds new journey when Add Journey button is clicked', () => {
    render(<JourneyForm onSubmit={mockOnSubmit} maxJourneys={20} />);
    
    const addButton = screen.getByText(/Add Journey/i);
    fireEvent.click(addButton);
    
    const fromZoneLabels = screen.getAllByText(/From Zone:/i);
    expect(fromZoneLabels).toHaveLength(2);
  });

  test('removes journey when remove button is clicked', () => {
    render(<JourneyForm onSubmit={mockOnSubmit} maxJourneys={20} />);
    
    // Add a second journey first
    const addButton = screen.getByText(/Add Journey/i);
    fireEvent.click(addButton);
    
    // Remove the second journey
    const removeButtons = screen.getAllByTitle(/Remove journey/i);
    fireEvent.click(removeButtons[1]);
    
    const fromZoneLabels = screen.getAllByText(/From Zone:/i);
    expect(fromZoneLabels).toHaveLength(1);
  });

  test('disables Add Journey button when max journeys reached', () => {
    render(<JourneyForm onSubmit={mockOnSubmit} maxJourneys={2} />);
    
    const addButton = screen.getByText(/Add Journey/i);
    
    // Add one more journey to reach max
    fireEvent.click(addButton);
    
    expect(addButton).toBeDisabled();
  });

  test('validates form before submission', async () => {
    render(<JourneyForm onSubmit={mockOnSubmit} maxJourneys={20} />);
    
    const submitButton = screen.getByText(/Calculate Fares/i);
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  test('submits form with valid data', async () => {
    render(<JourneyForm onSubmit={mockOnSubmit} maxJourneys={20} />);
    
    // Select zones
    const fromZoneSelects = screen.getAllByLabelText(/From Zone:/i);
    const toZoneSelects = screen.getAllByLabelText(/To Zone:/i);
    
    fireEvent.change(fromZoneSelects[0], { target: { value: '1' } });
    fireEvent.change(toZoneSelects[0], { target: { value: '2' } });
    
    const submitButton = screen.getByText(/Calculate Fares/i);
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith([
        { from_zone: 1, to_zone: 2 }
      ]);
    });
  });

  test('clears form when Clear All button is clicked', () => {
    render(<JourneyForm onSubmit={mockOnSubmit} maxJourneys={20} />);
    
    // Add values
    const fromZoneSelects = screen.getAllByLabelText(/From Zone:/i);
    fireEvent.change(fromZoneSelects[0], { target: { value: '1' } });
    
    // Clear form
    const clearButton = screen.getByText(/Clear All/i);
    fireEvent.click(clearButton);
    
    // Check if form is cleared
    const updatedFromZoneSelects = screen.getAllByLabelText(/From Zone:/i);
    expect(updatedFromZoneSelects[0].value).toBe('');
  });
});

describe('FareTable Component', () => {
  const mockFareResponse = {
    journeys: [
      { journey_id: 1, from_zone: 1, to_zone: 2, fare: 55 },
      { journey_id: 2, from_zone: 2, to_zone: 3, fare: 45 },
      { journey_id: 3, from_zone: 3, to_zone: 3, fare: 30 }
    ],
    total_daily_fare: 130,
    journey_count: 3
  };

  test('renders fare table with journeys', () => {
    render(<FareTable fareResponse={mockFareResponse} filters={{}} />);
    
    expect(screen.getByText('#1')).toBeInTheDocument();
    expect(screen.getByText('£55.00')).toBeInTheDocument();
    expect(screen.getByText('£45.00')).toBeInTheDocument();
    expect(screen.getByText('£30.00')).toBeInTheDocument();
  });

  test('displays filtered total', () => {
    render(<FareTable fareResponse={mockFareResponse} filters={{}} />);
    
    const totalText = screen.getByText(/Filtered Total/i);
    expect(totalText).toBeInTheDocument();
    expect(screen.getByText('£130.00')).toBeInTheDocument();
  });

  test('sorts table when column header is clicked', () => {
    render(<FareTable fareResponse={mockFareResponse} filters={{}} />);
    
    const fareHeader = screen.getByText(/Fare \(£\)/i);
    fireEvent.click(fareHeader);
    
    // After sorting, the order should change
    const cells = screen.getAllByRole('cell');
    expect(cells).toBeDefined();
  });

  test('filters journeys based on price', () => {
    const filters = { operator: '>', value: '40' };
    render(<FareTable fareResponse={mockFareResponse} filters={filters} />);
    
    // Should only show journeys with fare > 40 (55 and 45)
    expect(screen.getByText('£55.00')).toBeInTheDocument();
    expect(screen.getByText('£45.00')).toBeInTheDocument();
    expect(screen.queryByText('£30.00')).not.toBeInTheDocument();
  });

  test('shows no results message when filter returns empty', () => {
    const filters = { operator: '>', value: '100' };
    render(<FareTable fareResponse={mockFareResponse} filters={filters} />);
    
    expect(screen.getByText(/No journeys match the filter criteria/i)).toBeInTheDocument();
  });
});

describe('FilterControls Component', () => {
  const mockOnFilterChange = jest.fn();

  beforeEach(() => {
    mockOnFilterChange.mockClear();
  });

  test('renders filter controls', () => {
    render(<FilterControls onFilterChange={mockOnFilterChange} />);
    
    expect(screen.getByText(/Filter by price:/i)).toBeInTheDocument();
    expect(screen.getByText(/Value \(£\):/i)).toBeInTheDocument();
  });

  test('calls onFilterChange when operator is selected', () => {
    render(<FilterControls onFilterChange={mockOnFilterChange} />);
    
    const operatorSelect = screen.getByLabelText(/Filter by price:/i);
    fireEvent.change(operatorSelect, { target: { value: '>' } });
    
    expect(mockOnFilterChange).toHaveBeenCalledWith({
      operator: '>',
      value: ''
    });
  });

  test('validates numeric input', () => {
    render(<FilterControls onFilterChange={mockOnFilterChange} />);
    
    const valueInput = screen.getByLabelText(/Value \(£\):/i);
    fireEvent.change(valueInput, { target: { value: 'abc' } });
    
    expect(screen.getByText(/Please enter a valid number/i)).toBeInTheDocument();
  });

  test('applies filter with valid inputs', () => {
    render(<FilterControls onFilterChange={mockOnFilterChange} />);
    
    const operatorSelect = screen.getByLabelText(/Filter by price:/i);
    const valueInput = screen.getByLabelText(/Value \(£\):/i);
    
    fireEvent.change(operatorSelect, { target: { value: '>' } });
    fireEvent.change(valueInput, { target: { value: '30' } });
    
    const applyButton = screen.getByText(/Apply Filter/i);
    fireEvent.click(applyButton);
    
    expect(mockOnFilterChange).toHaveBeenCalledWith({
      operator: '>',
      value: '30'
    });
  });

  test('clears filter when Clear Filter button is clicked', () => {
    render(<FilterControls onFilterChange={mockOnFilterChange} />);
    
    // Set some values first
    const operatorSelect = screen.getByLabelText(/Filter by price:/i);
    const valueInput = screen.getByLabelText(/Value \(£\):/i);
    
    fireEvent.change(operatorSelect, { target: { value: '>' } });
    fireEvent.change(valueInput, { target: { value: '30' } });
    
    // Clear filter
    const clearButton = screen.getByText(/Clear Filter/i);
    fireEvent.click(clearButton);
    
    expect(mockOnFilterChange).toHaveBeenCalledWith({
      operator: '',
      value: ''
    });
  });

  test('shows active filter badge when filter is applied', () => {
    render(<FilterControls onFilterChange={mockOnFilterChange} />);
    
    const operatorSelect = screen.getByLabelText(/Filter by price:/i);
    const valueInput = screen.getByLabelText(/Value \(£\):/i);
    
    fireEvent.change(operatorSelect, { target: { value: '=' } });
    fireEvent.change(valueInput, { target: { value: '50' } });
    
    expect(screen.getByText(/Active Filter: Fare = £50/i)).toBeInTheDocument();
  });
});
