import axios from "axios";

const http = axios.create({
  baseURL: "/api",
  timeout: 8000
});

export function login(data) {
  return http.post("/auth/login", data);
}

export function fetchOptions() {
  return http.get("/options");
}

export function fetchDashboard(role, userId) {
  return http.get("/dashboard/summary", {
    params: {
      role,
      user_id: userId
    }
  });
}

export function updateProfile(id, data) {
  return http.put(`/profile/${id}`, data);
}

export function uploadImage(file) {
  const formData = new FormData();
  formData.append("file", file);
  return http.post("/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });
}

export function fetchRepairs() {
  return http.get("/repairs");
}

export function createRepair(data) {
  return http.post("/repairs", data);
}

export function updateRepair(id, data) {
  return http.put(`/repairs/${id}`, data);
}

export function deleteRepair(id) {
  return http.delete(`/repairs/${id}`);
}

export function fetchComplaints() {
  return http.get("/complaints");
}

export function createComplaint(data) {
  return http.post("/complaints", data);
}

export function updateComplaint(id, data) {
  return http.put(`/complaints/${id}`, data);
}

export function deleteComplaint(id) {
  return http.delete(`/complaints/${id}`);
}

export function fetchNotices() {
  return http.get("/notices");
}

export function fetchUserNotices(role, userId) {
  return http.get("/notices", {
    params: {
      role,
      user_id: userId
    }
  });
}

export function markNoticeRead(id, userId) {
  return http.post(`/notices/${id}/read`, {
    user_id: userId
  });
}

export function createNotice(data) {
  return http.post("/notices", data);
}

export function updateNotice(id, data) {
  return http.put(`/notices/${id}`, data);
}

export function deleteNotice(id) {
  return http.delete(`/notices/${id}`);
}

export function fetchUsers() {
  return http.get("/users");
}

export function createUser(data) {
  return http.post("/users", data);
}

export function updateUser(id, data) {
  return http.put(`/users/${id}`, data);
}

export function deleteUser(id) {
  return http.delete(`/users/${id}`);
}

export function fetchRoles() {
  return http.get("/roles");
}

export function createRole(data) {
  return http.post("/roles", data);
}

export function updateRole(id, data) {
  return http.put(`/roles/${id}`, data);
}

export function deleteRole(id) {
  return http.delete(`/roles/${id}`);
}

export function fetchBaseData() {
  return http.get("/base-data");
}

export function createBaseData(data) {
  return http.post("/base-data", data);
}

export function updateBaseData(id, data) {
  return http.put(`/base-data/${id}`, data);
}

export function deleteBaseData(id) {
  return http.delete(`/base-data/${id}`);
}

export function fetchEvaluations() {
  return http.get("/evaluations");
}

export function createEvaluation(data) {
  return http.post("/evaluations", data);
}
