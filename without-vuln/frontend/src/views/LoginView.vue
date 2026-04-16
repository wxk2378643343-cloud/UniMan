<template>
  <div class="login-page">
    <section class="login-hero">
      <p class="eyebrow">高校后勤服务管理系统</p>
      <h1>高校后勤服务管理系统</h1>
      <p class="hero-text">
        面向高校后勤业务场景，提供用户管理、报修工单、投诉建议、公告通知和统计分析等核心功能。
      </p>
      <div class="hero-grid">
        <div class="hero-card"><strong>FastAPI</strong><span>后端服务</span></div>
        <div class="hero-card"><strong>Vue</strong><span>前端界面</span></div>
        <div class="hero-card"><strong>SQLite</strong><span>轻量数据库</span></div>
      </div>
    </section>

    <section class="login-panel">
      <div class="panel-header">
        <p class="eyebrow">系统登录</p>
        <h2>进入管理平台</h2>
      </div>

      <form class="login-form" @submit.prevent="handleLogin">
        <label>
          <span>用户名</span>
          <input v-model="form.username" placeholder="admin" />
        </label>
        <label>
          <span>密码</span>
          <input v-model="form.password" type="password" placeholder="admin123" />
        </label>
        <button class="primary-button" :disabled="loading">
          {{ loading ? "登录中..." : "登录系统" }}
        </button>
      </form>

      <p class="hint-text">默认账户：admin / admin123</p>
      <p v-if="message" class="status-text">{{ message }}</p>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { login } from "../api";

const router = useRouter();
const loading = ref(false);
const message = ref("");
const form = reactive({
  username: "admin",
  password: "admin123"
});

async function handleLogin() {
  loading.value = true;
  message.value = "";
  try {
    const { data } = await login(form);
    localStorage.setItem("token", data.token);
    localStorage.setItem("userId", String(data.user.id));
    localStorage.setItem("username", data.user.username);
    localStorage.setItem("displayName", data.user.display_name);
    localStorage.setItem("role", data.user.role);
    localStorage.setItem("department", data.user.department);
    localStorage.setItem("status", data.user.status);
    message.value = data.message;
    setTimeout(() => router.push("/dashboard"), 500);
  } catch (error) {
    message.value = error.response?.data?.detail || "登录失败";
  } finally {
    loading.value = false;
  }
}
</script>
