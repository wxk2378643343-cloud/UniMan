<template>
  <AppShell title="角色管理" eyebrow="管理后台" mode="admin">
    <section class="table-toolbar">
      <div class="toolbar-group toolbar-single">
        <input v-model="keyword" placeholder="搜索角色名称/编码" />
      </div>
      <button class="primary-button" @click="openCreate">新增角色</button>
    </section>

    <section class="panel-card">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>角色名称</th>
              <th>角色编码</th>
              <th>说明</th>
              <th>菜单权限</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredItems" :key="item.id">
              <td>{{ item.name }}</td>
              <td>{{ item.code }}</td>
              <td>{{ item.description }}</td>
              <td class="cell-ellipsis">{{ item.permissions }}</td>
              <td><span class="tag">{{ item.status }}</span></td>
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
          <h3>{{ modalMode === "create" ? "新增角色" : "编辑角色" }}</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="modal-body form-grid form-grid-2">
            <div class="field-block">
              <span class="field-label">角色名称</span>
              <input v-model="form.name" />
            </div>
            <div class="field-block">
              <span class="field-label">角色编码</span>
              <input v-model="form.code" />
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">角色说明</span>
              <input v-model="form.description" />
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">菜单权限</span>
              <textarea v-model="form.permissions" rows="4"></textarea>
            </div>
            <div class="field-block">
              <span class="field-label">状态</span>
              <select v-model="form.status">
                <option>启用</option>
                <option>停用</option>
              </select>
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
import { createRole, deleteRole, fetchRoles, updateRole } from "../api";
import AppShell from "../components/AppShell.vue";

const items = ref([]);
const keyword = ref("");
const modalVisible = ref(false);
const modalMode = ref("create");
const currentId = ref(null);
const form = reactive({
  name: "",
  code: "",
  description: "",
  permissions: "",
  status: "启用"
});

const filteredItems = computed(() =>
  items.value.filter((item) => !keyword.value || `${item.name}${item.code}`.includes(keyword.value))
);

function resetForm() {
  Object.assign(form, {
    name: "",
    code: "",
    description: "",
    permissions: "",
    status: "启用"
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
  const { data } = await fetchRoles();
  items.value = data;
}

async function submitModal() {
  if (modalMode.value === "create") {
    await createRole(form);
  } else {
    await updateRole(currentId.value, form);
  }
  closeModal();
  await loadData();
}

async function removeItem(id) {
  await deleteRole(id);
  await loadData();
}

onMounted(loadData);
</script>
