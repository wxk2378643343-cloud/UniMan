<template>
  <UserPortalLayout
    title="我的报修"
    description="按服务记录查看提交、受理、处理和待确认状态，提交入口放在页面正面区域，不再混进后台式导航。"
  >
    <template #hero-aside>
      <article class="portal-hero-panel">
        <span>服务说明</span>
        <strong>提交后自动进入受理队列</strong>
        <small>可编辑未完结工单，并在完成后发起评价</small>
      </article>
    </template>

    <section class="table-toolbar">
      <div class="toolbar-group toolbar-single">
        <input v-model="keyword" placeholder="搜索工单号/类型/位置" />
      </div>
      <button class="primary-button" @click="openCreate">提交报修</button>
    </section>

    <section class="panel-card">
      <div class="card-intro">
        <h3>报修记录</h3>
        <p>可查看进度、补充描述，并对已处理完成的工单进行评价。</p>
      </div>
      <div class="service-list">
        <article
          v-for="item in filteredItems"
          :key="item.id"
          class="service-card service-card-interactive user-record-card"
          @click="openDetail(item)"
        >
          <div class="service-card-head">
            <div>
              <strong>{{ item.order_no }}</strong>
              <span>{{ item.repair_type }}</span>
            </div>
            <span class="tag">{{ displayStatus(item.status) }}</span>
          </div>
          <p>{{ item.campus }} / {{ item.building }} / {{ item.room }}</p>
          <p>{{ item.description }}</p>
          <small>处理人：{{ item.assignee_name }}</small>
          <div class="service-actions service-actions-bottom">
            <button class="table-button" @click.stop="openDetail(item)">查看详情</button>
            <button v-if="canEdit(item)" class="table-button" @click.stop="openEdit(item)">编辑</button>
            <button v-if="canCancel(item)" class="table-button danger-button" @click.stop="cancelRepair(item)">取消报修</button>
            <button v-if="canEvaluate(item)" class="table-button" @click.stop="openEvaluation(item)">评价</button>
          </div>
        </article>
      </div>
    </section>

    <div v-if="detailItem" class="modal-mask" @click.self="closeDetail">
      <div class="modal-card modal-card-compact">
        <div class="modal-header">
          <h3>{{ detailItem.order_no }}</h3>
          <button class="modal-close" @click="closeDetail">×</button>
        </div>
        <div class="modal-body form-grid">
          <div class="detail-summary-row">
            <span class="tag">{{ displayStatus(detailItem.status) }}</span>
            <small>提交时间：{{ detailItem.created_at }}</small>
          </div>
          <div class="detail-grid">
            <div class="field-block">
              <span class="field-label">报修类型</span>
              <div class="detail-value">{{ detailItem.repair_type }}</div>
            </div>
            <div class="field-block">
              <span class="field-label">处理人</span>
              <div class="detail-value">{{ detailItem.assignee_name }}</div>
            </div>
            <div class="field-block">
              <span class="field-label">当前进度</span>
              <div class="detail-value">{{ displayStatus(detailItem.status) }}</div>
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">报修地点</span>
              <div class="detail-value">{{ detailItem.campus }} / {{ detailItem.building }} / {{ detailItem.room }}</div>
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">问题描述</span>
              <div class="detail-value">{{ detailItem.description }}</div>
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">处理结果</span>
              <div class="detail-value">{{ detailItem.result || "暂未填写处理结果" }}</div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="secondary-button" @click="closeDetail">关闭</button>
          <button v-if="canEdit(detailItem)" type="button" class="table-button" @click="openEdit(detailItem)">编辑</button>
          <button v-if="canCancel(detailItem)" type="button" class="table-button danger-button" @click="cancelRepair(detailItem)">取消报修</button>
          <button v-if="canEvaluate(detailItem)" type="button" class="primary-button" @click="openEvaluation(detailItem)">评价</button>
        </div>
      </div>
    </div>

    <div v-if="modalVisible" class="modal-mask" @click.self="closeModal">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ modalMode === "create" ? "提交报修" : "编辑报修" }}</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="modal-body form-grid form-grid-2">
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
              <span class="field-label">房间号</span>
              <input v-model="form.room" />
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">问题描述</span>
              <textarea v-model="form.description" rows="4"></textarea>
            </div>
            <div class="field-block">
              <span class="field-label">联系电话</span>
              <input v-model="form.contact_phone" />
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="secondary-button" @click="closeModal">取消</button>
            <button type="submit" class="primary-button">保存</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="evaluationVisible" class="modal-mask" @click.self="closeEvaluation">
      <div class="modal-card modal-card-compact">
        <div class="modal-header">
          <h3>服务评价</h3>
          <button class="modal-close" @click="closeEvaluation">×</button>
        </div>
        <form @submit.prevent="submitEvaluation">
          <div class="modal-body form-grid">
            <div class="field-block">
              <span class="field-label">评分</span>
              <select v-model="evaluationForm.score">
                <option :value="5">5分</option>
                <option :value="4">4分</option>
                <option :value="3">3分</option>
                <option :value="2">2分</option>
                <option :value="1">1分</option>
              </select>
            </div>
            <div class="field-block">
              <span class="field-label">评价内容</span>
              <textarea v-model="evaluationForm.comment" rows="4"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="secondary-button" @click="closeEvaluation">取消</button>
            <button type="submit" class="primary-button">提交评价</button>
          </div>
        </form>
      </div>
    </div>
  </UserPortalLayout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { getSession } from "../auth";
