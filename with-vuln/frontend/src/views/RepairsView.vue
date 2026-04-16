<template>
  <AppShell title="报修工单">
    <section class="table-toolbar">
      <div class="toolbar-group">
        <input v-model="keyword" placeholder="搜索位置/报修人/类型" />
        <select v-model="statusFilter">
          <option value="">全部状态</option>
          <option>待受理</option>
          <option>已分配</option>
          <option>处理中</option>
          <option>已完成</option>
          <option>已评价</option>
          <option>已关闭</option>
        </select>
      </div>
      <button v-if="canCreate" class="primary-button" @click="openCreate">新增工单</button>
    </section>

    <section class="panel-card">
      <div class="panel-head">
        <h3>工单管理列表</h3>
        <small>{{ tableHint }}</small>
      </div>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>报修人</th>
              <th>位置</th>
              <th>类型</th>
              <th>联系电话</th>
              <th>状态</th>
              <th>处理人</th>
              <th>描述</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredRepairs" :key="item.id">
              <td>#{{ item.id }}</td>
              <td>{{ item.student_name }}</td>
              <td>{{ item.location }}</td>
              <td>{{ item.repair_type }}</td>
              <td>{{ item.contact_phone }}</td>
              <td><span class="tag">{{ item.status }}</span></td>
              <td>{{ item.assignee }}</td>
              <td class="cell-ellipsis" :title="item.description">{{ item.description }}</td>
              <td>
                <button
                  class="table-button"
                  :disabled="!canEdit(item)"
                  @click="openEdit(item)"
                >
                  编辑
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="modalVisible" class="modal-mask" @click.self="closeModal">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ modalMode === 'create' ? '新增工单' : '编辑工单' }}</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="modal-body form-grid form-grid-2">
            <input
              v-model="modalForm.student_name"
              placeholder="报修人姓名"
              :disabled="isStudent || isWorker"
            />
            <input
              v-model="modalForm.location"
              placeholder="故障位置"
              :disabled="isWorker || (isStudent && modalMode === 'edit')"
            />

            <select
              v-model="modalForm.repair_type"
              :disabled="isWorker || (isStudent && modalMode === 'edit')"
            >
              <option v-for="item in repairTypeOptions" :key="item">{{ item }}</option>
            </select>

            <input v-model="modalForm.contact_phone" placeholder="联系电话" :disabled="!(isAdmin || isStudent)" />

            <select v-model="modalForm.assignee" :disabled="!isAdmin">
              <option v-for="item in assigneeOptions" :key="item">{{ item }}</option>
            </select>

            <template v-if="isAdmin">
              <select v-model="modalForm.status">
                <option v-for="item in repairStatusOptions" :key="item">{{ item }}</option>
              </select>
            </template>

            <template v-else-if="isWorker">
              <select v-model="modalForm.status">
                <option>已完成</option>
                <option>已关闭</option>
              </select>
            </template>

            <template v-else>
              <input v-model="modalForm.status" placeholder="状态" disabled />
            </template>

            <div class="field-block">
              <span class="field-label">报修图片</span>
              <input type="file" accept="image/*" :disabled="!canUploadImage" @change="handleFileChange" />
              <button
                type="button"
                class="secondary-button"
                :disabled="!selectedFile || uploading || !canUploadImage"
                @click="submitUpload"
              >
                {{ uploading ? "上传中..." : "上传图片" }}
              </button>
            </div>

            <textarea
              v-model="modalForm.description"
              rows="4"
              placeholder="故障描述"
              :disabled="!(isAdmin || isStudent)"
            ></textarea>

            <div v-if="previewUrl" class="field-block">
              <span class="field-label">图片预览</span>
              <img :src="previewUrl" alt="预览图" class="upload-preview" />
            </div>
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
import { createRepair, fetchRepairs, updateRepair, uploadImage } from "../api";
import AppShell from "../components/AppShell.vue";

const repairs = ref([]);
const keyword = ref("");
const statusFilter = ref("");
const modalVisible = ref(false);
const modalMode = ref("create");
const currentId = ref(null);
const selectedFile = ref(null);
const previewUrl = ref("");
const uploading = ref(false);
const currentRole = localStorage.getItem("role") || "";
const currentDisplayName = localStorage.getItem("displayName") || "";
const isAdmin = currentRole === "系统管理员";
const isStudent = currentRole === "学生";
const isWorker = currentRole === "后勤工作人员";
const canCreate = isAdmin || isStudent;
const canUploadImage = isAdmin || isStudent;

