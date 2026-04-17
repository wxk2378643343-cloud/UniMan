<template>
  <AppShell title="用户管理" eyebrow="管理后台" mode="admin">
    <section class="table-toolbar">
      <div class="toolbar-group">
        <input v-model="keyword" placeholder="搜索账号/姓名/部门" />
        <select v-model="roleFilter">
          <option value="">全部角色</option>
          <option v-for="item in options.roles" :key="item">{{ item }}</option>
        </select>
      </div>
      <button class="primary-button" @click="openCreate">新增用户</button>
    </section>

    <section class="panel-card">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>账号</th>
              <th>姓名</th>
              <th>角色</th>
              <th>部门</th>
              <th>手机号</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredItems" :key="item.id">
              <td>{{ item.username }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.role }}</td>
              <td>{{ item.department }}</td>
              <td>{{ item.phone }}</td>
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
          <h3>{{ modalMode === "create" ? "新增用户" : "编辑用户" }}</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="modal-body form-grid form-grid-2">
            <div class="field-block">
              <span class="field-label">登录账号</span>
              <input v-model="form.username" />
            </div>
            <div class="field-block">
              <span class="field-label">登录密码</span>
              <input v-model="form.password" />
            </div>
            <div class="field-block">
              <span class="field-label">姓名</span>
              <input v-model="form.name" />
            </div>
            <div class="field-block">
              <span class="field-label">用户角色</span>
              <select v-model="form.role">
                <option v-for="item in options.roles" :key="item">{{ item }}</option>
              </select>
            </div>
            <div class="field-block">
              <span class="field-label">手机号</span>
              <input v-model="form.phone" />
            </div>
            <div class="field-block">
              <span class="field-label">邮箱</span>
              <input v-model="form.email" />
            </div>
            <div class="field-block">
              <span class="field-label">院系/部门</span>
              <select v-model="form.department">
                <option v-for="item in options.departments" :key="item">{{ item }}</option>
              </select>
            </div>
            <div class="field-block">
              <span class="field-label">账号状态</span>
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
import { createUser, deleteUser, fetchOptions, fetchUsers, updateUser } from "../api";
import AppShell from "../components/AppShell.vue";

const items = ref([]);
const keyword = ref("");
const roleFilter = ref("");
const modalVisible = ref(false);
const modalMode = ref("create");
const currentId = ref(null);
const options = reactive({
  roles: [],
  departments: []
});
const form = reactive({
  username: "",
  password: "",
  name: "",
  role: "普通用户",
  phone: "",
  email: "",
  department: "",
  status: "启用"
});

const filteredItems = computed(() =>
  items.value.filter((item) => {
    const hitKeyword = !keyword.value || `${item.username}${item.name}${item.department}`.includes(keyword.value);
    const hitRole = !roleFilter.value || item.role === roleFilter.value;
    return hitKeyword && hitRole;
  })
);

function resetForm() {
  Object.assign(form, {
    username: "",
    password: "",
    name: "",
    role: options.roles[0] || "普通用户",
    phone: "",
    email: "",
    department: options.departments[0] || "",
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
  const [userRes, optionRes] = await Promise.all([fetchUsers(), fetchOptions()]);
  items.value = userRes.data;
  Object.assign(options, optionRes.data);
}

async function submitModal() {
  if (modalMode.value === "create") {
    await createUser(form);
  } else {
    await updateUser(currentId.value, form);
  }
  closeModal();
  await loadData();
}

async function removeItem(id) {
  await deleteUser(id);
  await loadData();
}

onMounted(loadData);
</script>