import { createEvaluation, createRepair, fetchEvaluations, fetchOptions, fetchRepairs, updateRepair } from "../api";
import UserPortalLayout from "../components/UserPortalLayout.vue";

const session = getSession();
const items = ref([]);
const keyword = ref("");
const modalVisible = ref(false);
const modalMode = ref("create");
const currentId = ref(null);
const currentRepair = ref(null);
const detailItem = ref(null);
const evaluationVisible = ref(false);
const evaluatedRepairIds = ref(new Set());
const options = reactive({
  repair_types: [],
  campuses: [],
  buildings: []
});
const form = reactive({
  reporter_id: session.user.id,
  reporter_name: session.user.name,
  repair_type: "",
  campus: "",
  building: "",
  room: "",
  description: "",
  contact_phone: session.user.phone,
  image_url: "",
  status: "待受理",
  assignee_id: null,
  assignee_name: "未分配",
  result: ""
});
const evaluationForm = reactive({
  score: 5,
  comment: ""
});

const buildingOptions = computed(() => options.buildings.filter((item) => item.parent_name === form.campus));
const filteredItems = computed(() =>
  items.value.filter((item) => !keyword.value || `${item.order_no}${item.repair_type}${item.building}${item.room}`.includes(keyword.value))
);

function resetForm() {
  Object.assign(form, {
    reporter_id: session.user.id,
    reporter_name: session.user.name,
    repair_type: options.repair_types[0] || "",
    campus: options.campuses[0] || "",
    building: options.buildings[0]?.name || "",
    room: "",
    description: "",
    contact_phone: session.user.phone,
    image_url: "",
    status: "待受理",
    assignee_id: null,
    assignee_name: "未分配",
    result: ""
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

function openEvaluation(item) {
  closeDetail();
  currentRepair.value = item;
  Object.assign(evaluationForm, { score: 5, comment: "" });
  evaluationVisible.value = true;
}

function closeEvaluation() {
  evaluationVisible.value = false;
}

async function loadData() {
  const [repairRes, optionRes, evaluationRes] = await Promise.all([fetchRepairs(), fetchOptions(), fetchEvaluations()]);
  items.value = repairRes.data.filter((item) => item.reporter_id === session.user.id);
  Object.assign(options, optionRes.data);
  evaluatedRepairIds.value = new Set(
    evaluationRes.data.filter((item) => item.user_id === session.user.id).map((item) => item.repair_id)
  );
}

async function submitModal() {
  if (modalMode.value === "create") {
    await createRepair(form);
  } else {
    await updateRepair(currentId.value, form);
  }
  closeModal();
  await loadData();
}

async function submitEvaluation() {
  await createEvaluation({
    repair_id: currentRepair.value.id,
    user_id: session.user.id,
    user_name: session.user.name,
    assignee_id: currentRepair.value.assignee_id,
    assignee_name: currentRepair.value.assignee_name,
    score: evaluationForm.score,
    comment: evaluationForm.comment
  });
  closeEvaluation();
  await loadData();
}

function openDetail(item) {
  detailItem.value = item;
}

function closeDetail() {
  detailItem.value = null;
}

function canEdit(item) {
  return ["待受理", "已分派"].includes(item.status);
}

function canCancel(item) {
  return ["待受理", "已分派", "处理中", "待确认"].includes(item.status);
}

function canEvaluate(item) {
  return item.status === "已完成" && !evaluatedRepairIds.value.has(item.id);
}

async function cancelRepair(item) {
  await updateRepair(item.id, {
    ...item,
    status: "已取消"
  });
  closeDetail();
  await loadData();
}

function displayStatus(status) {
  if (["待受理", "已分派"].includes(status)) {
    return "待处理";
  }
  if (["处理中", "待确认"].includes(status)) {
    return "处理中";
  }
  if (status === "已完成") {
    return "已结束";
  }
  if (status === "已取消") {
    return "已取消";
  }
  return status;
}

onMounted(loadData);
</script>
