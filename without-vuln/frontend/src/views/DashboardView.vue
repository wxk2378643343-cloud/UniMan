<template>
  <AppShell title="业务总览" eyebrow="管理后台" mode="admin">
    <section class="hero-panel admin-hero">
      <div>
        <p class="eyebrow">首页看板</p>
        <h2>后勤服务管理总览</h2>
      </div>
      <p class="hero-copy">面向后勤人员和管理员展示工单、投诉建议、公告和基础数据的整体运行情况。</p>
    </section>

    <section class="metric-grid">
      <article v-for="item in summary.metrics" :key="item.label" class="metric-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </section>

    <section class="split-grid">
      <article class="panel-card">
        <div class="panel-head">
          <h3>工单状态分布</h3>
        </div>
        <div class="mini-list">
          <div v-for="item in summary.charts.repairs" :key="item.name" class="mini-list-row">
            <span>{{ item.name }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </article>

      <article class="panel-card">
        <div class="panel-head">
          <h3>投诉处理状态</h3>
        </div>
        <div class="mini-list">
          <div v-for="item in summary.charts.complaints" :key="item.name" class="mini-list-row">
            <span>{{ item.name }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </article>
    </section>

    <section class="panel-card">
      <div class="panel-head">
        <h3>最新工单</h3>
      </div>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>工单号</th>
              <th>报修人</th>
              <th>类型</th>
              <th>状态</th>
              <th>处理人</th>
              <th>更新时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in summary.latest_repairs" :key="item.id">
              <td>{{ item.order_no }}</td>
              <td>{{ item.reporter_name }}</td>
              <td>{{ item.repair_type }}</td>
              <td><span class="tag">{{ item.status }}</span></td>
              <td>{{ item.assignee_name }}</td>
              <td>{{ item.updated_at }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </AppShell>
</template>

<script setup>
import { onMounted, reactive } from "vue";
import { fetchDashboard } from "../api";
import AppShell from "../components/AppShell.vue";

const summary = reactive({
  metrics: [],
  charts: {
    repairs: [],
    complaints: []
  },
  latest_repairs: []
});

onMounted(async () => {
  const { data } = await fetchDashboard();
  Object.assign(summary, data);
});
</script>
