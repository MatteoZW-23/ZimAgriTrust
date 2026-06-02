import React, { useEffect, useMemo, useState } from "react";
import { fetchAcademyModules, listApplications, completeTrainingModule } from "../api";

type AcademyManagementProps = {
  token: string;
};

type AcademyModule = {
  id?: string;
  module_id?: string;
  title?: string;
  name?: string;
  module_number?: number;
  order?: number;
  passing_score?: number;
  quiz_count?: number;
  question_count?: number;
};

type AgentApplication = {
  id: string;
  full_name?: string;
  name?: string;
  phone_number?: string;
  status?: string;
  training_modules_completed?: string[];
};

export default function AcademyManagement({ token }: AcademyManagementProps) {
  const [modules, setModules] = useState<AcademyModule[]>([]);
  const [applications, setApplications] = useState<AgentApplication[]>([]);
  const [selectedApplicationId, setSelectedApplicationId] = useState("");
  const [loading, setLoading] = useState(true);
  const [savingModule, setSavingModule] = useState<string | null>(null);
  const [error, setError] = useState("");

  const selectedApplication = useMemo(
    () => applications.find((application) => application.id === selectedApplicationId),
    [applications, selectedApplicationId],
  );

  const completedModules = selectedApplication?.training_modules_completed || [];

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    Promise.all([fetchAcademyModules(token), listApplications(token)])
      .then(([moduleData, applicationData]) => {
        if (!mounted) return;
        const normalizedModules = Array.isArray(moduleData) ? moduleData : moduleData?.modules || [];
        const normalizedApplications = Array.isArray(applicationData) ? applicationData : applicationData?.applications || [];
        setModules(normalizedModules);
        setApplications(normalizedApplications);
        setSelectedApplicationId((current) => current || normalizedApplications[0]?.id || "");
        setError("");
      })
      .catch((err) => setError(err?.message || "Unable to load academy data"))
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [token]);

  const refreshApplications = async () => {
    const data = await listApplications(token);
    setApplications(Array.isArray(data) ? data : data?.applications || []);
  };

  const markModuleComplete = async (moduleId: string) => {
    if (!selectedApplicationId || !moduleId) return;
    setSavingModule(moduleId);
    try {
      await completeTrainingModule(token, selectedApplicationId, moduleId);
      await refreshApplications();
      setError("");
    } catch (err: any) {
      setError(err?.message || "Unable to update training progress");
    } finally {
      setSavingModule(null);
    }
  };

  const progress = modules.length > 0 ? Math.round((completedModules.length / modules.length) * 100) : 0;

  return (
    <div className="v4-academy-dashboard">
      <div className="academy-header-flex">
        <div>
          <h1 className="academy-title">Training Academy</h1>
          <p className="academy-subtitle">Agent module progress and certification readiness</p>
        </div>
        <select
          value={selectedApplicationId}
          onChange={(event) => setSelectedApplicationId(event.target.value)}
          className="v4-input"
          style={{ maxWidth: 360 }}
        >
          {applications.map((application) => (
            <option key={application.id} value={application.id}>
              {application.full_name || application.name || application.phone_number || application.id}
            </option>
          ))}
        </select>
      </div>

      {error && <div className="v4-alert danger">{error}</div>}

      {loading ? (
        <div className="academy-welcome">Loading academy records...</div>
      ) : (
        <div className="academy-layout">
          <aside className="academy-sidebar">
            <div className="v4-glass-card-premium" style={{ padding: 24 }}>
              <p className="text-label">Selected Applicant</p>
              <h3 style={{ margin: "8px 0", color: "var(--v4-text)" }}>
                {selectedApplication?.full_name || selectedApplication?.name || "No applicant selected"}
              </h3>
              <p style={{ color: "var(--v4-text-dim)", margin: 0 }}>{selectedApplication?.status || "No status"}</p>
              <div className="p-bar-v4" style={{ marginTop: 20 }}>
                <div className="p-fill" style={{ width: `${Math.min(100, progress)}%` }} />
              </div>
              <p className="p-count" style={{ marginTop: 10 }}>
                {completedModules.length}/{modules.length} modules complete
              </p>
            </div>
          </aside>

          <section className="academy-main">
            {modules.length === 0 ? (
              <div className="academy-welcome">No training modules are configured.</div>
            ) : (
              <div className="v4-table-wrapper">
                <table className="v4-table">
                  <thead>
                    <tr>
                      <th>Module</th>
                      <th>Questions</th>
                      <th>Passing Score</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {modules.map((module, index) => {
                      const moduleId = module.module_id || module.id || `M${module.module_number || module.order || index + 1}`;
                      const title = module.title || module.name || `Module ${module.module_number || module.order || index + 1}`;
                      const complete = completedModules.includes(moduleId);
                      return (
                        <tr key={moduleId}>
                          <td>
                            <strong>{title}</strong>
                            <span>{moduleId}</span>
                          </td>
                          <td>{module.question_count || module.quiz_count || 0}</td>
                          <td>{module.passing_score || 80}%</td>
                          <td>
                            <span className={`status-pill ${complete ? "success" : "pending"}`}>
                              {complete ? "Complete" : "Pending"}
                            </span>
                          </td>
                          <td>
                            <button
                              className="v4-btn v4-btn-primary"
                              disabled={complete || !selectedApplicationId || savingModule === moduleId}
                              onClick={() => markModuleComplete(moduleId)}
                            >
                              {savingModule === moduleId ? "Saving..." : complete ? "Completed" : "Mark Complete"}
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
