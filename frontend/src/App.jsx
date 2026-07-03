import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./routes/ProtectedRoute";
import { RoleRoute } from "./routes/RoleRoute";

// Auth screens
import { LoginPage } from "./features/auth/LoginPage";
import { SignupPage } from "./features/auth/SignupPage";
import { OTPPage } from "./features/auth/OTPPage";
import { ForgotPasswordPage } from "./features/auth/ForgotPasswordPage";
import { ResetPasswordPage } from "./features/auth/ResetPasswordPage";

// Admin portal
import { AdminDashboard } from "./features/admin/AdminDashboard";
import { CompanyListPage } from "./features/admin/CompanyListPage";
import { UserListPage } from "./features/admin/UserListPage";
import { VideoListPage } from "./features/admin/VideoListPage";

// HR portal
import { HRDashboard } from "./features/hr/HRDashboard";
import { BulkUploadPage } from "./features/hr/BulkUploadPage";
import { TrainingAssignPage } from "./features/hr/TrainingAssignPage";
import { CompliancePage } from "./features/hr/CompliancePage";

// Employee portal
import { EmployeeDashboard } from "./features/employee/EmployeeDashboard";
import { CoursesPage } from "./features/employee/CoursesPage";
import { VideoPlayerPage } from "./features/employee/VideoPlayerPage";
import { AssessmentPage } from "./features/employee/AssessmentPage";
import { CertificatesPage } from "./features/employee/CertificatesPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/verify-otp" element={<OTPPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/" element={<Navigate to="/login" replace />} />

        {/* Admin portal — role 1 or 2 only */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1, 2]}>
                <AdminDashboard />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/companies"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1]}>
                <CompanyListPage />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1, 2]}>
                <UserListPage />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/videos"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1, 2]}>
                <VideoListPage />
              </RoleRoute>
            </ProtectedRoute>
          }
        />

        {/* HR portal — role 1, 2, or 3 */}
        <Route
          path="/hr"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1, 2, 3]}>
                <HRDashboard />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/hr/upload"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1, 2, 3]}>
                <BulkUploadPage />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/hr/assign"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1, 2, 3]}>
                <TrainingAssignPage />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/hr/compliance"
          element={
            <ProtectedRoute>
              <RoleRoute allowedRoles={[1, 2, 3]}>
                <CompliancePage />
              </RoleRoute>
            </ProtectedRoute>
          }
        />

        {/* Employee portal — all authenticated users */}
        <Route
          path="/employee"
          element={
            <ProtectedRoute>
              <EmployeeDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/employee/courses"
          element={
            <ProtectedRoute>
              <CoursesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/employee/video/:videoId"
          element={
            <ProtectedRoute>
              <VideoPlayerPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/employee/assessment/:videoId"
          element={
            <ProtectedRoute>
              <AssessmentPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/employee/certificates"
          element={
            <ProtectedRoute>
              <CertificatesPage />
            </ProtectedRoute>
          }
        />

        {/* Catch-all */}
        <Route path="/unauthorized" element={<div>Access Denied</div>} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
