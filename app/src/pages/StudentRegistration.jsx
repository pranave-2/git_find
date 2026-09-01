import React, { useState } from 'react';
import { registerStudent, getStudentRegistrationFixture } from '../api/mockApi';
import { useApi } from '../hooks/useApi';
import './Pages.css';

export default function StudentRegistration() {
  const { execute, loading, error, data } = useApi(registerStudent);

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    github_username: '',
    consent: false,
    repo_urls: '',
  });

  const [validationError, setValidationError] = useState('');

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    setValidationError('');
  };

  const handlePrefill = () => {
    const fixture = getStudentRegistrationFixture();
    setFormData({
      name: fixture.name,
      email: fixture.email || 'rahul@example.edu',
      github_username: fixture.github_username,
      consent: fixture.consent,
      repo_urls: 'https://github.com/rahul-dev/ecommerce-api\nhttps://github.com/rahul-dev/ml-price-predictor\nhttps://github.com/rahul-dev/chatbot',
    });
    setValidationError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // GitHub username regex validation per contract
    const ghRegex = /^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$/;
    if (!ghRegex.test(formData.github_username)) {
      setValidationError(
        'Invalid GitHub username. Must be 1-39 alphanumeric chars or single internal hyphens.'
      );
      return;
    }

    if (!formData.consent) {
      setValidationError('You must grant consent to analyze public repositories.');
      return;
    }

    const payload = {
      name: formData.name,
      email: formData.email || undefined,
      github_username: formData.github_username,
      consent: formData.consent,
      repo_urls: formData.repo_urls
        ? formData.repo_urls.split('\n').filter((u) => u.trim().length > 0)
        : undefined,
    };

    try {
      await execute(payload);
    } catch {
      // handled by hook
    }
  };

  return (
    <div className="page-container">
      <div className="page-header animate-in">
        <h1>Student Registration</h1>
        <p>Register your GitHub account to trigger continuous knowledge ingestion for Pipeline A.</p>
      </div>

      <div className="grid-2">
        <div className="glass-card page-card animate-in stagger-1">
          <div className="card-header-flex">
            <h3>Candidate Information</h3>
            <button type="button" className="btn btn-ghost btn-sm" onClick={handlePrefill}>
              ⚡ Prefill Demo Data
            </button>
          </div>

          <form onSubmit={handleSubmit} className="form-stack">
            <div className="form-group">
              <label className="form-label" htmlFor="name">
                Full Name *
              </label>
              <input
                id="name"
                type="text"
                name="name"
                className="form-input"
                placeholder="e.g. Rahul Sharma"
                value={formData.name}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="email">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                name="email"
                className="form-input"
                placeholder="rahul@university.edu"
                value={formData.email}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="github_username">
                GitHub Username *
              </label>
              <input
                id="github_username"
                type="text"
                name="github_username"
                className="form-input mono"
                placeholder="e.g. rahul-dev"
                value={formData.github_username}
                onChange={handleChange}
                required
              />
              <span className="form-hint">Must be an active public GitHub profile.</span>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="repo_urls">
                Specific Repositories (Optional, 1 per line)
              </label>
              <textarea
                id="repo_urls"
                name="repo_urls"
                className="form-textarea mono"
                rows={3}
                placeholder="https://github.com/rahul-dev/ecommerce-api"
                value={formData.repo_urls}
                onChange={handleChange}
              />
              <span className="form-hint">
                If omitted, GitHub REST API will automatically enumerate all public repos.
              </span>
            </div>

            <div className="form-group">
              <label className="checkbox-wrapper">
                <input
                  type="checkbox"
                  name="consent"
                  checked={formData.consent}
                  onChange={handleChange}
                />
                <span>
                  I consent to automated static analysis and skill extraction from my public GitHub repositories.
                </span>
              </label>
            </div>

            {(validationError || error) && (
              <div className="toast toast-error">{validationError || error}</div>
            )}

            {data?.success && (
              <div className="toast toast-success">
                ✅ {data.message}
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary btn-lg"
              disabled={loading}
            >
              {loading ? 'Processing Registration...' : '🚀 Register & Ingest Repositories'}
            </button>
          </form>
        </div>

        <div className="glass-card page-card animate-in stagger-2 info-sidebar">
          <h3>How Pipeline A Works</h3>
          <p className="info-intro">
            When you register, Recruitment Genie continuously maintains your candidate knowledge base:
          </p>

          <div className="pipeline-steps">
            <div className="pipeline-step">
              <span className="step-num">1</span>
              <div>
                <strong>GitHub Ingestion (Person A)</strong>
                <p>Fetches public repos, computes language breakdown, extracts dependencies and code signals.</p>
              </div>
            </div>

            <div className="pipeline-step">
              <span className="step-num">2</span>
              <div>
                <strong>Gemini Evidence Extraction (Person B)</strong>
                <p>Prompts Gemini for repo summaries, candidate skill lists, and natural-language evidence.</p>
              </div>
            </div>

            <div className="pipeline-step">
              <span className="step-num">3</span>
              <div>
                <strong>Deterministic Evidence Scorer (Person C)</strong>
                <p>Combines 6 observable signals into a weighted Evidence Score stored in REPOSITORY_SKILL.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
