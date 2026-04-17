<template>
  <AppShell title="基础数据管理" eyebrow="管理后台" mode="admin">
    <section class="table-toolbar">
      <div class="toolbar-group">
        <input v-model="keyword" placeholder="搜索名称/上级名称" />
        <select v-model="typeFilter">
          <option value="">全部分类</option>
          <option v-for="item in typeOptions" :key="item">{{ item }}</option>
        </select>
      </div>
      <button class="primary-button" @click="openCreate">新增数据</button>
    </section>

    <section class="panel-card">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>分类</th>
              <th>名称</th>
              <th>上级名称</th>
              <th>状态</th>
              <th>备注</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredItems" :key="item.id">
              <td>{{ item.data_type }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.parent_name || "-" }}</td>
              <td><span class="tag">{{ item.status }}</span></td>
              <td>{{ item.extra || "-" }}</td>
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
      <div class="modal-card modal-card-compact">
        <div class="modal-header">
          <h3>{{ modalMode === "create" ? "新增基础数据" : "编辑基础数据" }}</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="modal-body form-grid form-grid-2">
            <div class="field-block">
              <span class="field-label">数据分类</span>
              <select v-model="form.data_type">
                <option v-for="item in typeOptions" :key="item">{{ item }}</option>
              </select>
            </div>
            <div class="field-block">
              <span class="field-label">名称</span>
              <input v-model="form.name" />
            </div>
            <div class="field-block">
              <span class="field-label">上级名称</span>
              <input v-model="form.parent_name" />
            </div>
            <div class="field-block">
              <span class="field-label">状态</span>
              <select v-model="form.status">
                <option>启用</option>
                <option>停用</option>
              </select>
            </div>
            <div class="field-block field-span-2">
              <span class="field-label">备注</span>
              <input v-model="form.extra" />
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
import { createBaseData, deleteBaseData, fetchBaseData, updateBaseData } from "../api";
import AppShell from "../components/AppShell.vue";

const items = ref([]);
const keyword = ref("");
const typeFilter = ref("");
const modalVisible = ref(false);
const modalMode = ref("create");
const currentId = ref(null);
const typeOptions = ["repair_type", "complaint_type", "campus", "building", "department"];
const form = reactive({
  data_type: "repair_type",
  name: "",
  parent_name: "",
  status: "启用",
  extra: ""
});

const filteredItems = computed(() =>
  items.value.filter((item) => {
    const hitKeyword = !keyword.value || `${item.name}${item.parent_name}`.includes(keyword.value);
    const hitType = !typeFilter.value || item.data_type === typeFilter.value;
    return hitKeyword && hitType;
  })
);

function resetForm() {
  Object.assign(form, {
    data_type: "repair_type",
    name: "",
    parent_name: "",
    status: "启用",
    extra: ""
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
  const { data } = await fetchBaseData();
  items.value = data;
}

async function submitModal() {
  if (modalMode.value === "create") {
    await createBaseData(form);
  } else {
    await updateBaseData(currentId.value, form);
  }
  closeModal();
  await loadData();
}

async function removeItem(id) {
  await deleteBaseData(id);
  await loadData();
}

onMounted(loadData);
</script>
