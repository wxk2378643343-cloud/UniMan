<template>
  <AppShell title="投诉建议">
    <section class="table-toolbar">
      <div class="toolbar-group">
        <input v-model="keyword" placeholder="搜索学生/分类/内容" />
        <select v-model="statusFilter">
          <option value="">全部状态</option>
          <option>待处理</option>
          <option>处理中</option>
          <option>已回复</option>
        </select>
      </div>
      <button class="primary-button" @click="openCreate">新增投诉建议</button>
    </section>

    <section class="panel-card">
      <div class="panel-head"><h3>投诉建议列表</h3></div>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>学生</th>
              <th>分类</th>
              <th>联系电话</th>
              <th>状态</th>
              <th>内容</th>
              <th>处理回复</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredComplaints" :key="item.id">
              <td>#{{ item.id }}</td>
              <td>{{ item.student_name }}</td>
              <td>{{ item.category }}</td>
              <td>{{ item.contact_phone }}</td>
              <td><span class="tag">{{ item.status }}</span></td>
              <td class="cell-ellipsis" :title="item.content">{{ item.content }}</td>
              <td class="cell-ellipsis" :title="item.reply">{{ item.reply || "-" }}</td>
              <td><button class="table-button" @click="openEdit(item)">编辑</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="modalVisible" class="modal-mask" @click.self="closeModal">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ modalMode === 'create' ? '新增投诉建议' : '编辑投诉建议' }}</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="modal-body form-grid form-grid-2">
            <input v-model="modalForm.student_name" placeholder="学生姓名" />
            <select v-model="modalForm.category">
              <option v-for="item in categoryOptions" :key="item">{{ item }}</option>
            </select>
            <input v-model="modalForm.contact_phone" placeholder="联系电话" />
            <select v-model="modalForm.status">
              <option>待处理</option>
              <option>处理中</option>
              <option>已回复</option>
            </select>
            <textarea v-model="modalForm.content" rows="4" placeholder="意见内容"></textarea>
            <textarea v-model="modalForm.reply" rows="4" placeholder="处理回复"></textarea>
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
import { createComplaint, fetchComplaints, updateComplaint } from "../api";
import AppShell from "../components/AppShell.vue";

const complaints = ref([]);
const keyword = ref("");
const statusFilter = ref("");
const modalVisible = ref(false);
const modalMode = ref("create");
const currentId = ref(null);
const categoryOptions = ["服务态度", "环境卫生", "餐饮建议", "宿舍管理", "设施维护"];
const emptyForm = () => ({
  student_name: "",
  category: "服务态度",
  content: "",
  contact_phone: "",
  status: "待处理",
  reply: ""
});
const modalForm = reactive(emptyForm());

const filteredComplaints = computed(() =>
  complaints.value.filter((item) => {
    const keywordMatched =
      !keyword.value || `${item.student_name}${item.category}${item.content}`.includes(keyword.value);
    const statusMatched = !statusFilter.value || item.status === statusFilter.value;
    return keywordMatched && statusMatched;
  })
);

function resetForm() {
  Object.assign(modalForm, emptyForm());
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
  Object.assign(modalForm, item);
  modalVisible.value = true;
}

function closeModal() {
  modalVisible.value = false;
}

async function loadComplaints() {
  const { data } = await fetchComplaints();
  complaints.value = data;
}

async function submitModal() {
  if (modalMode.value === "create") {
    await createComplaint(modalForm);
  } else {
    await updateComplaint(currentId.value, {
      category: modalForm.category,
      content: modalForm.content,
      status: modalForm.status,
      reply: modalForm.reply
    });
  }
  closeModal();
  await loadComplaints();
}

onMounted(loadComplaints);
</script>