const repairTypeOptions = ["宿舍报修", "公共设施", "教学设备", "餐饮反馈", "网络报修"];
const repairStatusOptions = ["待受理", "已分配", "处理中", "已完成", "已评价", "已关闭"];
const assigneeOptions = ["未分配", "李师傅", "赵师傅", "周师傅", "王师傅"];

const emptyForm = () => ({
  student_name: currentDisplayName,
  location: "",
  repair_type: "宿舍报修",
  description: "",
  contact_phone: "",
  image_url: "",
  status: "待受理",
  assignee: "未分配"
});
const modalForm = reactive(emptyForm());

const visibleRepairs = computed(() => {
  if (isAdmin) {
    return repairs.value;
  }
  if (isStudent) {
    return repairs.value.filter((item) => item.student_name === currentDisplayName);
  }
  if (isWorker) {
    return repairs.value.filter((item) => item.assignee === currentDisplayName);
  }
  return [];
});

const filteredRepairs = computed(() =>
  visibleRepairs.value.filter((item) => {
    const keywordMatched =
      !keyword.value || `${item.student_name}${item.location}${item.repair_type}`.includes(keyword.value);
    const statusMatched = !statusFilter.value || item.status === statusFilter.value;
    return keywordMatched && statusMatched;
  })
);

const tableHint = computed(() => {
  if (isAdmin) return "管理员查看全部工单";
  if (isStudent) return "仅显示当前学生提交的工单";
  if (isWorker) return "仅显示已分配给当前师傅的工单";
  return "";
});

function resetForm() {
  Object.assign(modalForm, emptyForm());
  selectedFile.value = null;
  previewUrl.value = "";
}

function canEdit(item) {
  if (isAdmin) return true;
  if (isStudent) return item.student_name === currentDisplayName;
  if (isWorker) return item.assignee === currentDisplayName;
  return false;
}

function openCreate() {
  if (!canCreate) return;
  modalMode.value = "create";
  currentId.value = null;
  resetForm();
  modalVisible.value = true;
}

function openEdit(item) {
  if (!canEdit(item)) return;
  modalMode.value = "edit";
  currentId.value = item.id;
  Object.assign(modalForm, item);
  previewUrl.value = item.image_url ? `http://127.0.0.1:8000${item.image_url}` : "";
  selectedFile.value = null;
  modalVisible.value = true;
}

function closeModal() {
  modalVisible.value = false;
}

function handleFileChange(event) {
  const [file] = event.target.files || [];
  selectedFile.value = file || null;
  if (file) {
    previewUrl.value = URL.createObjectURL(file);
  }
}

async function submitUpload() {
  if (!selectedFile.value || !canUploadImage) {
    return;
  }
  uploading.value = true;
  try {
    const { data } = await uploadImage(selectedFile.value);
    modalForm.image_url = data.url;
    previewUrl.value = `http://127.0.0.1:8000${data.url}`;
  } finally {
    uploading.value = false;
  }
}

async function loadRepairs() {
  const { data } = await fetchRepairs();
  repairs.value = data;
}

async function submitModal() {
  if (modalMode.value === "create") {
    await createRepair({
      ...modalForm,
      student_name: isStudent ? currentDisplayName : modalForm.student_name,
      status: "待受理",
      assignee: "未分配"
    });
  } else if (isAdmin) {
    await updateRepair(currentId.value, modalForm);
  } else if (isStudent) {
    const current = repairs.value.find((item) => item.id === currentId.value);
    await updateRepair(currentId.value, {
      ...current,
      description: modalForm.description,
      contact_phone: modalForm.contact_phone,
      image_url: modalForm.image_url
    });
  } else if (isWorker) {
    const current = repairs.value.find((item) => item.id === currentId.value);
    await updateRepair(currentId.value, {
      ...current,
      status: modalForm.status
    });
  }

  closeModal();
  await loadRepairs();
}

onMounted(loadRepairs);
</script>
