<template>
  <div class="app-shell theme-admin">
    <aside class="shell-sidebar">
      <div class="sidebar-top">
        <div class="brand-block">
          <div class="brand-mark">{{ roleMark }}</div>
          <div>
            <p class="brand-title">UniMan</p>
            <p class="brand-subtitle">{{ roleSubtitle }}</p>
          </div>
        </div>
        <div class="sidebar-role-pill">{{ currentUser.role }}</div>
      </div>

      <div class="sidebar-section">
        <p class="sidebar-section-label">工作导航</p>
        <nav class="shell-nav">
          <RouterLink v-for="item in menus" :key="item.to" :to="item.to" class="nav-item">
            <span class="nav-accent"></span>
            <div class="nav-copy">
              <strong>{{ item.label }}</strong>
              <span>{{ item.note }}</span>
            </div>
          </RouterLink>
        </nav>
      </div>

      <div class="sidebar-note">
        <span class="sidebar-note-label">当前账号</span>
        <strong>{{ currentUser.name }}</strong>
        <p>{{ currentUser.department }}</p>
        <small>{{ currentUser.role }}</small>
      </div>
    </aside>

    <main class="shell-main">
      <header class="shell-topbar">
        <div class="shell-topbar-inner">
          <div>
            <p class="eyebrow">{{ eyebrow }}</p>
            <h1>{{ title }}</h1>
          </div>
          <div class="topbar-actions">
            <div class="user-dropdown">
              <button class="avatar-button" type="button">
                <span class="avatar-badge">
                  <span class="avatar-circle">{{ userInitial }}</span>
                  <span class="avatar-meta">
                    <strong>{{ currentUser.name }}</strong>
                    <small>{{ currentUser.role }}</small>
                  </span>
                  <span class="avatar-caret">▾</span>
                </span>
              </button>
              <div class="user-dropdown-menu">
                <div class="user-dropdown-summary">
                  <span class="avatar-circle avatar-circle-small">{{ userInitial }}</span>
                  <div>
                    <strong>{{ currentUser.name }}</strong>
                    <small>{{ currentUser.department }}</small>
                  </div>
                </div>
                <button class="user-dropdown-item" type="button" @click="openProfile">个人信息</button>
                <button class="user-dropdown-item" type="button" @click="openPassword">修改密码</button>
                <button class="user-dropdown-item danger-text" type="button" @click="logout">退出登录</button>
              </div>
            </div>
          </div>
        </div>
      </header>
      <div class="shell-content">
        <slot />
      </div>
    </main>
  </div>

  <div v-if="profileVisible" class="modal-mask" @click.self="closeProfile">
    <div class="modal-card modal-card-compact">
      <div class="modal-header">
        <h3>个人中心</h3>
        <button class="modal-close" @click="closeProfile">×</button>
      </div>
      <form @submit.prevent="submitProfile">
        <div class="modal-body form-grid form-grid-2">
          <div class="field-block">
            <span class="field-label">登录账号</span>
            <input :value="currentUser.username" disabled />
          </div>
          <div class="field-block">
            <span class="field-label">角色</span>
            <input :value="currentUser.role" disabled />
          </div>
          <div class="field-block">
            <span class="field-label">姓名</span>
            <input v-model="profileForm.name" />
          </div>
          <div class="field-block">
            <span class="field-label">联系方式</span>
            <input v-model="profileForm.phone" />
          </div>
          <div class="field-block">
            <span class="field-label">邮箱</span>
            <input v-model="profileForm.email" />
          </div>
          <div class="field-block">
            <span class="field-label">所属院系/部门</span>
            <select v-model="profileForm.department">
              <option v-for="item in departments" :key="item">{{ item }}</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="secondary-button" @click="closeProfile">取消</button>
          <button type="submit" class="primary-button">保存</button>
        </div>
      </form>
    </div>
  </div>

  <div v-if="passwordVisible" class="modal-mask" @click.self="closePassword">
    <div class="modal-card modal-card-compact">
      <div class="modal-header">
        <h3>修改密码</h3>
        <button class="modal-close" @click="closePassword">×</button>
      </div>
      <form @submit.prevent="submitPassword">
        <div class="modal-body form-grid">
          <div class="field-block">
            <span class="field-label">当前密码</span>
            <input v-model="passwordForm.current_password" type="password" />
          </div>
          <div class="field-block">
            <span class="field-label">新密码</span>
            <input v-model="passwordForm.next_password" type="password" />
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="secondary-button" @click="closePassword">取消</button>
          <button type="submit" class="primary-button">保存</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { clearSession, getSession, setSession } from "../auth";
import { updatePassword, updateProfile } from "../api";

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  eyebrow: {
    type: String,
    default: "高校后勤服务管理系统"
  }
});

const router = useRouter();
const session = getSession();
const currentUser = reactive({
  ...session.user
});
const profileVisible = ref(false);
const passwordVisible = ref(false);
const departments = ["信息中心", "维修中心", "后勤保障处", "计算机学院", "外国语学院"];
const profileForm = reactive({
  name: currentUser.name,
  phone: currentUser.phone,
  email: currentUser.email,
  department: currentUser.department
});
const passwordForm = reactive({
  current_password: "",
  next_password: ""
});

const userInitial = computed(() => (currentUser.name || currentUser.username || "U").slice(0, 1).toUpperCase());
const roleMark = computed(() => (currentUser.role === "系统管理员" ? "A" : "W"));
const roleSubtitle = computed(() => (currentUser.role === "系统管理员" ? "系统管理后台" : "维修人员工作台"));
const menus = computed(() => {
  const workerMenus = [
    { to: "/admin/dashboard", label: "总览看板", note: "今日工单态势" },
    { to: "/admin/repairs", label: "报修管理", note: "确认、处理与退回" }
  ];

  const adminMenus = [
    { to: "/admin/dashboard", label: "总览看板", note: "统计与态势" },
    { to: "/admin/repairs", label: "报修管理", note: "分派与处理跟踪" },
    { to: "/admin/complaints", label: "投诉建议", note: "统一处理回复" },
    { to: "/admin/notices", label: "公告管理", note: "发布维护" }
  ];

  if (currentUser.role === "系统管理员") {
    return [
      ...adminMenus,
      { to: "/admin/users", label: "用户管理", note: "账号维护" },
      { to: "/admin/roles", label: "角色管理", note: "角色配置" },
      { to: "/admin/base-data", label: "基础数据", note: "下拉项维护" }
    ];
  }

  return workerMenus;
});

function openProfile() {
  Object.assign(profileForm, {
    name: currentUser.name,
    phone: currentUser.phone,
    email: currentUser.email,
    department: currentUser.department
  });
  profileVisible.value = true;
}

function closeProfile() {
  profileVisible.value = false;
}

function openPassword() {
  Object.assign(passwordForm, {
    current_password: "",
    next_password: ""
  });
  passwordVisible.value = true;
}

function closePassword() {
  passwordVisible.value = false;
}

async function submitProfile() {
  await updateProfile(currentUser.id, profileForm);
  Object.assign(currentUser, profileForm);
  setSession({
    ...session,
    user: {
      ...session.user,
      ...profileForm
    }
  });
  closeProfile();
}

async function submitPassword() {
  await updatePassword(currentUser.id, passwordForm);
  closePassword();
}

function logout() {
  clearSession();
  router.push("/login");
}
</script>
