<template>
  <div class="login-layout">
    <section class="login-showcase">
      <p class="eyebrow">高校后勤服务管理系统</p>
      <h1>统一登录入口</h1>
      <p class="showcase-text">
        使用同一个登录页进入系统。普通用户进入服务门户，后勤人员和管理员进入业务管理后台。
      </p>

      <div class="showcase-grid">
        <article class="showcase-card">
          <strong>前台用户端</strong>
          <span>报修、投诉、公告与个人记录</span>
        </article>
        <article class="showcase-card">
          <strong>后台管理端</strong>
          <span>表格管理、Modal 表单、完整增删改查</span>
        </article>
        <article class="showcase-card">
          <strong>技术栈</strong>
          <span>Vue + FastAPI + SQLite</span>
        </article>
      </div>
    </section>

    <section class="login-panel">
      <div class="panel-header">
        <p class="eyebrow">登录系统</p>
        <h2>账号登录</h2>
      </div>

      <form class="login-form" @submit.prevent="handleLogin">
        <label>
          <span>用户名</span>
          <input v-model="form.username" placeholder="admin / user01 / logis01" />
        </label>
        <label>
          <span>密码</span>
          <input v-model="form.password" type="password" placeholder="请输入密码" />
        </label>
        <button class="primary-button" :disabled="loading">
          {{ loading ? "登录中..." : "进入系统" }}
        </button>
      </form>

      <div class="login-demo">
        <p>示例账号</p>
        <small>`admin / admin123` 管理员</small>
        <small>`logis01 / 123456` 后勤人员</small>
        <small>`user01 / 123456` 普通用户</small>
      </div>

      <p v-if="message" class="status-text">{{ message }}</p>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { getRoleHome, setSession } from "../auth";
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
    setSession({
      token: data.token,
      password: form.password,
      user: data.user
    });
    router.push(getRoleHome(data.user.role));
  } catch (error) {
    message.value = error.response?.data?.detail || "登录失败";
  } finally {
    loading.value = false;
  }
}
</script>
