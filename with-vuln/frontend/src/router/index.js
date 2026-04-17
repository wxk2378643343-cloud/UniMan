import { createRouter, createWebHistory } from "vue-router";
import AdminBaseDataView from "../views/AdminBaseDataView.vue";
import ComplaintsView from "../views/ComplaintsView.vue";
import DashboardView from "../views/DashboardView.vue";
import LoginView from "../views/LoginView.vue";
import NoticesView from "../views/NoticesView.vue";
import RepairsView from "../views/RepairsView.vue";
import RolesView from "../views/RolesView.vue";
import UserComplaintsView from "../views/UserComplaintsView.vue";
import UserHomeView from "../views/UserHomeView.vue";
import UserNoticesView from "../views/UserNoticesView.vue";
import UserRepairsView from "../views/UserRepairsView.vue";
import UsersView from "../views/UsersView.vue";
import { getRoleHome, getSession, isAdminRole } from "../auth";

const routes = [
  { path: "/", redirect: "/login" },
  { path: "/login", component: LoginView },
  { path: "/user/home", component: UserHomeView, meta: { requiresAuth: true, roles: ["普通用户"] } },
  { path: "/user/repairs", component: UserRepairsView, meta: { requiresAuth: true, roles: ["普通用户"] } },
  { path: "/user/complaints", component: UserComplaintsView, meta: { requiresAuth: true, roles: ["普通用户"] } },
  { path: "/user/notices", component: UserNoticesView, meta: { requiresAuth: true, roles: ["普通用户"] } },
  { path: "/admin/dashboard", component: DashboardView, meta: { requiresAuth: true, adminOnly: true } },
  { path: "/admin/repairs", component: RepairsView, meta: { requiresAuth: true, adminOnly: true } },
  { path: "/admin/complaints", component: ComplaintsView, meta: { requiresAuth: true, roles: ["系统管理员"] } },
  { path: "/admin/notices", component: NoticesView, meta: { requiresAuth: true, roles: ["系统管理员"] } },
  { path: "/admin/users", component: UsersView, meta: { requiresAuth: true, roles: ["系统管理员"] } },
  { path: "/admin/roles", component: RolesView, meta: { requiresAuth: true, roles: ["系统管理员"] } },
  { path: "/admin/base-data", component: AdminBaseDataView, meta: { requiresAuth: true, roles: ["系统管理员"] } }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to) => {
  const session = getSession();

  if (to.meta.requiresAuth && !session?.token) {
    return "/login";
  }

  if (to.path === "/login" && session?.token) {
    return getRoleHome(session.user.role);
  }

  if (!session?.token) {
    return true;
  }

  if (to.meta.adminOnly && !isAdminRole(session.user.role)) {
    return getRoleHome(session.user.role);
  }

  if (to.meta.roles && !to.meta.roles.includes(session.user.role)) {
    return getRoleHome(session.user.role);
  }

  return true;
});

export default router;
