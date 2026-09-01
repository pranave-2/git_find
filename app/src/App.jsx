import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import StudentRegistration from './pages/StudentRegistration';
import JobSubmission from './pages/JobSubmission';
import RecruiterResults from './pages/RecruiterResults';
import PlacementDashboard from './pages/PlacementDashboard';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/results" replace />} />
          <Route path="register" element={<StudentRegistration />} />
          <Route path="jobs/new" element={<JobSubmission />} />
          <Route path="results" element={<RecruiterResults />} />
          <Route path="placement" element={<PlacementDashboard />} />
          <Route path="*" element={<Navigate to="/results" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
