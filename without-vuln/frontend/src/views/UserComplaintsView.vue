<template>
  <UserPortalLayout
    title="投诉建议"
    description="在前台门户中直接提交意见和查看回复，保留普通用户需要的内容，不再出现管理后台样式。"
  >
    <template #hero-aside>
      <article class="portal-hero-panel">
        <span>反馈入口</span>
        <strong>意见会进入后勤处理流程</strong>
        <small>已提交记录可继续查看状态和回复内容</small>
      </article>
    </template>

    <section class="table-toolbar">
      <div class="toolbar-group toolbar-single">
        <input v-model="keyword" placeholder="搜索标题/类型/状态" />
      </div>
      <button class="primary-button" @click="openCreate">提交意见</button>
    </section>

    <section class="panel-card">
      <div class="service-list">
        <article
          v-for="item in filteredItems"
          :key="item.id"
          class="service-card service-card-interactive user-record-card"
          @click="openDetail(item)"
        >
          <div class="service-card-head">
            <div>
              <strong>{{ item.title }}</strong>
              <span>{{ item.type }}</span>
            </div>
            <span class="tag">{{ displayStatus(item.status) }}</span>
          </div>
          <p>{{ item.content }}</p>
          <small>{{ item.reply || "暂未回复" }}</small>
          <div class="service-actions service-actions-bottom">
            <button class="table-button" @click.stop="openDetail(item)">查看详情</button>
            <button v-if="canEdit(item)" class="table-button" @click.stop="openEdit(item)">编辑</button>
            <button v-if="canCancel(item)" class="table-button danger-button" @click.stop="cancelComplaint(item)">取消建议</button>
          </div>
        </article>
      </div>
    </section>

    <div v-if="detailItem" class="modal-mask" @click.self="closeDetail">
      <div class="modal-card modal-card-compact">
        <div class="modal-header">
          <h3>{{ detailItem.title }}</h3>
          <button class="modal-close" @click="closeDetail">×</button>
        </div>
        <div class="modal-body form-grid">
          <div class="detail-summary-row">
            <span class="tag">{{ displayStatus(detailItem.status) }}</span>
            <small>提交时间：{{ detailItem.created_at }}</small>
          </div>
          <div class="detail-grid">
            <div class="field-block">
              <span class="field-label">建议类型</span>
              <div class="detail-value">{{ detailItem.type }}</div>
            </div>
            <div class="field-block">
              <span class="field-label">当前状态</span>
              <div class="detail-value">{{ displayStatus(detailItem.status) }}</div>
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">详细内容</span>
              <div class="detail-value">{{ detailItem.content }}</div>
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">处理回复</span>
              <div class="detail-value">{{ detailItem.reply || "暂未回复" }}</div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="secondary-button" @click="closeDetail">关闭</button>
          <button v-if="canEdit(detailItem)" type="button" class="table-button" @click="openEdit(detailItem)">编辑</button>
          <button v-if="canCancel(detailItem)" type="button" class="table-button danger-button" @click="cancelComplaint(detailItem)">取消建议</button>
        </div>
      </div>
    </div>

    <div v-if="modalVisible" class="modal-mask" @click.self="closeModal">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ modalMode === "create" ? "提交投诉建议" : "编辑投诉建议" }}</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="modal-body form-grid form-grid-2">
            <div class="field-block">
              <span class="field-label">建议类型</span>
              <select v-model="form.type">
                <option v-for="item in options.complaint_types" :key="item">{{ item }}</option>
              </select>
            </div>
            <div class="field-block">
              <span class="field-label">状态</span>
              <input :value="form.status" disabled />
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">标题</span>
              <input v-model="form.title" />
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">详细内容</span>
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
  </UserPortalLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { getSession } from "../auth";
import { createComplaint, fetchComplaints, fetchOptions, updateComplaint } from "../api";
import UserPortalLayout from "../components/UserPortalLayout.vue";

const session = getSession();
const items = ref([]);
const keyword = ref("");
const modalVisible = ref(false);
const modalMode = ref("create");
const currentId = ref(null);
const detailItem = ref(null);
const options = reactive({
  complaint_types: []
});
const form = reactive({
  user_id: session.user.id,
  user_name: session.user.name,
  type: "",
  title: "",
  content: "",
  image_url: "",
  status: "待处理",
  reply: ""
});

const filteredItems = computed(() =>
  items.value.filter((item) => !keyword.value || `${item.title}${item.type}${item.status}`.includes(keyword.value))
);

function resetForm() {
  Object.assign(form, {
    user_id: session.user.id,
    user_name: session.user.name,
    type: options.complaint_types[0] || "",
    title: "",
    content: "",
    image_url: "",
    status: "待处理",
    reply: ""
  });
}

function openCreate() {
  modalMode.value = "create";
  currentId.value = null;
  resetForm();
  modalVisible.value = true;
}

function openEdit(item) {
  closeDetail();
  modalMode.value = "edit";
  currentId.value = item.id;
  Object.assign(form, item);
  modalVisible.value = true;
}

function closeModal() {
  modalVisible.value = false;
}

async function loadData() {
  const [complaintRes, optionRes] = await Promise.all([fetchComplaints(), fetchOptions()]);
  items.value = complaintRes.data.filter((item) => item.user_id === session.user.id);
  Object.assign(options, optionRes.data);
}

async function submitModal() {
  if (modalMode.value === "create") {
    await createComplaint(form);
  } else {
    await updateComplaint(currentId.value, form);
  }
  closeModal();
  await loadData();
}

function openDetail(item) {
  detailItem.value = item;
}

function closeDetail() {
  detailItem.value = null;
}

function canEdit(item) {
  return item.status === "待处理";
}

function canCancel(item) {
  return ["待处理", "处理中", "已回复"].includes(item.status);
}

async function cancelComplaint(item) {
  await updateComplaint(item.id, {
    ...item,
    status: "已撤销"
  });
  closeDetail();
  await loadData();
}

function displayStatus(status) {
  if (status === "待处理") {
    return "待处理";
  }
  if (["处理中", "已回复"].includes(status)) {
    return "处理中";
  }
  if (status === "已关闭") {
    return "已结束";
  }
  if (status === "已撤销") {
    return "已取消";
  }
  return status;
}

onMounted(loadData);
</script>
