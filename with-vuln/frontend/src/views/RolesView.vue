<template>
  <AppShell title="角色管理">
    <section class="table-toolbar">
      <div class="toolbar-group toolbar-single">
        <input v-model="keyword" placeholder="搜索角色名/编码/权限点" />
      </div>
      <button class="primary-button" @click="openCreate">新增角色</button>
    </section>

    <section class="panel-card">
      <div class="panel-head"><h3>角色列表</h3></div>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>角色名</th>
              <th>编码</th>
              <th>权限点</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredRoles" :key="item.id">
              <td>#{{ item.id }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.code }}</td>
              <td class="cell-ellipsis" :title="item.permissions">{{ item.permissions }}</td>
              <td><span class="tag">{{ item.status }}</span></td>
              <td><button class="table-button" @click="openEdit(item)">编辑</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="modalVisible" class="modal-mask" @click.self="closeModal">
      <div class="modal-card">
        <div class="modal-header">
          <h3>{{ modalMode === 'create' ? '新增角色' : '编辑角色' }}</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="modal-body form-grid form-grid-2">
            <input v-model="modalForm.name" placeholder="角色名称" />
            <input v-model="modalForm.code" placeholder="角色编码" />
            <div class="field-block field-span-2">
              <span class="field-label">权限点</span>
              <div class="multi-select-grid">
                <label v-for="item in permissionOptions" :key="item" class="check-chip">
                  <input v-model="selectedPermissions" type="checkbox" :value="item" />
                  <span>{{ item }}</span>
                </label>
              </div>
            </div>
            <select v-model="modalForm.status">
              <option>启用</option>
              <option>停用</option>
            </select>
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
import { createRole, fetchRoles, updateRole } from "../api";
import AppShell from "../components/AppShell.vue";

const roles = ref([]);
const keyword = ref("");
const modalVisible = ref(false);
const modalMode = ref("create");
const currentId = ref(null);
const permissionOptions = [
  "用户管理",
  "角色管理",
  "工单管理",
  "投诉建议",
  "公告管理",
  "统计分析"
];
const emptyForm = () => ({
  name: "",
  code: "",
  permissions: "",
  status: "启用"
});
const modalForm = reactive(emptyForm());
const selectedPermissions = ref([]);

const filteredRoles = computed(() =>
  roles.value.filter((item) =>
    !keyword.value || `${item.name}${item.code}${item.permissions}`.includes(keyword.value)
  )
);

function resetForm() {
  Object.assign(modalForm, emptyForm());
  selectedPermissions.value = [];
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
  selectedPermissions.value = item.permissions ? item.permissions.split(",").map((v) => v.trim()) : [];
  modalVisible.value = true;
}

function closeModal() {
  modalVisible.value = false;
}

async function loadRoles() {
  const { data } = await fetchRoles();
  roles.value = data;
}

async function submitModal() {
  modalForm.permissions = selectedPermissions.value.join(", ");
  if (modalMode.value === "create") {
    await createRole(modalForm);
  } else {
    await updateRole(currentId.value, modalForm);
  }
  closeModal();
  await loadRoles();
}

onMounted(loadRoles);
</script>
