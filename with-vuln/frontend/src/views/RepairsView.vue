<template>
  <AppShell title="报修管理" eyebrow="管理后台" mode="admin">
    <section class="table-toolbar">
      <div class="toolbar-group">
        <input v-model="keyword" placeholder="搜索工单号/报修人/地点" />
        <select v-model="statusFilter">
          <option value="">全部状态</option>
          <option v-for="item in options.repair_statuses" :key="item">{{ item }}</option>
        </select>
      </div>
      <button v-if="isAdmin" class="primary-button" @click="openCreate">新增工单</button>
    </section>

    <section class="panel-card">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>工单号</th>
              <th>报修人</th>
              <th>位置</th>
              <th>类型</th>
              <th>状态</th>
              <th>处理人</th>
              <th>联系电话</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredRepairs" :key="item.id">
              <td>{{ item.order_no }}</td>
              <td>{{ item.reporter_name }}</td>
              <td>{{ item.campus }} / {{ item.building }} / {{ item.room }}</td>
              <td>{{ item.repair_type }}</td>
              <td><span class="tag">{{ item.status }}</span></td>
              <td>{{ item.assignee_name }}</td>
              <td>{{ item.contact_phone }}</td>
              <td class="table-actions">
                <button v-if="isAdmin" class="table-button" @click="openEdit(item)">编辑</button>
                <button v-if="isAdmin" class="table-button danger-button" @click="removeItem(item.id)">删除</button>
                <button v-if="canWorkerConfirm(item)" class="table-button" @click="confirmRepair(item)">确认</button>
                <button v-if="canWorkerFinish(item)" class="table-button" @click="openFinish(item)">已处理</button>
                <button v-if="canWorkerCancel(item)" class="table-button danger-button" @click="openCancel(item, 'worker')">取消</button>
                <button v-if="isAdmin" class="table-button danger-button" @click="openCancel(item, 'admin')">管理员取消</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="modalVisible" class="modal-mask" @click.self="closeModal">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ modalMode === "create" ? "新增报修" : "编辑报修" }}</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="modal-body form-grid form-grid-2">
            <div class="field-block">
              <span class="field-label">报修人</span>
              <select v-model="form.reporter_id" @change="syncReporter">
                <option v-for="item in userOptions" :key="item.id" :value="item.id">{{ item.name }}</option>
              </select>
            </div>
            <div class="field-block">
              <span class="field-label">报修类型</span>
              <select v-model="form.repair_type">
                <option v-for="item in options.repair_types" :key="item">{{ item }}</option>
              </select>
            </div>
            <div class="field-block">
              <span class="field-label">校区</span>
              <select v-model="form.campus">
                <option v-for="item in options.campuses" :key="item">{{ item }}</option>
              </select>
            </div>
            <div class="field-block">
              <span class="field-label">楼栋</span>
              <select v-model="form.building">
                <option v-for="item in buildingOptions" :key="item.name">{{ item.name }}</option>
              </select>
            </div>
            <div class="field-block">
              <span class="field-label">房间</span>
              <input v-model="form.room" />
            </div>
            <div class="field-block">
              <span class="field-label">联系电话</span>
              <input v-model="form.contact_phone" />
            </div>
            <div class="field-block">
              <span class="field-label">状态</span>
              <select v-model="form.status">
                <option v-for="item in options.repair_statuses" :key="item">{{ item }}</option>
              </select>
            </div>
            <div class="field-block">
              <span class="field-label">处理人</span>
              <select v-model="form.assignee_id" @change="syncWorker">
                <option :value="null">未分配</option>
                <option v-for="item in options.workers" :key="item.id" :value="item.id">{{ item.name }}</option>
              </select>
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">问题描述</span>
              <textarea v-model="form.description" rows="4"></textarea>
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">处理结果</span>
              <textarea v-model="form.result" rows="3"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="secondary-button" @click="closeModal">取消</button>
            <button type="submit" class="primary-button">确定</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="cancelVisible" class="modal-mask" @click.self="closeCancel">
      <div class="modal-card modal-card-compact">
        <div class="modal-header">
          <h3>{{ cancelMode === "admin" ? "管理员取消工单" : "取消当前处理" }}</h3>
          <button class="modal-close" @click="closeCancel">×</button>
        </div>
        <form @submit.prevent="submitCancel">
          <div class="modal-body form-grid">
            <div class="field-block">
              <span class="field-label">取消原因</span>
              <textarea v-model="cancelReason" rows="4" placeholder="请填写取消原因"></textarea>
            </div>
            <small v-if="cancelMode === 'worker'" class="status-text">
              取消后，工单将退回待受理，等待重新安排处理人员。
            </small>
            <small v-else class="status-text">
              管理员取消后，表示该工单确认不需要修复，工单将终止。
            </small>
          </div>
          <div class="modal-footer">
            <button type="button" class="secondary-button" @click="closeCancel">返回</button>
            <button type="submit" class="primary-button">确认</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="finishVisible" class="modal-mask" @click.self="closeFinish">
      <div class="modal-card modal-card-compact">
        <div class="modal-header">
          <h3>提交处理结果</h3>
          <button class="modal-close" @click="closeFinish">×</button>
        </div>
        <form @submit.prevent="submitFinish">
          <div class="modal-body form-grid">
            <div class="field-block">
              <span class="field-label">处理结果</span>
              <textarea v-model="finishResult" rows="4" placeholder="请填写本次处理结果"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="secondary-button" @click="closeFinish">返回</button>
            <button type="submit" class="primary-button">确认提交</button>
          </div>
        </form>
      </div>
    </div>
  </AppShell>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { getSession } from "../auth";
import { createRepair, deleteRepair, fetchOptions, fetchRepairs, fetchUsers, updateRepair } from "../api";
import AppShell from "../components/AppShell.vue";

