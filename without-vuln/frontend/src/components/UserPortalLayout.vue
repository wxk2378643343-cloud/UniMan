<template>
  <div class="user-portal">
    <header class="portal-header">
      <div class="portal-header-bar">
        <RouterLink to="/user/home" class="portal-brand">
          <span class="portal-brand-mark">U</span>
          <span>
            <strong>UniMan</strong>
            <small>校园后勤服务门户</small>
          </span>
        </RouterLink>

        <nav class="portal-nav">
          <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="portal-nav-link">
            <span>{{ item.label }}</span>
            <span v-if="item.to === '/user/notices' && unreadNoticeCount > 0" class="portal-nav-badge">
              {{ unreadNoticeCount > 99 ? "99+" : unreadNoticeCount }}
            </span>
          </RouterLink>
        </nav>

        <div class="portal-user-actions">
          <div class="user-dropdown">
            <button class="portal-profile-button" type="button">
              <span class="avatar-circle">{{ userInitial }}</span>
              <span class="portal-profile-meta">
                <strong>{{ currentUser.name }}</strong>
                <small>{{ currentUser.department }}</small>
              </span>
            </button>
            <div class="user-dropdown-menu">
              <button class="user-dropdown-item" type="button" @click="openProfile">个人信息</button>
              <button class="user-dropdown-item" type="button" @click="openPassword">修改密码</button>
              <button class="user-dropdown-item danger-text" type="button" @click="logout">退出登录</button>
            </div>
          </div>
        </div>
      </div>
    </header>

    <main class="portal-main">
      <section class="portal-hero-card">
        <div class="portal-hero-copy">
          <p class="eyebrow">用户服务门户</p>
          <h1>{{ title }}</h1>
          <p>{{ description }}</p>
        </div>
        <div class="portal-hero-side">
          <slot name="hero-aside">
            <article class="portal-hero-panel">
              <span>当前账号</span>
              <strong>{{ currentUser.name }}</strong>
              <small>{{ currentUser.role }} · {{ currentUser.department }}</small>
            </article>
          </slot>
        </div>
      </section>

      <section class="portal-content">
        <slot />
      </section>
    </main>
  </div>

  <div v-if="profileVisible" class="modal-mask" @click.self="closeProfile">
    <div class="modal-card modal-card-compact">
      <div class="modal-header">
        <h3>个人信息</h3>
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
            <input v-model="passwordForm.currentPassword" type="password" />
          </div>
          <div class="field-block">
            <span class="field-label">新密码</span>
            <input v-model="passwordForm.nextPassword" type="password" />
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
import { computed, onMounted, reactive, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { clearSession, getSession, setSession } from "../auth";
import { fetchUserNotices, updatePassword, updateProfile } from "../api";

defineProps({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ""
  }
});

const router = useRouter();
const session = getSession();
const currentUser = reactive({
  ...session.user
});
const navItems = [
  { to: "/user/home", label: "首页" },
  { to: "/user/repairs", label: "我的报修" },
  { to: "/user/complaints", label: "投诉建议" },
  { to: "/user/notices", label: "公告通知" }
];
const profileVisible = ref(false);
const passwordVisible = ref(false);
const unreadNoticeCount = ref(0);
const departments = ["信息中心", "维修中心", "后勤保障处", "计算机学院", "外国语学院"];
const profileForm = reactive({
  name: currentUser.name,
  phone: currentUser.phone,
  email: currentUser.email,
  department: currentUser.department
});
const passwordForm = reactive({
  currentPassword: "",
  nextPassword: ""
});

const userInitial = computed(() => (currentUser.name || currentUser.username || "U").slice(0, 1).toUpperCase());

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
    currentPassword: "",
    nextPassword: ""
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
  if (!passwordForm.currentPassword || !passwordForm.nextPassword) {
    return;
  }
  await updatePassword(currentUser.id, {
    current_password: passwordForm.currentPassword,
    next_password: passwordForm.nextPassword
  });
  closePassword();
}

async function loadUnreadCount() {
  const { data } = await fetchUserNotices();
  unreadNoticeCount.value = data.filter((item) => item.read_status === "未读").length;
}

function logout() {
  clearSession();
  router.push("/login");
}

onMounted(loadUnreadCount);
</script>
