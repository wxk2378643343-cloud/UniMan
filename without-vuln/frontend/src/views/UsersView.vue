<template>
  <AppShell title="用户管理">
    <section class="table-toolbar">
      <div class="toolbar-group">
        <input v-model="keyword" placeholder="搜索用户名/姓名/部门" />
        <select v-model="roleFilter">
          <option value="">全部角色</option>
          <option v-for="role in roles" :key="role.id" :value="role.name">{{ role.name }}</option>
        </select>
      </div>
      <button class="primary-button" @click="openCreate">新增用户</button>
    </section>

    <section class="panel-card">
      <div class="panel-head"><h3>用户列表</h3></div>
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>用户名</th>
              <th>姓名</th>
              <th>角色</th>
              <th>部门</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredUsers" :key="item.id">
              <td>#{{ item.id }}</td>
              <td>{{ item.username }}</td>
              <td>{{ item.display_name }}</td>
              <td>{{ item.role }}</td>
              <td>{{ item.department }}</td>
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
          <h3>{{ modalMode === 'create' ? '新增用户' : '编辑用户' }}</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="modal-body form-grid form-grid-2">
            <input v-model="modalForm.username" placeholder="用户名" />
            <input v-model="modalForm.password" type="password" :placeholder="modalMode === 'create' ? '密码' : '新密码（留空则不修改）'" />
            <input v-model="modalForm.display_name" placeholder="姓名" />
            <select v-model="modalForm.department">
              <option v-for="item in departmentOptions" :key="item">{{ item }}</option>
            </select>
            <select v-model="modalForm.role">
              <option v-for="role in roles" :key="role.id" :value="role.name">{{ role.name }}</option>
            </select>
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
import { createUser, fetchRoles, fetchUsers, updateUser } from "../api";
import AppShell from "../components/AppShell.vue";

const users = ref([]);
const roles = ref([]);
const keyword = ref("");
const roleFilter = ref("");
const modalVisible = ref(false);
const modalMode = ref("create");
const currentId = ref(null);
const departmentOptions = ["信息中心", "维修中心", "后勤保障处", "宿舍管理中心", "网信办", "计算机学院"];
const emptyForm = () => ({
  username: "",
  password: "",
  role: "学生",
  display_name: "",
  department: "后勤保障处",
  status: "启用"
});
const modalForm = reactive(emptyForm());

const filteredUsers = computed(() =>
  users.value.filter((item) => {
    const keywordMatched =
      !keyword.value || `${item.username}${item.display_name}${item.department}`.includes(keyword.value);
    const roleMatched = !roleFilter.value || item.role === roleFilter.value;
    return keywordMatched && roleMatched;
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
  resetForm();
  Object.assign(modalForm, item);
  modalForm.password = "";
  modalVisible.value = true;
}

function closeModal() {
  modalVisible.value = false;
}

async function loadAll() {
  const [usersRes, rolesRes] = await Promise.all([fetchUsers(), fetchRoles()]);
  users.value = usersRes.data;
  roles.value = rolesRes.data;
}

async function submitModal() {
  if (modalMode.value === "create") {
    await createUser(modalForm);
  } else {
    await updateUser(currentId.value, modalForm);
  }
  closeModal();
  await loadAll();
}

onMounted(loadAll);
</script>
