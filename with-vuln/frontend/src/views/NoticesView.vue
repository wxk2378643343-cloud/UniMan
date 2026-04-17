<template>
  <AppShell title="公告管理" eyebrow="管理后台" mode="admin">
    <section class="table-toolbar">
      <div class="toolbar-group">
        <input v-model="keyword" placeholder="搜索标题/发布范围" />
        <select v-model="statusFilter">
          <option value="">全部状态</option>
          <option v-for="item in options.notice_statuses" :key="item">{{ item }}</option>
        </select>
      </div>
      <button class="primary-button" @click="openCreate">新增公告</button>
    </section>

    <section class="panel-card">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>标题</th>
              <th>状态</th>
              <th>发布范围</th>
              <th>发布人</th>
              <th>发布时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredItems" :key="item.id">
              <td>{{ item.title }}</td>
              <td><span class="tag">{{ item.status }}</span></td>
              <td>{{ item.publish_scope }}</td>
              <td>{{ item.publisher_name }}</td>
              <td>{{ item.published_at || "-" }}</td>
              <td class="table-actions">
                <button class="table-button" @click="openEdit(item)">编辑</button>
                <button class="table-button danger-button" @click="removeItem(item.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="modalVisible" class="modal-mask" @click.self="closeModal">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ modalMode === "create" ? "新增公告" : "编辑公告" }}</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="modal-body form-grid form-grid-2">
            <div class="field-block field-span-2">
              <span class="field-label">公告标题</span>
              <input v-model="form.title" />
            </div>
            <div class="field-block">
              <span class="field-label">公告状态</span>
              <select v-model="form.status">
                <option v-for="item in options.notice_statuses" :key="item">{{ item }}</option>
              </select>
            </div>
            <div class="field-block">
              <span class="field-label">发布范围</span>
              <select v-model="form.publish_scope">
                <option v-for="item in options.notice_scopes" :key="item">{{ item }}</option>
              </select>
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">公告内容</span>
              <textarea v-model="form.content" rows="5"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="secondary-button" @click="closeModal">取消</button>
            <button type="submit" class="primary-button">保存</button>
          </div>
        </form>
      </div>
    </div>
  </AppShell>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { getSession } from "../auth";
import { createNotice, deleteNotice, fetchNotices, fetchOptions, updateNotice } from "../api";
import AppShell from "../components/AppShell.vue";

const session = getSession();
const items = ref([]);
const keyword = ref("");
const statusFilter = ref("");
const modalVisible = ref(false);
const modalMode = ref("create");
const currentId = ref(null);
const options = reactive({
  notice_statuses: [],
  notice_scopes: []
});
const form = reactive({
  title: "",
  content: "",
  status: "草稿",
  publish_scope: "全校",
  publisher_id: session.user.id,
  publisher_name: session.user.name
});

const filteredItems = computed(() =>
  items.value.filter((item) => {
    const hitKeyword = !keyword.value || `${item.title}${item.publish_scope}`.includes(keyword.value);
    const hitStatus = !statusFilter.value || item.status === statusFilter.value;
    return hitKeyword && hitStatus;
  })
);

function resetForm() {
  Object.assign(form, {
    title: "",
    content: "",
    status: "草稿",
    publish_scope: "全校",
    publisher_id: session.user.id,
    publisher_name: session.user.name
  });
}

function openCreate() {
  modalMode.value = "create";
  currentId.value = null;
  resetForm();
  modalVisible.value = true;
}

function openEdit(item) {
  modalMode.value = "edit";
  currentId.value = item.id;
  Object.assign(form, item);
  modalVisible.value = true;
}

function closeModal() {
  modalVisible.value = false;
}

async function loadData() {
  const [noticeRes, optionRes] = await Promise.all([fetchNotices(), fetchOptions()]);
  items.value = noticeRes.data;
  Object.assign(options, optionRes.data);
}

async function submitModal() {
  if (modalMode.value === "create") {
    await createNotice(form);
  } else {
    await updateNotice(currentId.value, form);
  }
  closeModal();
  await loadData();
}

async function removeItem(id) {
  await deleteNotice(id);
  await loadData();
}

onMounted(loadData);
</script>
