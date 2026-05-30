<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Download,
  KeyRound,
  MoreHorizontal,
  Pencil,
  Plus,
  Search,
  ShieldCheck,
  Trash2,
  UserCog,
  UsersRound
} from 'lucide-vue-next'

const roleOptions = [
  { value: 'admin', label: '管理员' },
  { value: 'analyst', label: '数据分析员' },
  { value: 'user', label: '普通用户' }
]

const organizations = ['北京新发地', '寿光研发部', '国家农产品监测中心', '郑州万邦监测站', '上海江桥监测点', '成都白家市场', '广州江南市场']

const roleMeta = {
  admin: {
    label: '管理员',
    className: 'role-tag-admin',
    permissions: ['修改系统配置', '手动运行流水线', '用户权限管理', '全量数据导出']
  },
  analyst: {
    label: '数据分析员',
    className: 'role-tag-analyst',
    permissions: ['手动运行流水线', '价格多维分析', '趋势预测复核', '报表导出']
  },
  user: {
    label: '普通用户',
    className: 'role-tag-user',
    permissions: ['查看监控看板', '接收价格预警', '查看采集状态']
  }
}

const userRows = ref([
  {
    id: 1001,
    name: '张经理',
    account: 'zhang.manager',
    email: 'zhang.manager@agripulse.gov.cn',
    phone: '13801080001',
    role: 'admin',
    organization: '北京新发地',
    active: true,
    online: true,
    createdThisWeek: false,
    lastLogin: '2026-05-30 10:32',
    permissions: { editSystem: true, runPipeline: true }
  },
  {
    id: 1002,
    name: '李分析师',
    account: 'li.analysis',
    email: 'li.analysis@agripulse.gov.cn',
    phone: '13901080002',
    role: 'analyst',
    organization: '寿光研发部',
    active: true,
    online: true,
    createdThisWeek: true,
    lastLogin: '2026-05-30 09:58',
    permissions: { editSystem: false, runPipeline: true }
  },
  {
    id: 1003,
    name: '王运营',
    account: 'wang.ops',
    email: 'wang.ops@agripulse.gov.cn',
    phone: '13701080003',
    role: 'user',
    organization: '上海江桥监测点',
    active: true,
    online: false,
    createdThisWeek: false,
    lastLogin: '2026-05-29 18:21',
    permissions: { editSystem: false, runPipeline: false }
  },
  {
    id: 1004,
    name: '赵管理员',
    account: 'zhao.admin',
    email: 'zhao.admin@agripulse.gov.cn',
    phone: '13601080004',
    role: 'admin',
    organization: '国家农产品监测中心',
    active: true,
    online: true,
    createdThisWeek: false,
    lastLogin: '2026-05-30 10:18',
    permissions: { editSystem: true, runPipeline: true }
  },
  {
    id: 1005,
    name: '陈数据',
    account: 'chen.data',
    email: 'chen.data@agripulse.gov.cn',
    phone: '13501080005',
    role: 'analyst',
    organization: '郑州万邦监测站',
    active: true,
    online: false,
    createdThisWeek: true,
    lastLogin: '2026-05-30 08:44',
    permissions: { editSystem: false, runPipeline: true }
  },
  {
    id: 1006,
    name: '刘采集',
    account: 'liu.crawler',
    email: 'liu.crawler@agripulse.gov.cn',
    phone: '13401080006',
    role: 'user',
    organization: '成都白家市场',
    active: false,
    online: false,
    createdThisWeek: false,
    lastLogin: '2026-05-27 16:06',
    permissions: { editSystem: false, runPipeline: false }
  },
  {
    id: 1007,
    name: '周审核',
    account: 'zhou.review',
    email: 'zhou.review@agripulse.gov.cn',
    phone: '13301080007',
    role: 'analyst',
    organization: '广州江南市场',
    active: true,
    online: false,
    createdThisWeek: true,
    lastLogin: '2026-05-29 22:15',
    permissions: { editSystem: false, runPipeline: true }
  }
])

const searchKeyword = ref('')
const roleFilter = ref('all')
const selectedUsers = ref([])
const userFormRef = ref(null)
const dialogVisible = ref(false)
const dialogMode = ref('create')
const deleteDialog = reactive({ visible: false, ids: [], names: [] })

const userForm = reactive({
  id: null,
  name: '',
  account: '',
  email: '',
  phone: '',
  role: 'user',
  organization: '北京新发地',
  active: true,
  permissions: { editSystem: false, runPipeline: false }
})

const formRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  account: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  organization: [{ required: true, message: '请选择所属机构', trigger: 'change' }],
  email: [
    { required: true, message: '请输入电子邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: ['blur', 'change'] }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入 11 位中国大陆手机号', trigger: ['blur', 'change'] }
  ]
}

const filteredUsers = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  return userRows.value.filter((user) => {
    const matchedKeyword = !keyword || [user.name, user.email, user.account].some((value) => value.toLowerCase().includes(keyword))
    const matchedRole = roleFilter.value === 'all' || user.role === roleFilter.value
    return matchedKeyword && matchedRole
  })
})

const stats = computed(() => [
  { label: '总用户数', value: userRows.value.length, note: '覆盖全部监测席位', icon: UsersRound },
  { label: '当前在线人数', value: userRows.value.filter((user) => user.online).length, note: '近 10 分钟活跃', icon: ShieldCheck },
  { label: '本周新增用户', value: userRows.value.filter((user) => user.createdThisWeek).length, note: '已完成权限分配', icon: UserCog }
])

const resetForm = () => {
  Object.assign(userForm, {
    id: null,
    name: '',
    account: '',
    email: '',
    phone: '',
    role: 'user',
    organization: '北京新发地',
    active: true,
    permissions: { editSystem: false, runPipeline: false }
  })
}

const openCreateDialog = () => {
  dialogMode.value = 'create'
  resetForm()
  dialogVisible.value = true
}

const openEditDialog = (user) => {
  dialogMode.value = 'edit'
  Object.assign(userForm, {
    id: user.id,
    name: user.name,
    account: user.account,
    email: user.email,
    phone: user.phone,
    role: user.role,
    organization: user.organization,
    active: user.active,
    permissions: { ...user.permissions }
  })
  dialogVisible.value = true
}

const applyRoleDefaults = (role) => {
  if (role === 'admin') userForm.permissions = { editSystem: true, runPipeline: true }
  if (role === 'analyst') userForm.permissions = { editSystem: false, runPipeline: true }
  if (role === 'user') userForm.permissions = { editSystem: false, runPipeline: false }
}

const submitUserForm = async () => {
  const valid = await userFormRef.value?.validate().catch(() => false)
  if (!valid) return

  if (dialogMode.value === 'create') {
    userRows.value.unshift({
      id: Date.now(),
      name: userForm.name,
      account: userForm.account,
      email: userForm.email,
      phone: userForm.phone,
      role: userForm.role,
      organization: userForm.organization,
      active: userForm.active,
      online: false,
      createdThisWeek: true,
      lastLogin: '尚未登录',
      permissions: { ...userForm.permissions }
    })
    ElMessage.success('新增用户已保存')
  } else {
    const target = userRows.value.find((user) => user.id === userForm.id)
    if (target) {
      Object.assign(target, {
        name: userForm.name,
        account: userForm.account,
        email: userForm.email,
        phone: userForm.phone,
        role: userForm.role,
        organization: userForm.organization,
        active: userForm.active,
        permissions: { ...userForm.permissions }
      })
    }
    ElMessage.success('用户信息已更新')
  }
  dialogVisible.value = false
}

const handleSelectionChange = (selection) => {
  selectedUsers.value = selection
}

const requestDelete = (users) => {
  const targets = Array.isArray(users) ? users : [users]
  deleteDialog.ids = targets.map((user) => user.id)
  deleteDialog.names = targets.map((user) => user.name)
  deleteDialog.visible = true
}

const confirmDelete = () => {
  userRows.value = userRows.value.filter((user) => !deleteDialog.ids.includes(user.id))
  selectedUsers.value = []
  deleteDialog.visible = false
  ElMessage.success('用户已删除')
}

const applyBatchRole = (role) => {
  const selectedIds = selectedUsers.value.map((user) => user.id)
  userRows.value.forEach((user) => {
    if (!selectedIds.includes(user.id)) return
    user.role = role
    user.permissions = {
      editSystem: role === 'admin',
      runPipeline: role !== 'user'
    }
  })
  ElMessage.success(`已批量修改为${roleMeta[role].label}`)
}

const handleRowCommand = (command, user) => {
  if (command === 'reset') {
    ElMessage.success(`已向 ${user.name} 发送密码重置链接`)
  }
  if (command === 'delete') requestDelete(user)
}

const exportUsers = () => {
  ElMessage.success('用户列表导出任务已创建')
}
</script>

