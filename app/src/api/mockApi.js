// Mock API layer — serves shared fixture JSONs with simulated latency.
// In Phase 2, swap each function body for real fetch() calls.

import recruiterResult from '@shared/fixtures/app.recruiter_result.json';
import placementDashboard from '@shared/fixtures/app.placement_dashboard.json';
import studentRegistrationFixture from '@shared/fixtures/app.requests.student_registration.json';
import jobSubmissionFixture from '@shared/fixtures/app.requests.job_submission.json';

// Simulated latency (300–800ms)
const delay = (ms) =>
  new Promise((resolve) => setTimeout(resolve, ms ?? 300 + Math.random() * 500));

// ── Student Registration ──
export async function registerStudent(payload) {
  await delay();
  // Validate required fields
  if (!payload.name || !payload.github_username) {
    throw new Error('Name and GitHub username are required.');
  }
  if (payload.consent !== true) {
    throw new Error('Consent is required to proceed.');
  }
  // Simulate success response with a generated student ID
  const id = 'S' + String(Math.floor(100 + Math.random() * 900));
  return {
    success: true,
    student_id: id,
    message: `Student ${payload.name} registered as ${id}. Ingestion pipeline triggered for @${payload.github_username}.`,
  };
}

// ── Job Submission ──
export async function submitJob(payload) {
  await delay();
  if (!payload.title || !payload.jd_text || !payload.registered_student_ids?.length) {
    throw new Error('Title, JD text, and at least one student ID are required.');
  }
  const id = 'J' + String(Math.floor(100 + Math.random() * 900));
  return {
    success: true,
    job_id: id,
    message: `Job "${payload.title}" submitted as ${id}. Pipeline running…`,
  };
}

// ── Recruiter Results (GET /jobs/{job_id}/results) ──
export async function getJobResults(jobId) {
  await delay();
  // Return fixture — in production, fetch from real backend
  return { ...recruiterResult, job_id: jobId || recruiterResult.job_id };
}

// ── Placement Dashboard (GET /placement/overview) ──
export async function getPlacementOverview() {
  await delay();
  return { ...placementDashboard };
}

// ── Fixture accessors (for pre-filling forms in demo mode) ──
export function getStudentRegistrationFixture() {
  return { ...studentRegistrationFixture };
}

export function getJobSubmissionFixture() {
  return { ...jobSubmissionFixture };
}
