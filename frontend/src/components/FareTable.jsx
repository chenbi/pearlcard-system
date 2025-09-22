import React, { useState, useCallback, useMemo } from 'react';
import './FareTable.css';

const FareTable = ({ fareResponse, filters }) => {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  const handleSort = useCallback((key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  }, [sortConfig]);

  const filterJourneys = useCallback((journeys) => {
    if (!filters.operator || !filters.value) {
      return journeys;
    }

    const filterValue = parseFloat(filters.value);
    if (isNaN(filterValue)) {
      return journeys;
    }

    return journeys.filter(journey => {
      const fare = journey.fare;
      switch (filters.operator) {
        case '>':
          return fare > filterValue;
        case '<':
          return fare < filterValue;
        case '=':
          return fare === filterValue;
        case '>=':
          return fare >= filterValue;
        case '<=':
          return fare <= filterValue;
        default:
          return true;
      }
    });
  }, [filters]);

  const sortedAndFilteredJourneys = useMemo(() => {
    let journeys = [...fareResponse.journeys];
    
    // Apply filter
    journeys = filterJourneys(journeys);
    
    // Apply sort
    if (sortConfig.key) {
      journeys.sort((a, b) => {
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];
        
        if (aValue < bValue) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    
    return journeys;
  }, [fareResponse.journeys, sortConfig, filterJourneys]);

  const getSortIcon = (columnKey) => {
    if (sortConfig.key !== columnKey) {
      return '⇅';
    }
    return sortConfig.direction === 'asc' ? '↑' : '↓';
  };

  const filteredTotal = useMemo(() => {
    return sortedAndFilteredJourneys.reduce((sum, journey) => sum + journey.fare, 0);
  }, [sortedAndFilteredJourneys]);

  return (
    <div className="fare-table-container">
      <table className="fare-table">
        <thead>
          <tr>
            <th 
              onClick={() => handleSort('journey_id')}
              className="sortable"
            >
              Journey # {getSortIcon('journey_id')}
            </th>
            <th 
              onClick={() => handleSort('from_zone')}
              className="sortable"
            >
              From Zone {getSortIcon('from_zone')}
            </th>
            <th 
              onClick={() => handleSort('to_zone')}
              className="sortable"
            >
              To Zone {getSortIcon('to_zone')}
            </th>
            <th 
              onClick={() => handleSort('fare')}
              className="sortable fare-column"
            >
              Fare (£) {getSortIcon('fare')}
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedAndFilteredJourneys.length > 0 ? (
            sortedAndFilteredJourneys.map((journey, index) => (
              <tr key={journey.journey_id || index}>
                <td className="journey-id">#{journey.journey_id}</td>
                <td className="zone">Zone {journey.from_zone}</td>
                <td className="zone">Zone {journey.to_zone}</td>
                <td className="fare">£{journey.fare.toFixed(2)}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="4" className="no-results">
                No journeys match the filter criteria
              </td>
            </tr>
          )}
        </tbody>
        {sortedAndFilteredJourneys.length > 0 && (
          <tfoot>
            <tr className="total-row">
              <td colSpan="3" className="total-label">
                Filtered Total ({sortedAndFilteredJourneys.length} journeys):
              </td>
              <td className="total-fare">
                £{filteredTotal.toFixed(2)}
              </td>
            </tr>
          </tfoot>
        )}
      </table>
      
      {filters.operator && filters.value && (
        <div className="filter-info">
          <p>
            Showing journeys where fare {filters.operator} £{filters.value}
            {' '}({sortedAndFilteredJourneys.length} of {fareResponse.journeys.length} journeys)
          </p>
        </div>
      )}
    </div>
  );
};

export default FareTable;
