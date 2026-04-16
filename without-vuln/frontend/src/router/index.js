import { createRouter, createWebHistory } from "vue-router";
import ComplaintsView from "../views/ComplaintsView.vue";
import DashboardView from "../views/DashboardView.vue";
import LoginView from "../views/LoginView.vue";
import NoticesView from "../views/NoticesView.vue";
import RepairsView from "../views/RepairsView.vue";
import RolesView from "../views/RolesView.vue";
import UsersView from "../views/UsersView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/login" },
    { path: "/login", component: LoginView },
    { path: "/dashboard", component: DashboardView, meta: { requiresAuth: true } },
    { path: "/repairs", component: RepairsView, meta: { requiresAuth: true } },
    { path: "/complaints", component: ComplaintsView, meta: { requiresAuth: true } },
    { path: "/notices", component: NoticesView, meta: { requiresAuth: true } },
    { path: "/users", component: UsersView, meta: { requiresAuth: true, roles: ["系统管理员"] } },
    { path: "/roles", component: RolesView, meta: { requiresAuth: true, roles: ["系统管理员"] } }
  ]
});

router.beforeEach((to) => {
  const token = localStorage.getItem("token");
  const role = localStorage.getItem("role");

  if (to.meta.requiresAuth && !token) {
    return "/login";
  }

  if (to.path === "/login" && token) {
    return "/dashboard";
  }

  if (to.meta.roles && !to.meta.roles.includes(role)) {
    return "/dashboard";
  }

  return true;
});

export default router;
