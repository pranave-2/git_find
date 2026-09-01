import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { submitJob, getJobSubmissionFixture } from '../api/mockApi';
import { useApi } from '../hooks/useApi';
import './Pages.css';

export default function JobSubmission() {
  const navigate = useNavigate();
  const { execute, loading, error, data } = useApi(submitJob);

  const [formData, setFormData] = useState({
    title: '',
    jd_text: '',
    registered_student_ids: 'S001, S002, S003',
    weight_required: 1.0,
    weight_preferred: 0.6,
    weight_bonus: 0.3,
  });

  const [validationError, setValidationError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setValidationError('');
  };

  const handlePrefill = () => {
    const fixture = getJobSubmissionFixture();
    setFormData({
      title: fixture.title,
      jd_text: fixture.jd_text,
      registered_student_ids: fixture.registered_student_ids.join(', '),
      weight_required: 1.0,
      weight_preferred: 0.6,
      weight_bonus: 0.3,
    });
    setValidationError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.jd_text.length < 20) {
      setValidationError('Job description text must be at least 20 characters.');
      return;
    }

    const studentIds = formData.registered_student_ids
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    if (studentIds.length === 0) {
      setValidationError('Please list at least one registered student ID.');
      return;
    }

    const payload = {
      title: formData.title,
      jd_text: formData.jd_text,
      registered_student_ids: studentIds,
      policy_overrides: {
        required: parseFloat(formData.weight_required),
        preferred: parseFloat(formData.weight_preferred),
        bonus: parseFloat(formData.weight_bonus),
      },
    };

    try {
      const res = await execute(payload);
      setTimeout(() => {
        navigate('/results');
      }, 1200);
    } catch {
      // handled by hook
    }
  };

  return (
    <div className="page-container">
      <div className="page-header animate-in">
        <h1>Submit Job Description</h1>
        <p>
          The raw JD goes straight to the Recruitment Genie Agent (Person D) for dynamic semantic interpretation & retrieval.
        </p>
      </div>

      <div className="grid-2">
        <div className="glass-card page-card animate-in stagger-1">
          <div className="card-header-flex">
            <h3>Job Details & Description</h3>
            <button type="button" className="btn btn-ghost btn-sm" onClick={handlePrefill}>
              ⚡ Prefill Demo JD
            </button>
          </div>

          <form onSubmit={handleSubmit} className="form-stack">
            <div className="form-group">
              <label className="form-label" htmlFor="title">
                Job Title *
              </label>
              <input
                id="title"
                type="text"
                name="title"
                className="form-input"
                placeholder="e.g. Backend Software Engineer"
                value={formData.title}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <div className="label-with-count">
                <label className="form-label" htmlFor="jd_text">
                  Unmodified Job Description Text *
                </label>
                <span className="char-count mono">
                  {formData.jd_text.length} / 20000 chars
                </span>
              </div>
              <textarea
                id="jd_text"
                name="jd_text"
                className="form-textarea"
                rows={7}
                placeholder="Paste full job description here... (e.g. We are looking for candidates with strong experience developing production-grade backend services using Python...)"
                value={formData.jd_text}
                onChange={handleChange}
                required
              />
              <span className="form-hint">
                No manual skill tagging needed — Genie interprets requirements (Required / Preferred / Bonus) directly from text.
              </span>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="registered_student_ids">
                Registered Student Candidate Pool (IDs) *
              </label>
              <input
                id="registered_student_ids"
                type="text"
                name="registered_student_ids"
                className="form-input mono"
                placeholder="S001, S002, S003"
                value={formData.registered_student_ids}
                onChange={handleChange}
                required
              />
              <span className="form-hint">
                Comma-separated student IDs in scope for retrieval.
              </span>
            </div>

            <div className="form-group">
              <label className="form-label">Requirement Scoring Policy Weights (Optional Overrides)</label>
              <div className="grid-3">
                <div>
                  <span className="form-hint">Required</span>
                  <input
                    type="number"
                    step="0.1"
                    name="weight_required"
                    className="form-input mono"
                    value={formData.weight_required}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <span className="form-hint">Preferred</span>
                  <input
                    type="number"
                    step="0.1"
                    name="weight_preferred"
                    className="form-input mono"
                    value={formData.weight_preferred}
                    onChange={handleChange}
                  />
                </div>
                <div>
                  <span className="form-hint">Bonus</span>
                  <input
                    type="number"
                    step="0.1"
                    name="weight_bonus"
                    className="form-input mono"
                    value={formData.weight_bonus}
                    onChange={handleChange}
                  />
                </div>
              </div>
            </div>

            {(validationError || error) && (
              <div className="toast toast-error">{validationError || error}</div>
            )}

            {data?.success && (
              <div className="toast toast-success">
                ✅ {data.message} Redirecting to candidate results…
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary btn-lg"
              disabled={loading}
            >
              {loading ? 'Executing Pipeline B...' : '✨ Submit JD to Recruitment Genie'}
            </button>
          </form>
        </div>

        <div className="glass-card page-card animate-in stagger-2 info-sidebar">
          <h3>How Pipeline B Executes</h3>
          <p className="info-intro">
            When a raw JD is submitted, the online recruitment pipeline executes:
          </p>

          <div className="pipeline-steps">
            <div className="pipeline-step">
              <span className="step-num">1</span>
              <div>
                <strong>Recruitment Genie Agent (Person D)</strong>
                <p>Maps natural-language requirements to canonical skills via synonyms, table relationships, & instructions. Generates retrieval SQL.</p>
              </div>
            </div>

            <div className="pipeline-step">
              <span className="step-num">2</span>
              <div>
                <strong>Deterministic Ranking Scorer (Person C)</strong>
                <p>Aggregates multi-repo skill evidence (MAX) and applies requirement weights (Required=1.0, Preferred=0.6, Bonus=0.3).</p>
              </div>
            </div>

            <div className="pipeline-step">
              <span className="step-num">3</span>
              <div>
                <strong>Databricks ai_summarize (Person D/E)</strong>
                <p>Generates evidence-backed narrative justification per candidate for the Recruiter Dashboard.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
