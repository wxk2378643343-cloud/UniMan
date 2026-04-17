<template>
  <UserPortalLayout
    title="我的后勤服务中心"
    description="在一个统一入口里查看报修进度、投诉建议、公告通知和待办事项，普通用户进入后直接看到服务而不是后台管理界面。"
  >
    <template #hero-aside>
      <section class="home-hero-side">
        <article class="home-highlight-card">
          <span class="home-highlight-label">欢迎回来</span>
          <strong>{{ session.user.name }}</strong>
          <p>{{ session.user.department }} · 在线查看我的报修、公告和投诉处理进度。</p>
          <div class="home-highlight-actions">
            <RouterLink to="/user/repairs" class="primary-button">立即报修</RouterLink>
            <RouterLink to="/user/notices" class="ghost-button">查看公告</RouterLink>
          </div>
        </article>

        <div class="home-hero-metrics">
          <article v-for="item in summary.metrics.slice(0, 2)" :key="item.label" class="home-mini-metric">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </article>
        </div>
      </section>
    </template>

    <section class="home-overview-grid">
      <article class="home-summary-card">
        <div class="home-section-heading">
          <div>
            <p class="eyebrow">公告通知</p>
            <h2>进入首页先看通知</h2>
          </div>
          <RouterLink to="/user/notices" class="home-inline-link">全部公告</RouterLink>
        </div>

        <section class="home-notice-board">
          <article
            v-for="item in summary.recent_notices"
            :key="item.id"
            class="home-notice-board-item notice-entry-button"
            @click="openNotice(item)"
          >
            <div>
              <strong>{{ item.title }}</strong>
              <span>{{ item.publish_scope }}</span>
            </div>
            <div class="home-notice-meta">
              <span class="tag">{{ item.read_status }}</span>
              <small>{{ item.published_at || "-" }}</small>
            </div>
          </article>
        </section>
      </article>

      <article class="home-notice-focus">
        <p class="eyebrow">消息中心</p>
        <h2>公告优先</h2>
        <p>首页第一屏优先展示与你相关的后勤通知，避免用户进入系统后错过停水停电、维修安排和服务提醒。</p>
        <div class="home-highlight-actions">
          <RouterLink to="/user/notices" class="primary-button">查看全部公告</RouterLink>
        </div>
      </article>
    </section>

    <section class="home-shortcuts-panel">
      <div class="home-section-heading">
        <div>
          <p class="eyebrow">快捷服务</p>
          <h2>常用入口</h2>
        </div>
        <span>公告下面直接接常用服务，减少来回找入口</span>
      </div>

      <section class="portal-shortcuts home-shortcuts-grid">
        <RouterLink to="/user/repairs" class="portal-shortcut-card home-shortcut-card home-shortcut-warm">
          <small>维修服务</small>
          <strong>报修申请</strong>
          <span>快速提交宿舍、教室和公共区域报修</span>
        </RouterLink>
        <RouterLink to="/user/complaints" class="portal-shortcut-card home-shortcut-card home-shortcut-cool">
          <small>意见反馈</small>
          <strong>投诉建议</strong>
          <span>向后勤中心反馈问题并跟踪回复</span>
        </RouterLink>
        <RouterLink to="/user/notices" class="portal-shortcut-card home-shortcut-card home-shortcut-light">
          <small>消息中心</small>
          <strong>公告通知</strong>
          <span>查看面向学生的最新后勤消息</span>
        </RouterLink>
        <button
          class="portal-shortcut-card portal-shortcut-card-button home-shortcut-card home-shortcut-deep"
          type="button"
          @click="scrollToProgress"
        >
          <small>服务进度</small>
          <strong>我的进度</strong>
          <span>直接跳转到当前服务处理进度区域</span>
        </button>
      </section>
    </section>

    <section class="home-summary-card">
      <div class="home-section-heading">
        <div>
          <p class="eyebrow">服务概况</p>
          <h2>本学期服务状态</h2>
        </div>
        <span>从首页就能快速判断当前办事节奏</span>
      </div>

      <section class="home-metric-board">
        <article v-for="item in summary.metrics" :key="item.label" class="metric-card home-metric-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
      </section>
    </section>

    <section id="progress-section" class="home-progress-grid">
      <article class="panel-card home-list-card">
        <div class="home-section-heading">
          <div>
            <p class="eyebrow">我的报修</p>
            <h2>处理进度</h2>
          </div>
          <RouterLink to="/user/repairs" class="home-inline-link">查看全部</RouterLink>
        </div>
        <div class="home-list-shell">
          <div v-for="item in summary.recent_repairs" :key="item.id" class="home-progress-item">
            <div class="home-progress-main">
              <strong>{{ item.order_no }}</strong>
              <span>{{ item.repair_type }} / {{ item.building }}{{ item.room ? ` ${item.room}` : "" }}</span>
            </div>
            <span class="tag">{{ item.status }}</span>
          </div>
        </div>
      </article>

      <article class="panel-card home-list-card">
        <div class="home-section-heading">
          <div>
            <p class="eyebrow">投诉建议</p>
            <h2>最新反馈</h2>
          </div>
          <RouterLink to="/user/complaints" class="home-inline-link">去反馈</RouterLink>
        </div>
        <div class="home-list-shell">
          <div
            v-for="item in summary.recent_complaints.slice(0, 4)"
            :key="item.id"
            class="home-feedback-item"
          >
            <div>
              <strong>{{ item.title }}</strong>
              <span>{{ item.type }}</span>
            </div>
            <small>{{ item.reply || "暂未回复" }}</small>
          </div>
        </div>
      </article>
    </section>

    <section class="home-bottom-grid">
      <article class="panel-card home-list-card">
        <div class="home-section-heading">
          <div>
            <p class="eyebrow">公告通知</p>
            <h2>更多公告</h2>
          </div>
          <RouterLink to="/user/notices" class="home-inline-link">全部公告</RouterLink>
        </div>
        <div class="home-list-shell">
          <div
            v-for="item in summary.recent_notices"
            :key="item.id"
            class="home-notice-row notice-entry-button"
            @click="openNotice(item)"
          >
            <div>
              <strong>{{ item.title }}</strong>
              <span>{{ item.publish_scope }}</span>
            </div>
            <div class="home-notice-meta">
              <span class="tag">{{ item.read_status }}</span>
              <small>{{ item.published_at || "-" }}</small>
            </div>
          </div>
        </div>
      </article>

      <article class="home-service-banner">
        <p class="eyebrow">使用建议</p>
        <h2>有问题先提交服务单</h2>
        <p>报修适合设施故障，投诉建议适合流程、态度和体验反馈。系统会保留你的历史记录，后续查询更方便。</p>
        <div class="home-highlight-actions">
          <RouterLink to="/user/repairs" class="primary-button">提交报修</RouterLink>
          <RouterLink to="/user/complaints" class="ghost-button">提交建议</RouterLink>
        </div>
      </article>
    </section>

    <div v-if="activeNotice" class="modal-mask" @click.self="closeNotice">
      <div class="modal-card modal-card-compact">
        <div class="modal-header">
          <h3>{{ activeNotice.title }}</h3>
          <button class="modal-close" @click="closeNotice">×</button>
        </div>
        <div class="modal-body notice-detail">
          <div class="notice-detail-meta">
            <span class="tag">{{ activeNotice.read_status }}</span>
            <small>发布范围：{{ activeNotice.publish_scope }}</small>
            <small>发布时间：{{ activeNotice.published_at || activeNotice.created_at }}</small>
          </div>
          <div class="notice-detail-content">
            {{ activeNotice.content }}
          </div>
          <div class="notice-detail-footer">
            <strong>发布人：{{ activeNotice.publisher_name }}</strong>
            <small>发布编号：公告 #{{ activeNotice.id }}</small>
          </div>
        </div>
      </div>
    </div>
  </UserPortalLayout>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { RouterLink } from "vue-router";
import { getSession } from "../auth";
import { fetchDashboard, markNoticeRead } from "../api";
import UserPortalLayout from "../components/UserPortalLayout.vue";

const session = getSession();
const summary = reactive({
  metrics: [],
  recent_repairs: [],
  recent_notices: [],
  recent_complaints: []
});
const activeNotice = ref(null);

onMounted(async () => {
  const { data } = await fetchDashboard();
  Object.assign(summary, data);
});

function scrollToProgress() {
  document.getElementById("progress-section")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function openNotice(item) {
  if (item.read_status !== "已读") {
    await markNoticeRead(item.id);
    item.read_status = "已读";
  }
  activeNotice.value = { ...item };
}

function closeNotice() {
  activeNotice.value = null;
}
</script>
