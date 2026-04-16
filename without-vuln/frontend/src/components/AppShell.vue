<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">U</div>
        <div>
          <p class="brand-title">UniMan</p>
          <p class="brand-subtitle">管理后台</p>
        </div>
      </div>

      <nav class="nav">
        <RouterLink v-for="item in items" :key="item.to" :to="item.to" class="nav-link">
          <span>{{ item.label }}</span>
          <small>{{ item.note }}</small>
        </RouterLink>
      </nav>
    </aside>

    <main class="content">
      <header class="topbar">
        <div>
          <p class="eyebrow">{{ eyebrow }}</p>
          <h1>{{ title }}</h1>
        </div>
        <div class="user-menu">
          <div class="user-pill">
            <span>{{ profile.display_name }}</span>
            <small>{{ profile.role }}</small>
          </div>
          <div class="user-dropdown">
            <button class="user-dropdown-item" @click="openProfile">编辑个人信息</button>
            <button class="user-dropdown-item danger-text" @click="logout">退出登录</button>
          </div>
        </div>
      </header>

      <slot />
    </main>
  </div>

  <div v-if="profileVisible" class="modal-mask" @click.self="closeProfile">
    <div class="modal-card modal-card-compact">
      <div class="modal-header">
        <h3>编辑个人信息</h3>
        <button class="modal-close" @click="closeProfile">×</button>
      </div>
      <form @submit.prevent="submitProfile">
        <div class="modal-body form-grid form-grid-2">
          <input v-model="profileForm.username" placeholder="用户名" disabled />
          <input v-model="profileForm.role" placeholder="角色" disabled />
          <input v-model="profileForm.display_name" placeholder="姓名" />
          <select v-model="profileForm.department">
            <option v-for="item in departmentOptions" :key="item">{{ item }}</option>
          </select>
          <input v-model="profileForm.password" type="password" placeholder="登录密码" />
          <input v-model="profileForm.status" placeholder="状态" disabled />
        </div>
        <div class="modal-footer">
          <button type="button" class="secondary-button" @click="closeProfile">取消</button>
          <button type="submit" class="primary-button">保存</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { updateUser } from "../api";

defineProps({
  title: {
    type: String,
    required: true
  },
  eyebrow: {
    type: String,
    default: "高校后勤服务管理系统"
  }
});

const allItems = [
  { to: "/dashboard", label: "总览看板", note: "业务态势" },
  { to: "/repairs", label: "报修工单", note: "服务处理" },
  { to: "/complaints", label: "投诉建议", note: "意见反馈" },
  { to: "/notices", label: "公告通知", note: "校园消息" },
  { to: "/users", label: "用户管理", note: "账号维护" },
  { to: "/roles", label: "角色管理", note: "权限配置" }
];

const router = useRouter();
const profileVisible = ref(false);
const departmentOptions = ["信息中心", "维修中心", "后勤保障处", "宿舍管理中心", "网信办", "计算机学院"];
const profile = reactive({
  id: Number(localStorage.getItem("userId") || 0),
  username: localStorage.getItem("username") || "",
  display_name: localStorage.getItem("displayName") || "未登录",
  role: localStorage.getItem("role") || "",
  department: localStorage.getItem("department") || "后勤保障处",
  status: localStorage.getItem("status") || "启用",
  password: ""
});

const profileForm = reactive({
  username: "",
  display_name: "",
  role: "",
  department: "",
  status: "",
  password: ""
});

const items = computed(() =>
  profile.role === "系统管理员"
    ? allItems
    : allItems.filter((item) => !["/users", "/roles"].includes(item.to))
);

function openProfile() {
  Object.assign(profileForm, profile);
  profileForm.password = "";
  profileVisible.value = true;
}

function closeProfile() {
  profileVisible.value = false;
}

async function submitProfile() {
  await updateUser(profile.id, {
    username: profileForm.username,
    password: profileForm.password,
    role: profile.role,
    display_name: profileForm.display_name,
    department: profileForm.department,
    status: profile.status
  });
  Object.assign(profile, {
    ...profile,
    display_name: profileForm.display_name,
    department: profileForm.department
  });
  localStorage.setItem("displayName", profile.display_name);
  localStorage.setItem("department", profile.department);
  profileForm.password = "";
  closeProfile();
}

function logout() {
  localStorage.clear();
  router.push("/login");
}
</script>
