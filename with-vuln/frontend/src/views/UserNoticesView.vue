<template>
  <UserPortalLayout
    title="公告通知"
    description="集中浏览面向学生的后勤公告，列表改为门户信息流风格，适合普通用户直接阅读。"
  >
    <template #hero-aside>
      <article class="portal-hero-panel">
        <span>阅读建议</span>
        <strong>优先关注全校与学生范围公告</strong>
        <small>系统只展示已发布且与你相关的通知</small>
      </article>
    </template>

    <section class="table-toolbar">
      <div class="toolbar-group toolbar-single">
        <input v-model="keyword" placeholder="搜索公告标题/范围" />
      </div>
    </section>

    <section class="panel-card">
      <div class="service-list">
        <article
          v-for="item in filteredItems"
          :key="item.id"
          class="service-card notice-card notice-card-interactive"
          @click="openNotice(item)"
        >
          <div class="service-card-head">
            <div>
              <strong>{{ item.title }}</strong>
              <span>{{ item.publish_scope }}</span>
            </div>
            <span class="tag">{{ item.read_status }}</span>
          </div>
          <p>{{ item.content }}</p>
          <small>发布时间：{{ item.published_at || item.created_at }}</small>
        </article>
      </div>
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
import { computed, onMounted, ref } from "vue";
import { getSession } from "../auth";
import { fetchUserNotices, markNoticeRead } from "../api";
import UserPortalLayout from "../components/UserPortalLayout.vue";

const session = getSession();
const items = ref([]);
const keyword = ref("");
const activeNotice = ref(null);

const filteredItems = computed(() =>
  items.value.filter((item) => !keyword.value || `${item.title}${item.publish_scope}`.includes(keyword.value))
);

async function loadData() {
  const { data } = await fetchUserNotices(session.user.role, session.user.id);
  items.value = data;
}

async function openNotice(item) {
  if (item.read_status !== "已读") {
    await markNoticeRead(item.id, session.user.id);
    item.read_status = "已读";
  }
  activeNotice.value = item;
}

function closeNotice() {
  activeNotice.value = null;
}

onMounted(async () => {
  await loadData();
});
</script>
