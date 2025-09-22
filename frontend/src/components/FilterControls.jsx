import React, { useState, useCallback } from 'react';
import './FilterControls.css';

const FilterControls = ({ onFilterChange }) => {
  const [operator, setOperator] = useState('');
  const [value, setValue] = useState('');
  const [error, setError] = useState('');

  const operators = [
    { value: '', label: 'Select operator' },
    { value: '>', label: 'Greater than (>)' },
    { value: '<', label: 'Less than (<)' },
    { value: '=', label: 'Equal to (=)' },
    { value: '>=', label: 'Greater or equal (≥)' },
    { value: '<=', label: 'Less or equal (≤)' }
  ];

  const handleOperatorChange = useCallback((e) => {
    const newOperator = e.target.value;
    setOperator(newOperator);
    onFilterChange({ operator: newOperator, value });
  }, [value, onFilterChange]);

  const handleValueChange = useCallback((e) => {
    const newValue = e.target.value;
    setValue(newValue);
    
    // Validate input
    if (newValue && isNaN(parseFloat(newValue))) {
      setError('Please enter a valid number');
    } else {
      setError('');
      onFilterChange({ operator, value: newValue });
    }
  }, [operator, onFilterChange]);

  const clearFilter = useCallback(() => {
    setOperator('');
    setValue('');
    setError('');
    onFilterChange({ operator: '', value: '' });
  }, [onFilterChange]);

  const applyFilter = useCallback(() => {
    if (operator && value && !error) {
      onFilterChange({ operator, value });
    }
  }, [operator, value, error, onFilterChange]);

  return (
    <div className="filter-controls">
      <div className="filter-inputs">
        <div className="filter-group">
          <label htmlFor="operator">Filter by price:</label>
          <select
            id="operator"
            value={operator}
            onChange={handleOperatorChange}
            className="filter-select"
          >
            {operators.map(op => (
              <option key={op.value} value={op.value}>
                {op.label}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="value">Value (£):</label>
          <input
            id="value"
            type="number"
            value={value}
            onChange={handleValueChange}
            placeholder="Enter amount"
            className={`filter-input ${error ? 'error' : ''}`}
            step="0.01"
            min="0"
          />
          {error && <span className="error-text">{error}</span>}
        </div>

        <div className="filter-actions">
          <button
            type="button"
            onClick={applyFilter}
            className="btn-apply"
            disabled={!operator || !value || !!error}
          >
            Apply Filter
          </button>
          <button
            type="button"
            onClick={clearFilter}
            className="btn-clear-filter"
          >
            Clear Filter
          </button>
        </div>
      </div>

      {operator && value && !error && (
        <div className="active-filter">
          <span className="filter-badge">
            Active Filter: Fare {operator} £{value}
          </span>
        </div>
      )}

      <div className="filter-examples">
        <small>
          Examples: &gt; 30 (fares greater than £30), &lt; 60 (fares less than £60), = 50 (fares equal to £50)
        </small>
      </div>
    </div>
  );
};

export default FilterControls;
