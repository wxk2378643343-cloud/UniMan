<template>
  <AppShell title="业务总览">
    <section class="hero-banner">
      <div>
        <p class="eyebrow">统计分析</p>
        <h2>高校后勤服务管理系统首页总览</h2>
      </div>
      <p class="hero-banner-text">
        首页集中展示工单、投诉、公告和部门任务负载。除首页外，其他功能页面均采用后台表格方式展示。
      </p>
    </section>

    <section class="metric-grid metric-grid-4">
      <article v-for="metric in visibleMetrics" :key="metric.label" class="metric-card" :class="`accent-${metric.accent}`">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
      </article>
    </section>

    <section class="chart-grid">
      <article class="panel-card">
        <div class="panel-head"><h3>工单状态分布</h3><small>ECharts</small></div>
        <div ref="repairChartRef" class="chart-box"></div>
      </article>
      <article class="panel-card">
        <div class="panel-head"><h3>投诉处理状态</h3><small>ECharts</small></div>
        <div ref="complaintChartRef" class="chart-box"></div>
      </article>
      <article class="panel-card">
        <div class="panel-head"><h3>公告分类统计</h3><small>ECharts</small></div>
        <div ref="noticeChartRef" class="chart-box"></div>
      </article>
      <article class="panel-card">
        <div class="panel-head"><h3>部门任务负载</h3><small>ECharts</small></div>
        <div ref="departmentChartRef" class="chart-box"></div>
      </article>
    </section>

    <section class="split-grid">
      <article class="panel-card">
        <div class="panel-head"><h3>最新工单</h3><small>最近 6 条</small></div>
        <div class="table-wrap">
          <table class="data-table compact-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>报修人</th>
                <th>位置</th>
                <th>类型</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in summary.repairs" :key="item.id">
                <td>#{{ item.id }}</td>
                <td>{{ item.student_name }}</td>
                <td>{{ item.location }}</td>
                <td>{{ item.repair_type }}</td>
                <td><span class="tag">{{ item.status }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="panel-card">
        <div class="panel-head"><h3>运行说明</h3><small>系统概览</small></div>
        <div class="intro-block">
          <p>当前系统覆盖用户管理、角色管理、报修工单、投诉建议、公告通知和统计分析模块。</p>
          <p>页面交互统一采用后台表格样式，新增和编辑均通过弹窗完成，便于后续继续扩展分页、筛选和审批流程。</p>
        </div>
      </article>
    </section>
  </AppShell>
</template>

<script setup>
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { fetchDashboard } from "../api";
import AppShell from "../components/AppShell.vue";

const summary = reactive({
  metrics: [],
  charts: {
    repairStatus: [],
    complaintStatus: [],
    noticeCategory: [],
    departmentLoad: []
  },
  repairs: []
});

const visibleMetrics = computed(() =>
  summary.metrics.filter((item) =>
    ["累计工单", "待处理事项", "投诉建议", "系统用户"].includes(item.label)
  )
);

const repairChartRef = ref(null);
const complaintChartRef = ref(null);
const noticeChartRef = ref(null);
const departmentChartRef = ref(null);
const chartInstances = [];

function makePie(el, data, title) {
  const chart = echarts.init(el);
  chart.setOption({
    tooltip: { trigger: "item" },
    legend: { bottom: 0 },
    series: [{ type: "pie", radius: ["45%", "72%"], data, label: { formatter: "{b}" } }],
    title: { text: title, left: "center", top: "42%", textStyle: { fontSize: 14, fontWeight: 600 } }
  });
  chartInstances.push(chart);
}

function makeBar(el, data) {
  const chart = echarts.init(el);
  chart.setOption({
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: data.map((item) => item.name) },
    yAxis: { type: "value" },
    series: [{ type: "bar", data: data.map((item) => item.value), itemStyle: { color: "#d38d22" }, barWidth: 34 }]
  });
  chartInstances.push(chart);
}

async function renderCharts() {
  await nextTick();
  chartInstances.splice(0).forEach((chart) => chart.dispose());
  makePie(repairChartRef.value, summary.charts.repairStatus, "工单");
  makePie(complaintChartRef.value, summary.charts.complaintStatus, "投诉");
  makePie(noticeChartRef.value, summary.charts.noticeCategory, "公告");
  makeBar(departmentChartRef.value, summary.charts.departmentLoad);
}

function handleResize() {
  chartInstances.forEach((chart) => chart.resize());
}

onMounted(async () => {
  const { data } = await fetchDashboard();
  Object.assign(summary, data);
  await renderCharts();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  chartInstances.forEach((chart) => chart.dispose());
});
</script>
