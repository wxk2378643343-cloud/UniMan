<template>
  <AppShell title="投诉建议管理" eyebrow="管理后台" mode="admin">
    <section class="table-toolbar">
      <div class="toolbar-group">
        <input v-model="keyword" placeholder="搜索标题/提交人/类型" />
        <select v-model="statusFilter">
          <option value="">全部状态</option>
          <option v-for="item in options.complaint_statuses" :key="item">{{ item }}</option>
        </select>
      </div>
    </section>

    <section class="panel-card">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>提交人</th>
              <th>类型</th>
              <th>标题</th>
              <th>状态</th>
              <th>回复</th>
              <th>时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredItems" :key="item.id">
              <td>{{ item.user_name }}</td>
              <td>{{ item.type }}</td>
              <td>{{ item.title }}</td>
              <td><span class="tag">{{ item.status }}</span></td>
              <td class="cell-ellipsis">{{ item.reply || "待回复" }}</td>
              <td>{{ item.created_at }}</td>
              <td class="table-actions">
                <button class="table-button" @click="openEdit(item)">处理</button>
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
          <h3>处理投诉建议</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="modal-body form-grid form-grid-2">
            <div class="field-block">
              <span class="field-label">提交人</span>
              <input :value="form.user_name" disabled />
            </div>
            <div class="field-block">
              <span class="field-label">类型</span>
              <select v-model="form.type">
                <option v-for="item in options.complaint_types" :key="item">{{ item }}</option>
              </select>
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">标题</span>
              <input v-model="form.title" />
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">内容</span>
              <textarea v-model="form.content" rows="4"></textarea>
            </div>
            <div class="field-block">
              <span class="field-label">状态</span>
              <select v-model="form.status">
                <option v-for="item in options.complaint_statuses" :key="item">{{ item }}</option>
              </select>
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">处理回复</span>
              <textarea v-model="form.reply" rows="4"></textarea>
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
import { deleteComplaint, fetchComplaints, fetchOptions, updateComplaint } from "../api";
import AppShell from "../components/AppShell.vue";

const items = ref([]);
const keyword = ref("");
const statusFilter = ref("");
const modalVisible = ref(false);
const currentId = ref(null);
const options = reactive({
  complaint_types: [],
  complaint_statuses: []
});
const form = reactive({
  user_id: null,
  user_name: "",
  type: "",
  title: "",
  content: "",
  image_url: "",
  status: "待处理",
  reply: ""
});

const filteredItems = computed(() =>
  items.value.filter((item) => {
    const hitKeyword = !keyword.value || `${item.user_name}${item.type}${item.title}`.includes(keyword.value);
    const hitStatus = !statusFilter.value || item.status === statusFilter.value;
    return hitKeyword && hitStatus;
  })
);

function openEdit(item) {
  currentId.value = item.id;
  Object.assign(form, item);
  modalVisible.value = true;
}

function closeModal() {
  modalVisible.value = false;
}

async function loadData() {
  const [complaintRes, optionRes] = await Promise.all([fetchComplaints(), fetchOptions()]);
  items.value = complaintRes.data;
  Object.assign(options, optionRes.data);
}

async function submitModal() {
  await updateComplaint(currentId.value, form);
  closeModal();
  await loadData();
}

async function removeItem(id) {
  await deleteComplaint(id);
  await loadData();
}

onMounted(loadData);
</script>
