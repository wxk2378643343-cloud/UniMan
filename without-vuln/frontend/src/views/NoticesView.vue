<template>
  <AppShell title="公告通知">
    <section class="table-toolbar">
      <div class="toolbar-group toolbar-single">
        <input v-model="keyword" placeholder="搜索标题/分类/发布人" />
      </div>
      <button v-if="canManage" class="primary-button" @click="openCreate">新增公告</button>
    </section>

    <section class="panel-card">
      <div class="panel-head"><h3>公告管理列表</h3></div>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>标题</th>
              <th>分类</th>
              <th>发布人</th>
              <th>状态</th>
              <th>发布时间</th>
              <th>内容</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredNotices" :key="item.id">
              <td>#{{ item.id }}</td>
              <td>{{ item.title }}</td>
              <td>{{ item.category }}</td>
              <td>{{ item.publisher }}</td>
              <td><span class="tag">{{ item.status }}</span></td>
              <td>{{ item.created_at }}</td>
              <td class="cell-ellipsis" :title="item.content">{{ item.content }}</td>
              <td>
                <button v-if="canManage" class="table-button" @click="openEdit(item)">编辑</button>
                <span v-else class="text-muted">查看</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="modalVisible" class="modal-mask" @click.self="closeModal">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ modalMode === 'create' ? '新增公告' : '编辑公告' }}</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="modal-body form-grid form-grid-2">
            <input v-model="modalForm.title" placeholder="公告标题" />
            <select v-model="modalForm.category">
              <option v-for="item in categoryOptions" :key="item">{{ item }}</option>
            </select>
            <input v-model="modalForm.publisher" placeholder="发布人" />
            <select v-model="modalForm.status">
              <option>已发布</option>
              <option>草稿</option>
              <option>已下线</option>
            </select>
            <textarea v-model="modalForm.content" rows="5" placeholder="公告内容"></textarea>
          </div>
          <div class="modal-footer">
            <button type="button" class="secondary-button" @click="closeModal">取消</button>
            <button type="submit" class="primary-button">{{ modalMode === "create" ? "新增" : "保存" }}</button>
          </div>
        </form>
      </div>
    </div>
  </AppShell>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { createNotice, fetchNotices, updateNotice } from "../api";
import AppShell from "../components/AppShell.vue";

const notices = ref([]);
const keyword = ref("");
const modalVisible = ref(false);
const modalMode = ref("create");
const currentId = ref(null);
const currentRole = localStorage.getItem("role") || "";
const canManage = currentRole === "系统管理员";
const categoryOptions = ["后勤公告", "服务提醒", "值班通知", "停水停电", "节假日安排"];
const emptyForm = () => ({
  title: "",
  category: "后勤公告",
  content: "",
  publisher: "后勤保障处",
  status: "已发布"
});
const modalForm = reactive(emptyForm());

const filteredNotices = computed(() =>
  notices.value.filter((item) =>
    !keyword.value || `${item.title}${item.category}${item.publisher}`.includes(keyword.value)
  )
);

function resetForm() {
  Object.assign(modalForm, emptyForm());
}

function openCreate() {
  if (!canManage) {
    return;
  }
  modalMode.value = "create";
  currentId.value = null;
  resetForm();
  modalVisible.value = true;
}

function openEdit(item) {
  if (!canManage) {
    return;
  }
  modalMode.value = "edit";
  currentId.value = item.id;
  Object.assign(modalForm, item);
  modalVisible.value = true;
}

function closeModal() {
  modalVisible.value = false;
}

async function loadNotices() {
  const { data } = await fetchNotices();
  notices.value = data;
}

async function submitModal() {
  if (!canManage) {
    return;
  }
  if (modalMode.value === "create") {
    await createNotice(modalForm);
  } else {
    await updateNotice(currentId.value, modalForm);
  }
  closeModal();
  await loadNotices();
}

onMounted(loadNotices);
</script>
