const STORAGE_KEY = "uniman-session";

export function getSession() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
  } catch {
    return null;
  }
}

export function setSession(session) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearSession() {
  localStorage.removeItem(STORAGE_KEY);
}

export function getRoleHome(role) {
  return role === "普通用户" ? "/user/home" : "/admin/dashboard";
}

export function isAdminRole(role) {
  return role === "系统管理员" || role === "后勤人员";
}

export function getToken() {
  return getSession()?.token || "";
}
