import React, { useState, useCallback } from 'react';
import './App.css';
import JourneyForm from './components/JourneyForm';
import FareTable from './components/FareTable';
import FilterControls from './components/FilterControls';
import { calculateFares } from './services/api';

function App() {
  const [fareResponse, setFareResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({ operator: '', value: '' });

  const handleJourneysSubmit = useCallback(async (journeyList) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await calculateFares(journeyList);
      setFareResponse(response);
    } catch (err) {
      setError(err.message || 'Failed to calculate fares');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters);
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🚇 PearlCard Fare Calculator</h1>
        <p>Pearly City Metro System</p>
      </header>

      <main className="App-main">
        <div className="container">
          <div className="form-section">
            <h2>Enter Journeys</h2>
            <JourneyForm 
              onSubmit={handleJourneysSubmit}
              maxJourneys={20}
            />
          </div>

          {error && (
            <div className="error-message">
              <p>⚠️ {error}</p>
            </div>
          )}

          {loading && (
            <div className="loading">
              <p>Calculating fares...</p>
            </div>
          )}

          {fareResponse && !loading && (
            <>
              <div className="filter-section">
                <h2>Filter Results</h2>
                <FilterControls onFilterChange={handleFilterChange} />
              </div>

              <div className="results-section">
                <h2>Fare Calculation Results</h2>
                <FareTable 
                  fareResponse={fareResponse}
                  filters={filters}
                />
                
                <div className="summary">
                  <div className="summary-card">
                    <h3>Daily Summary</h3>
                    <div className="summary-item">
                      <span>Total Journeys:</span>
                      <strong>{fareResponse.journey_count}</strong>
                    </div>
                    <div className="summary-item total">
                      <span>Total Daily Fare:</span>
                      <strong className="fare-amount">
                        £{fareResponse.total_daily_fare.toFixed(2)}
                      </strong>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </main>

      <footer className="App-footer">
        <p>© 2025 Pearly City Transport Authority</p>
      </footer>
    </div>
  );
}

export default App;