const session = getSession();
const isAdmin = session.user.role === "系统管理员";
const isWorker = session.user.role === "后勤人员";
const repairs = ref([]);
const keyword = ref("");
const statusFilter = ref("");
const modalVisible = ref(false);
const modalMode = ref("create");
const currentId = ref(null);
const cancelVisible = ref(false);
const cancelTarget = ref(null);
const cancelMode = ref("worker");
const cancelReason = ref("");
const finishVisible = ref(false);
const finishTarget = ref(null);
const finishResult = ref("");
const options = reactive({
  repair_types: [],
  campuses: [],
  buildings: [],
  workers: [],
  repair_statuses: []
});
const userOptions = ref([]);
const form = reactive({
  reporter_id: null,
  reporter_name: "",
  repair_type: "",
  campus: "",
  building: "",
  room: "",
  description: "",
  contact_phone: "",
  image_url: "",
  status: "待受理",
  assignee_id: null,
  assignee_name: "未分配",
  result: "",
  cancel_reason: "",
  cancel_source: ""
});

const buildingOptions = computed(() => options.buildings.filter((item) => item.parent_name === form.campus));
const filteredRepairs = computed(() =>
  repairs.value.filter((item) => {
    const hitKeyword = !keyword.value || `${item.order_no}${item.reporter_name}${item.campus}${item.building}${item.room}`.includes(keyword.value);
    const hitStatus = !statusFilter.value || item.status === statusFilter.value;
    return hitKeyword && hitStatus;
  })
);

function resetForm() {
  Object.assign(form, {
    reporter_id: userOptions.value[0]?.id || null,
    reporter_name: userOptions.value[0]?.name || "",
    repair_type: options.repair_types[0] || "",
    campus: options.campuses[0] || "",
    building: options.buildings[0]?.name || "",
    room: "",
    description: "",
    contact_phone: "",
    image_url: "",
    status: "待受理",
    assignee_id: null,
    assignee_name: "未分配",
    result: ""
  });
}

function syncReporter() {
  const current = userOptions.value.find((item) => item.id === Number(form.reporter_id));
  if (current) {
    form.reporter_name = current.name;
    form.contact_phone = current.phone;
  }
}

function syncWorker() {
  const worker = options.workers.find((item) => item.id === Number(form.assignee_id));
  form.assignee_name = worker?.name || "未分配";
}

function openCreate() {
  if (!isAdmin) {
    return;
  }
  modalMode.value = "create";
  currentId.value = null;
  resetForm();
  syncReporter();
  modalVisible.value = true;
}

function openEdit(item) {
  if (!isAdmin) {
    return;
  }
  modalMode.value = "edit";
  currentId.value = item.id;
  Object.assign(form, item);
  modalVisible.value = true;
}

function closeModal() {
  modalVisible.value = false;
}

async function loadData() {
  const [repairRes, optionRes, userRes] = await Promise.all([fetchRepairs(), fetchOptions(), fetchUsers()]);
  repairs.value = isWorker
    ? repairRes.data.filter((item) => Number(item.assignee_id) === Number(session.user.id))
    : repairRes.data;
  Object.assign(options, optionRes.data);
  userOptions.value = userRes.data.filter((item) => item.role === "普通用户");
  if (!form.reporter_id) {
    resetForm();
  }
}

async function submitModal() {
  syncReporter();
  syncWorker();
  if (modalMode.value === "create") {
    await createRepair(form);
  } else {
    await updateRepair(currentId.value, form);
  }
  closeModal();
  await loadData();
}

async function removeItem(id) {
  await deleteRepair(id);
  await loadData();
}

function canWorkerConfirm(item) {
  return isWorker && item.status === "已分派" && Number(item.assignee_id) === Number(session.user.id);
}

function canWorkerFinish(item) {
  return isWorker && item.status === "处理中" && Number(item.assignee_id) === Number(session.user.id);
}

function canWorkerCancel(item) {
  return (
    isWorker &&
    ["已分派", "处理中"].includes(item.status) &&
    Number(item.assignee_id) === Number(session.user.id)
  );
}

async function confirmRepair(item) {
  await updateRepair(item.id, {
    ...item,
    status: "处理中"
  });
  await loadData();
}

function openFinish(item) {
  finishTarget.value = item;
  finishResult.value = item.result || "";
  finishVisible.value = true;
}

function closeFinish() {
  finishVisible.value = false;
  finishTarget.value = null;
  finishResult.value = "";
}

function openCancel(item, mode) {
  cancelTarget.value = item;
  cancelMode.value = mode;
  cancelReason.value = "";
  cancelVisible.value = true;
}

function closeCancel() {
  cancelVisible.value = false;
  cancelTarget.value = null;
  cancelReason.value = "";
}

async function submitCancel() {
  if (!cancelTarget.value || !cancelReason.value.trim()) {
    return;
  }

  const nextPayload =
    cancelMode.value === "admin"
      ? {
          ...cancelTarget.value,
          status: "已取消",
          cancel_reason: cancelReason.value.trim(),
          cancel_source: "admin"
        }
      : {
          ...cancelTarget.value,
          status: "待受理",
          assignee_id: null,
          assignee_name: "未分配",
          cancel_reason: cancelReason.value.trim(),
          cancel_source: "worker"
        };

  await updateRepair(cancelTarget.value.id, nextPayload);
  closeCancel();
  await loadData();
}

async function submitFinish() {
  if (!finishTarget.value || !finishResult.value.trim()) {
    return;
  }
  await updateRepair(finishTarget.value.id, {
    ...finishTarget.value,
    status: "待确认",
    result: finishResult.value.trim()
  });
  closeFinish();
  await loadData();
}

onMounted(loadData);
</script>
