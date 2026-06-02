import React, { useEffect, useMemo, useState } from "react";
import {
  acceptTask,
  confirmDeliveryByAgent,
  confirmPickup,
  getDeliveryStatus,
  getMyTasks,
  markDeliveryArrived,
  markPickupInProgress,
  rejectTask,
} from "../api.ts";

function normalizeTaskStatus(status) {
  const value = String(status || "").toLowerCase();
  if (value === "assigned") return "pending";
  return value || "pending";
}

function badgeClass(status) {
  return (
    {
      pending: "badge-yellow",
      accepted: "badge-green",
      completed: "badge-green",
      rejected: "badge-red",
    }[normalizeTaskStatus(status)] || "badge-gray"
  );
}

export default function DeliveryPanel() {
  const [tasks, setTasks] = useState(null);
  const [tracking, setTracking] = useState(null);
  const [activeTask, setActiveTask] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const loadTasks = async () => {
    try {
      const rows = await getMyTasks();
      setTasks(Array.isArray(rows) ? rows : []);
    } catch {
      setTasks([]);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const deliveryTasks = useMemo(() => {
    if (!Array.isArray(tasks)) return [];
    return tasks.filter((task) => {
      if (!task?.order_id) return false;
      const type = String(task.assignment_type || "").toLowerCase();
      return type.includes("order") || type.includes("delivery") || type.includes("fulfillment");
    });
  }, [tasks]);

  const openTrack = async (task) => {
    if (!task?.order_id) return;
    setLoading(true);
    try {
      setActiveTask(task);
      setTracking(await getDeliveryStatus(task.order_id));
    } catch (e) {
      alert("No delivery info yet. Order may not have logistics set up.");
    } finally {
      setLoading(false);
    }
  };

  const handleTaskAccept = async (taskId) => {
    setLoading(true);
    try {
      await acceptTask(taskId);
      setMsg("Delivery assignment accepted.");
      await loadTasks();
    } catch (e) {
      setMsg(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTaskReject = async (taskId) => {
    const reason = prompt("Reason for rejecting this delivery assignment:");
    if (!reason) return;
    setLoading(true);
    try {
      await rejectTask(taskId, reason);
      setMsg("Delivery assignment rejected.");
      if (activeTask?.id === taskId) {
        setActiveTask(null);
        setTracking(null);
      }
      await loadTasks();
    } catch (e) {
      setMsg(e.message);
    } finally {
      setLoading(false);
    }
  };

  const action = async (fn, label) => {
    if (!tracking?.order_id) return;
    setLoading(true);
    try {
      await fn(tracking.order_id);
      setMsg(`${label} done!`);
      setTracking(await getDeliveryStatus(tracking.order_id));
      await loadTasks();
    } catch (e) {
      setMsg(e.message);
    } finally {
      setLoading(false);
    }
  };

  const steps = ["PENDING", "METHOD_SET", "PICKUP_IN_PROGRESS", "IN_TRANSIT", "ARRIVED", "DELIVERED"];
  const stepIdx = tracking ? steps.indexOf(tracking.status) : -1;
  const selectedTaskStatus = normalizeTaskStatus(activeTask?.status);

  return (
    <div>
      <h2 className="page-title">Delivery Controls</h2>
      <p className="page-sub">Manage only the logistics work assigned to your agent account</p>
      {msg && (
        <div className="alert alert-info" onClick={() => setMsg("")}>
          {msg}
        </div>
      )}

      {tasks === null ? (
        <p>Loading...</p>
      ) : deliveryTasks.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">
            <i className="fas fa-truck"></i>
          </div>
          <h3>No delivery assignments</h3>
          <p style={{ color: "var(--text-dim)" }}>
            Accepted crop delivery work will appear here once it is assigned to you.
          </p>
        </div>
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Assignment</th>
                  <th>Order ID</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Deadline</th>
                  <th>Delivery</th>
                </tr>
              </thead>
              <tbody>
                {deliveryTasks.map((task) => {
                  const normalizedStatus = normalizeTaskStatus(task.status);
                  return (
                    <tr key={task.id}>
                      <td style={{ fontFamily: "monospace", fontSize: 11 }}>{task.id?.slice(0, 8)}...</td>
                      <td style={{ fontFamily: "monospace", fontSize: 11 }}>{task.order_id?.slice(0, 8)}...</td>
                      <td>{String(task.assignment_type || "delivery").replace(/_/g, " ")}</td>
                      <td>
                        <span className={`badge ${badgeClass(task.status)}`}>{normalizedStatus}</span>
                      </td>
                      <td style={{ fontSize: 11 }}>
                        {task.deadline ? new Date(task.deadline).toLocaleString() : "—"}
                      </td>
                      <td>
                        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                          {normalizedStatus === "pending" && (
                            <>
                              <button
                                className="btn btn-sm btn-primary"
                                onClick={() => handleTaskAccept(task.id)}
                                disabled={loading}
                              >
                                Accept
                              </button>
                              <button
                                className="btn btn-sm btn-danger"
                                onClick={() => handleTaskReject(task.id)}
                                disabled={loading}
                              >
                                Reject
                              </button>
                            </>
                          )}
                          {normalizedStatus === "accepted" && (
                            <button
                              className="btn btn-sm btn-ghost"
                              onClick={() => openTrack(task)}
                              disabled={loading}
                            >
                              <i className="fas fa-cog"></i> Manage
                            </button>
                          )}
                          {normalizedStatus === "completed" && (
                            <button
                              className="btn btn-sm btn-ghost"
                              onClick={() => openTrack(task)}
                              disabled={loading}
                            >
                              <i className="fas fa-eye"></i> View
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tracking && (
        <div className="modal-overlay" onClick={() => setTracking(null)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 480 }}>
            <button
              className="modal-close"
              onClick={() => {
                setTracking(null);
                setActiveTask(null);
              }}
            >
              &times;
            </button>
            <div className="modal-title">Delivery Management</div>
            <div className="modal-sub">
              Assignment: <strong>{selectedTaskStatus}</strong>
              <br />
              Logistics status: <strong>{tracking.status}</strong>
            </div>

            {selectedTaskStatus !== "accepted" ? (
              <div className="alert alert-info" style={{ marginTop: 16 }}>
                This assignment must be accepted before delivery actions can be recorded.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 16 }}>
                {[
                  {
                    label: "Mark Pickup In Progress",
                    fn: () => action(markPickupInProgress, "Pickup started"),
                    show: stepIdx <= 1,
                  },
                  {
                    label: "Confirm Goods Collected",
                    fn: () => action((id) => confirmPickup(id, { gps_verified: true }), "Pickup confirmed"),
                    show: stepIdx === 2,
                  },
                  {
                    label: "Mark Arrived at Destination",
                    fn: () => action(markDeliveryArrived, "Arrival confirmed"),
                    show: stepIdx === 3,
                  },
                  {
                    label: "Confirm Delivery Complete",
                    fn: () => action((id) => confirmDeliveryByAgent(id, { gps_verified: true }), "Delivery confirmed"),
                    show: stepIdx === 4,
                  },
                ]
                  .filter((button) => button.show)
                  .map((button) => (
                    <button key={button.label} className="btn btn-primary" onClick={button.fn} disabled={loading}>
                      {button.label}
                    </button>
                  ))}
              </div>
            )}

            <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 16 }}>
              Driver: {tracking.driver_name || "Not assigned"} · ETA:{" "}
              {tracking.estimated_arrival_at ? new Date(tracking.estimated_arrival_at).toLocaleString() : "TBD"}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
