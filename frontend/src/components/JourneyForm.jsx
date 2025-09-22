import React, { useState, useCallback, useEffect } from 'react';
import { getFareRules } from '../services/api';
import './JourneyForm.css';

const JourneyForm = ({ onSubmit, maxJourneys = 20 }) => {
  const [journeys, setJourneys] = useState([{ from_zone: '', to_zone: '' }]);
  const [errors, setErrors] = useState({});
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch available zones from API
  useEffect(() => {
    const fetchZones = async () => {
      try {
        const data = await getFareRules();
        setZones(data.available_zones || []);
        setMaxJourneys(data.max_journeys_per_day || 20);
      } catch (error) {
        console.error('Failed to fetch zones:', error);
        // Don't set fallback zones - show error instead
        setErrors({ general: 'Failed to load zones. Please refresh the page.' });
      } finally {
        setLoading(false);
      }
    };
    
    fetchZones();
  }, []);

  const [maxJourneysLimit, setMaxJourneys] = useState(maxJourneys);

  const handleJourneyChange = useCallback((index, field, value) => {
    const newJourneys = [...journeys];
    newJourneys[index][field] = value ? parseInt(value, 10) : '';
    setJourneys(newJourneys);
    
    // Clear error for this field
    const newErrors = { ...errors };
    delete newErrors[`${index}-${field}`];
    setErrors(newErrors);
  }, [journeys, errors]);

  const addJourney = useCallback(() => {
    if (journeys.length < maxJourneysLimit) {
      setJourneys([...journeys, { from_zone: '', to_zone: '' }]);
    }
  }, [journeys, maxJourneysLimit]);

  const removeJourney = useCallback((index) => {
    if (journeys.length > 1) {
      const newJourneys = journeys.filter((_, i) => i !== index);
      setJourneys(newJourneys);
    }
  }, [journeys]);

  const validateForm = useCallback(() => {
    const newErrors = {};
    let isValid = true;

    journeys.forEach((journey, index) => {
      if (!journey.from_zone) {
        newErrors[`${index}-from_zone`] = 'From zone is required';
        isValid = false;
      }
      if (!journey.to_zone) {
        newErrors[`${index}-to_zone`] = 'To zone is required';
        isValid = false;
      }
    });

    setErrors(newErrors);
    return isValid;
  }, [journeys]);

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    
    if (validateForm()) {
      // Filter out empty journeys
      const validJourneys = journeys.filter(
        j => j.from_zone && j.to_zone
      );
      onSubmit(validJourneys);
    }
  }, [journeys, validateForm, onSubmit]);

  const clearForm = useCallback(() => {
    setJourneys([{ from_zone: '', to_zone: '' }]);
    setErrors({});
  }, []);

  if (loading) {
    return <div className="loading">Loading zones...</div>;
  }

  if (errors.general) {
    return <div className="error-message">{errors.general}</div>;
  }

  if (!zones || zones.length === 0) {
    return <div className="error-message">No zones available. Please contact support.</div>;
  }

  return (
    <form className="journey-form" onSubmit={handleSubmit}>
      <div className="journeys-list">
        {journeys.map((journey, index) => (
          <div key={index} className="journey-item">
            <div className="journey-number">#{index + 1}</div>
            
            <div className="journey-fields">
              <div className="field-group">
                <label>From Zone:</label>
                <select
                  value={journey.from_zone}
                  onChange={(e) => handleJourneyChange(index, 'from_zone', e.target.value)}
                  className={errors[`${index}-from_zone`] ? 'error' : ''}
                >
                  <option value="">Select</option>
                  {zones.map(zone => (
                    <option key={zone} value={zone}>Zone {zone}</option>
                  ))}
                </select>
                {errors[`${index}-from_zone`] && (
                  <span className="error-text">{errors[`${index}-from_zone`]}</span>
                )}
              </div>

              <div className="field-group">
                <label>To Zone:</label>
                <select
                  value={journey.to_zone}
                  onChange={(e) => handleJourneyChange(index, 'to_zone', e.target.value)}
                  className={errors[`${index}-to_zone`] ? 'error' : ''}
                >
                  <option value="">Select</option>
                  {zones.map(zone => (
                    <option key={zone} value={zone}>Zone {zone}</option>
                  ))}
                </select>
                {errors[`${index}-to_zone`] && (
                  <span className="error-text">{errors[`${index}-to_zone`]}</span>
                )}
              </div>

              <button
                type="button"
                onClick={() => removeJourney(index)}
                className="btn-remove"
                disabled={journeys.length === 1}
                title="Remove journey"
              >
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="form-actions">
        <button
          type="button"
          onClick={addJourney}
          className="btn-add"
          disabled={journeys.length >= maxJourneysLimit}
        >
          + Add Journey ({journeys.length}/{maxJourneysLimit})
        </button>

        <div className="action-buttons">
          <button
            type="button"
            onClick={clearForm}
            className="btn-clear"
          >
            Clear All
          </button>
          <button
            type="submit"
            className="btn-submit"
          >
            Calculate Fares
          </button>
        </div>
      </div>
    </form>
  );
};

export default JourneyForm;
