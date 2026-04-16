import axios from "axios";

const http = axios.create({
  baseURL: "/api",
  timeout: 5000
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.clear();
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export function login(data) {
  return http.post("/auth/login", data);
}

export function fetchDashboard() {
  return http.get("/dashboard/summary");
}

export function fetchRepairs() {
  return http.get("/repairs");
}

export function createRepair(data) {
  return http.post("/repairs", data);
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

export function fetchNotices() {
  return http.get("/notices");
}

export function createNotice(data) {
  return http.post("/notices", data);
}

export function updateRepair(id, data) {
  return http.put(`/repairs/${id}`, data);
}

export function updateNotice(id, data) {
  return http.put(`/notices/${id}`, data);
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

export function fetchUsers() {
  return http.get("/users");
}

export function createUser(data) {
  return http.post("/users", data);
}

export function updateUser(id, data) {
  return http.put(`/users/${id}`, data);
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