<template>
  <div class="user-permission-center space-y-4">
    <section class="grid gap-3 lg:grid-cols-3">
      <article v-for="item in stats" :key="item.label" class="rounded-lg border border-slate-100 bg-white p-4 shadow-sm">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-xs font-medium text-slate-500">{{ item.label }}</p>
            <p class="mt-2 text-2xl font-semibold text-slate-950">{{ item.value }}</p>
            <p class="mt-1 text-xs text-slate-400">{{ item.note }}</p>
          </div>
          <span class="flex h-11 w-11 items-center justify-center rounded-lg bg-emerald-50 text-[#064e3b]">
            <component :is="item.icon" class="h-5 w-5" />
          </span>
        </div>
      </article>
    </section>

    <section class="rounded-lg border border-slate-100 bg-white p-4 shadow-sm">
      <div class="flex flex-col justify-between gap-3 xl:flex-row xl:items-center">
        <div class="flex flex-col gap-3 md:flex-row md:items-center">
          <el-input v-model="searchKeyword" class="toolbar-search" clearable placeholder="按姓名 / 邮箱 / 账号搜索">
            <template #prefix><Search class="h-4 w-4 text-slate-400" /></template>
          </el-input>
          <el-select v-model="roleFilter" class="w-full md:w-[180px]" placeholder="角色筛选">
            <el-option label="全部角色" value="all" />
            <el-option v-for="role in roleOptions" :key="role.value" :label="role.label" :value="role.value" />
          </el-select>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <el-button class="export-button" @click="exportUsers">
            <Download class="mr-1 h-4 w-4" />导出用户列表
          </el-button>
          <el-button type="primary" class="create-button" @click="openCreateDialog">
            <Plus class="mr-1 h-4 w-4" />新增用户
          </el-button>
        </div>
      </div>
    </section>

    <div v-if="selectedUsers.length" class="sticky top-2 z-10 flex flex-col justify-between gap-3 rounded-lg border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm shadow-sm md:flex-row md:items-center">
      <div class="font-medium text-[#064e3b]">已选择 {{ selectedUsers.length }} 个用户</div>
      <div class="flex flex-wrap items-center gap-2">
        <el-dropdown @command="applyBatchRole">
          <el-button class="batch-button">批量修改角色</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-for="role in roleOptions" :key="role.value" :command="role.value">{{ role.label }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="danger" plain @click="requestDelete(selectedUsers)">
          <Trash2 class="mr-1 h-4 w-4" />批量删除
        </el-button>
      </div>
    </div>

    <section class="rounded-lg border border-slate-100 bg-white shadow-sm">
      <el-table :data="filteredUsers" size="small" class="user-table" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="44" />
        <el-table-column label="用户信息" min-width="220">
          <template #default="{ row }">
            <div class="flex items-center gap-3">
              <span class="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-50 text-sm font-semibold text-[#064e3b]">{{ row.name.slice(0, 1) }}</span>
              <span class="min-w-0">
                <span class="block truncate text-sm font-semibold text-slate-950">{{ row.name }}</span>
                <span class="block truncate text-xs text-slate-500">{{ row.account }}</span>
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="所属角色" min-width="118">
          <template #default="{ row }">
            <el-tooltip placement="top" effect="light">
              <template #content>
                <div class="space-y-1 text-xs">
                  <p class="font-semibold text-slate-800">权限列表</p>
                  <p v-for="permission in roleMeta[row.role].permissions" :key="permission">{{ permission }}</p>
                </div>
              </template>
              <el-tag :class="['role-tag', roleMeta[row.role].className]" effect="plain">{{ roleMeta[row.role].label }}</el-tag>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="organization" label="所属机构" min-width="156" />
        <el-table-column label="修改系统配置" min-width="112" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.permissions.editSystem" :disabled="row.role !== 'admin'" />
          </template>
        </el-table-column>
        <el-table-column label="手动运行流水线" min-width="126" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.permissions.runPipeline" :disabled="row.role === 'user'" />
          </template>
        </el-table-column>
        <el-table-column label="账号状态" min-width="100" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.active" active-text="启用" inactive-text="禁用" inline-prompt />
          </template>
        </el-table-column>
        <el-table-column prop="lastLogin" label="最后登录时间" min-width="140" />
        <el-table-column label="操作" width="156" fixed="right">
          <template #default="{ row }">
            <div class="flex items-center gap-1">
              <el-button link type="primary" class="row-action" @click="openEditDialog(row)">
                <Pencil class="mr-1 h-4 w-4" />编辑
              </el-button>
              <el-dropdown trigger="click" @command="handleRowCommand($event, row)">
                <el-button link class="row-more">
                  <MoreHorizontal class="h-4 w-4" />
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="reset">
                      <KeyRound class="mr-2 h-4 w-4" />重置密码
                    </el-dropdown-item>
                    <el-dropdown-item command="delete">
                      <Trash2 class="mr-2 h-4 w-4 text-red-500" />删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '新增用户' : '编辑用户'" width="620px" destroy-on-close>
      <el-form ref="userFormRef" :model="userForm" :rules="formRules" label-position="top" class="dialog-form grid gap-4 md:grid-cols-2">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="userForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="账号" prop="account">
          <el-input v-model="userForm.account" placeholder="请输入登录账号" />
        </el-form-item>
        <el-form-item label="电子邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="name@agripulse.gov.cn" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="userForm.phone" placeholder="11 位手机号" />
        </el-form-item>
        <el-form-item label="所属角色" prop="role">
          <el-select v-model="userForm.role" class="w-full" @change="applyRoleDefaults">
            <el-option v-for="role in roleOptions" :key="role.value" :label="role.label" :value="role.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属机构" prop="organization">
          <el-select v-model="userForm.organization" class="w-full">
            <el-option v-for="organization in organizations" :key="organization" :label="organization" :value="organization" />
          </el-select>
        </el-form-item>
        <div class="md:col-span-2 grid gap-3 rounded-lg border border-slate-100 bg-slate-50 p-4 md:grid-cols-3">
          <div class="flex items-center justify-between gap-3 rounded-lg bg-white px-3 py-2">
            <span class="text-sm font-medium text-slate-700">启用账号</span>
            <el-switch v-model="userForm.active" />
          </div>
          <div class="flex items-center justify-between gap-3 rounded-lg bg-white px-3 py-2">
            <span class="text-sm font-medium text-slate-700">修改系统配置</span>
            <el-switch v-model="userForm.permissions.editSystem" />
          </div>
          <div class="flex items-center justify-between gap-3 rounded-lg bg-white px-3 py-2">
            <span class="text-sm font-medium text-slate-700">手动运行流水线</span>
            <el-switch v-model="userForm.permissions.runPipeline" />
          </div>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" class="create-button" @click="submitUserForm">保存</el-button>
      </template>
    </el-dialog>

    <div v-if="deleteDialog.visible" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4" role="dialog" aria-modal="true" aria-label="确认删除用户">
      <div class="w-full max-w-[420px] rounded-lg border border-red-100 bg-white p-5 shadow-2xl">
        <div class="flex items-start gap-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-red-50 text-red-600">
            <Trash2 class="h-5 w-5" />
          </span>
          <div>
            <h3 class="text-base font-semibold text-slate-950">确认删除用户</h3>
            <p class="mt-2 text-sm leading-6 text-slate-600">将删除 {{ deleteDialog.names.join('、') }}，相关账号将无法登录平台。</p>
          </div>
        </div>
        <div class="mt-5 flex justify-end gap-2">
          <el-button @click="deleteDialog.visible = false">取消</el-button>
          <el-button type="danger" @click="confirmDelete">确认删除</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.user-permission-center {
  --el-color-primary: #064e3b;
  --el-color-primary-light-3: #13805f;
  --el-color-primary-light-5: #36a47f;
  --el-color-primary-light-7: #a7f3d0;
  --el-color-primary-light-8: #d1fae5;
  --el-color-primary-light-9: #ecfdf5;
  --el-color-primary-dark-2: #043829;
}

.toolbar-search {
  width: min(420px, 100%);
}

.create-button {
  border: 0;
  background: #064e3b;
}

.create-button:hover,
.create-button:focus {
  background: #043829;
}

.export-button,
.batch-button {
  border-color: #d1fae5;
  color: #064e3b;
}

.user-table {
  font-size: 13px;
}

.user-table :deep(.el-table__header th) {
  color: #475569;
  background: #f8fafc;
  font-size: 12px;
  font-weight: 700;
}

.user-table :deep(.el-table__row) {
  height: 58px;
}

.role-tag {
  border-radius: 6px;
  font-weight: 700;
}

.role-tag-admin {
  border-color: #064e3b;
  background: #ecfdf5;
  color: #064e3b;
}

.role-tag-analyst {
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
}

.role-tag-user {
  border-color: #e2e8f0;
  background: #f8fafc;
  color: #475569;
}

.row-action,
.row-more {
  color: #064e3b;
}

.dialog-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.dialog-form :deep(.el-form-item__label) {
  color: #334155;
  font-size: 13px;
  font-weight: 700;
}
</style>