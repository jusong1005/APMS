<script setup>
import { computed, onUnmounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  BellRing,
  Camera,
  CheckCircle2,
  KeyRound,
  Mail,
  MapPin,
  MonitorSmartphone,
  Save,
  ShieldCheck,
  Smartphone,
  UserRound,
  Wheat
} from 'lucide-vue-next'

const activeTab = ref('basic')
const saving = ref(false)
const avatarPreview = ref('')

const userInfo = reactive({
  name: '张建国',
  employeeId: 'AGP-230118',
  email: 'zhangjianguo@agripulse.gov.cn',
  phone: '138 0108 2026',
  organization: '国家农产品监测中心-华东市场监测站',
  role: '系统管理员',
  avatar: ''
})

const securityForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const preferences = reactive({
  province: '山东省',
  categories: ['猪肉', '大白菜', '红富士苹果'],
  refreshRate: '1min'
})

const notification = reactive({
  priceVolatility: true,
  crawlerFailure: true,
  systemMaintenance: true,
  channels: ['站内信', '邮件']
})

const provinces = ['山东省', '北京市', '河南省', '四川省', '广东省', '江苏省', '浙江省']
const categoryOptions = ['猪肉', '大白菜', '红富士苹果', '鸡蛋', '番茄', '玉米', '黄瓜', '土豆']
const refreshOptions = ['30s', '1min', '5min', '10min']

const deviceRows = [
  { id: 1, time: '2026-05-30 09:22:18', ip: '10.24.18.32', device: 'Windows 工作站', current: true },
  { id: 2, time: '2026-05-29 21:08:44', ip: '10.24.18.77', device: 'Chrome / macOS', current: false },
  { id: 3, time: '2026-05-28 18:36:09', ip: '10.24.20.16', device: '移动端 Web', current: false }
]

const notificationRows = [
  { key: 'priceVolatility', title: '价格剧烈波动预警', detail: '重点品类触发涨跌幅阈值时推送' },
  { key: 'crawlerFailure', title: '采集任务失败提醒', detail: '任务超时、重试耗尽或数据源不可达时推送' },
  { key: 'systemMaintenance', title: '系统维护通知', detail: '版本发布、数据库维护和权限策略变更时推送' }
]

const tabItems = [
  { name: 'basic', label: '基本资料', icon: UserRound },
  { name: 'security', label: '安全设置', icon: KeyRound },
  { name: 'preferences', label: '监控偏好', icon: Wheat },
  { name: 'notification', label: '消息通知', icon: BellRing }
]

const passwordStrength = computed(() => {
  const password = securityForm.newPassword
  let score = 0
  if (password.length >= 8) score += 1
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score += 1
  if (/\d/.test(password)) score += 1
  if (/[^A-Za-z0-9]/.test(password)) score += 1
  return score
})

const strengthText = computed(() => ['未输入', '偏弱', '中等', '较强', '高强度'][passwordStrength.value])
const passwordMismatch = computed(() => securityForm.confirmPassword && securityForm.newPassword !== securityForm.confirmPassword)

const beforeAvatarUpload = (rawFile) => {
  if (!rawFile.type.startsWith('image/')) {
    ElMessage.error('仅支持图片格式')
    return false
  }
  if (rawFile.size / 1024 / 1024 > 3) {
    ElMessage.error('头像图片需小于 3MB')
    return false
  }
  return true
}

const handleAvatarChange = (uploadFile) => {
  const rawFile = uploadFile.raw
  if (!rawFile || !beforeAvatarUpload(rawFile)) return
  if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value)
  avatarPreview.value = URL.createObjectURL(rawFile)
  userInfo.avatar = avatarPreview.value
  ElMessage.success('头像裁剪预览已更新')
}

const handleSave = async () => {
  if (passwordMismatch.value) {
    ElMessage.error('两次输入的新密码不一致')
    return
  }

  saving.value = true
  try {
    await new Promise((resolve) => window.setTimeout(resolve, 650))
    ElMessage.success('个人设置已保存')
  } finally {
    saving.value = false
  }
}

onUnmounted(() => {
  if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value)
})
</script>

<template>
  <div class="profile-settings space-y-5">
    <section class="rounded-lg border border-slate-100 bg-white p-5 shadow-sm">
      <div class="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
        <div class="flex items-center gap-4">
          <div class="relative flex h-14 w-14 items-center justify-center rounded-full bg-[#064e3b] text-lg font-semibold text-white shadow-sm">
            <img v-if="userInfo.avatar" :src="userInfo.avatar" alt="用户头像" class="h-full w-full rounded-full object-cover" />
            <span v-else>张</span>
            <span class="absolute -bottom-0.5 -right-0.5 h-4 w-4 rounded-full border-2 border-white bg-emerald-400" />
          </div>
          <div>
            <h2 class="text-xl font-semibold text-slate-950">个人设置</h2>
            <p class="mt-1 text-sm text-slate-500">欢迎回来，管理员{{ userInfo.name }}，今天的监控席位已准备就绪。</p>
          </div>
        </div>
        <el-button type="primary" :loading="saving" class="profile-save-button" @click="handleSave">
          <Save class="mr-2 h-4 w-4" />保存个人设置
        </el-button>
      </div>
    </section>

    <section class="rounded-lg border border-slate-100 bg-white shadow-sm">
      <el-tabs v-model="activeTab" tab-position="left" class="profile-tabs">
        <el-tab-pane v-for="item in tabItems" :key="item.name" :name="item.name">
          <template #label>
            <span class="flex items-center gap-2">
              <component :is="item.icon" class="h-4 w-4" />
              <span>{{ item.label }}</span>
            </span>
          </template>

          <div v-if="item.name === 'basic'" class="tab-panel">
            <div class="panel-heading">
              <div>
                <h3>基本资料</h3>
                <p>维护个人身份信息和监测机构归属</p>
              </div>
              <el-tag effect="plain" type="success">{{ userInfo.role }}</el-tag>
            </div>

            <div class="grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)]">
              <div class="rounded-lg border border-slate-100 bg-slate-50 p-5">
                <el-upload
                  class="avatar-uploader"
                  :show-file-list="false"
                  :auto-upload="false"
                  accept="image/*"
                  :on-change="handleAvatarChange"
                >
                  <div class="avatar-trigger group">
                    <img v-if="userInfo.avatar" :src="userInfo.avatar" alt="头像预览" class="h-full w-full rounded-full object-cover" />
                    <span v-else class="text-3xl font-semibold text-[#064e3b]">张</span>
                    <span class="avatar-mask"><Camera class="h-4 w-4" />修改头像</span>
                  </div>
                </el-upload>
                <div class="mt-5 rounded-lg border border-dashed border-emerald-200 bg-white p-4">
                  <p class="text-xs font-semibold text-slate-500">裁剪预览</p>
                  <div class="mt-3 flex items-center gap-3">
                    <div class="h-16 w-16 overflow-hidden rounded-full border-4 border-white bg-emerald-50 shadow-sm">
                      <img v-if="userInfo.avatar" :src="userInfo.avatar" alt="圆形裁剪预览" class="h-full w-full object-cover" />
                      <div v-else class="flex h-full w-full items-center justify-center text-lg font-semibold text-[#064e3b]">张</div>
                    </div>
                    <div class="text-xs leading-5 text-slate-500">
                      <p>1:1 圆形裁剪</p>
                      <p>推荐 400 x 400 px</p>
                    </div>
                  </div>
                </div>
              </div>

              <el-form label-position="top" class="profile-form grid gap-4 lg:grid-cols-2">
                <el-form-item label="姓名">
                  <el-input v-model="userInfo.name" />
                </el-form-item>
                <el-form-item label="工号">
                  <el-input v-model="userInfo.employeeId" />
                </el-form-item>
                <el-form-item label="电子邮箱">
                  <el-input v-model="userInfo.email">
                    <template #prefix><Mail class="h-4 w-4 text-slate-400" /></template>
                  </el-input>
                </el-form-item>
                <el-form-item label="手机号">
                  <el-input v-model="userInfo.phone">
                    <template #prefix><Smartphone class="h-4 w-4 text-slate-400" /></template>
                  </el-input>
                </el-form-item>
                <el-form-item label="所属机构" class="lg:col-span-2">
                  <div class="flex w-full items-center gap-3 rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
                    <MapPin class="h-4 w-4 text-[#064e3b]" />
                    <span class="text-sm font-medium text-slate-800">{{ userInfo.organization }}</span>
                    <el-tag class="ml-auto" effect="plain">只读</el-tag>
                  </div>
                </el-form-item>
              </el-form>
            </div>
          </div>

          <div v-else-if="item.name === 'security'" class="tab-panel">
            <div class="panel-heading">
              <div>
                <h3>安全设置</h3>
                <p>管理密码重置和最近登录设备</p>
              </div>
              <ShieldCheck class="h-5 w-5 text-[#064e3b]" />
            </div>

            <div class="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
              <div class="rounded-lg border border-slate-100 p-5">
                <h4 class="text-sm font-semibold text-slate-950">密码重置</h4>
                <el-form label-position="top" class="profile-form mt-4 space-y-4">
                  <el-form-item label="旧密码">
                    <el-input v-model="securityForm.oldPassword" type="password" show-password />
                  </el-form-item>
                  <el-form-item label="新密码">
                    <el-input v-model="securityForm.newPassword" type="password" show-password />
                  </el-form-item>
                  <div class="rounded-lg bg-slate-50 px-4 py-3">
                    <div class="mb-2 flex items-center justify-between text-xs">
                      <span class="text-slate-500">密码强度</span>
                      <span class="font-semibold text-[#064e3b]">{{ strengthText }}</span>
                    </div>
                    <div class="grid grid-cols-4 gap-2">
                      <span v-for="level in 4" :key="level" :class="['h-1.5 rounded-full', passwordStrength >= level ? 'bg-[#064e3b]' : 'bg-slate-200']" />
                    </div>
                  </div>
                  <el-form-item label="确认密码">
                    <el-input v-model="securityForm.confirmPassword" type="password" show-password />
                    <p v-if="passwordMismatch" class="mt-2 text-xs font-medium text-red-600">两次输入的新密码不一致</p>
                  </el-form-item>
                </el-form>
              </div>

              <div class="rounded-lg border border-slate-100 p-5">
                <h4 class="text-sm font-semibold text-slate-950">登录设备管理</h4>
                <div class="mt-4 space-y-3">
                  <div v-for="device in deviceRows" :key="device.id" class="flex items-center justify-between gap-4 rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
                    <div class="flex items-center gap-3">
                      <span class="flex h-10 w-10 items-center justify-center rounded-lg bg-white text-[#064e3b] shadow-sm">
                        <MonitorSmartphone class="h-5 w-5" />
                      </span>
                      <div>
                        <div class="flex flex-wrap items-center gap-2">
                          <p class="text-sm font-semibold text-slate-900">{{ device.device }}</p>
                          <el-tag v-if="device.current" type="success" effect="plain" size="small">当前设备</el-tag>
                        </div>
                        <p class="mt-1 text-xs text-slate-500">{{ device.time }} · {{ device.ip }}</p>
                      </div>
                    </div>
                    <CheckCircle2 class="h-4 w-4 text-emerald-500" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="item.name === 'preferences'" class="tab-panel">
            <div class="panel-heading">
              <div>
                <h3>监控偏好</h3>
                <p>设置进入平台后的默认地区、关注品类和刷新周期</p>
              </div>
              <Wheat class="h-5 w-5 text-[#064e3b]" />
            </div>

            <el-form label-position="top" class="profile-form grid gap-5 xl:grid-cols-3">
              <el-form-item label="默认监测地区">
                <el-select v-model="preferences.province" class="w-full">
                  <el-option v-for="province in provinces" :key="province" :label="province" :value="province" />
                </el-select>
              </el-form-item>
              <el-form-item label="看板刷新频率">
                <el-select v-model="preferences.refreshRate" class="w-full">
                  <el-option v-for="option in refreshOptions" :key="option" :label="option" :value="option" />
                </el-select>
              </el-form-item>
              <div class="rounded-lg border border-slate-100 bg-[#064e3b] px-4 py-3 text-white">
                <p class="text-xs text-emerald-100">当前首页默认视图</p>
                <p class="mt-1 text-lg font-semibold">{{ preferences.province }} · {{ preferences.refreshRate }}</p>
              </div>
              <el-form-item label="关注品类" class="xl:col-span-3">
                <el-checkbox-group v-model="preferences.categories" class="category-checks">
                  <el-checkbox-button v-for="category in categoryOptions" :key="category" :label="category" :value="category" />
                </el-checkbox-group>
              </el-form-item>
            </el-form>
          </div>

          <div v-else class="tab-panel">
            <div class="panel-heading">
              <div>
                <h3>消息通知</h3>
                <p>配置预警、采集失败和系统维护消息</p>
              </div>
              <BellRing class="h-5 w-5 text-[#064e3b]" />
            </div>

            <div class="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
              <div class="space-y-3">
                <div v-for="row in notificationRows" :key="row.key" class="flex items-center justify-between gap-4 rounded-lg border border-slate-100 bg-slate-50 px-4 py-4">
                  <div>
                    <p class="text-sm font-semibold text-slate-950">{{ row.title }}</p>
                    <p class="mt-1 text-xs leading-5 text-slate-500">{{ row.detail }}</p>
                  </div>
                  <el-switch v-model="notification[row.key]" />
                </div>
              </div>

              <div class="rounded-lg border border-slate-100 p-5">
                <h4 class="text-sm font-semibold text-slate-950">接收渠道</h4>
                <el-checkbox-group v-model="notification.channels" class="mt-4 flex flex-col gap-3">
                  <el-checkbox label="站内信" value="站内信" disabled>站内信（必选）</el-checkbox>
                  <el-checkbox label="邮件" value="邮件">邮件</el-checkbox>
                  <el-checkbox label="微信 Webhook" value="微信 Webhook">微信 Webhook</el-checkbox>
                </el-checkbox-group>
                <div class="mt-5 rounded-lg bg-emerald-50 px-4 py-3 text-xs leading-5 text-[#064e3b]">
                  已启用渠道：{{ notification.channels.join('、') }}
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </section>
  </div>
</template>

<style scoped>
.profile-settings {
  --el-color-primary: #064e3b;
  --el-color-primary-light-3: #13805f;
  --el-color-primary-light-5: #36a47f;
  --el-color-primary-light-7: #a7f3d0;
  --el-color-primary-light-8: #d1fae5;
  --el-color-primary-light-9: #ecfdf5;
  --el-color-primary-dark-2: #043829;
}

.profile-save-button {
  border: 0;
  background: #064e3b;
  box-shadow: 0 10px 24px rgba(6, 78, 59, 0.22);
}

.profile-save-button:hover,
.profile-save-button:focus {
  background: #043829;
}

.profile-tabs :deep(.el-tabs__header.is-left) {
  width: 230px;
  margin-right: 0;
  border-right: 1px solid #e2e8f0;
  background: #f8fafc;
}

.profile-tabs :deep(.el-tabs__nav-wrap.is-left::after) {
  display: none;
}

.profile-tabs :deep(.el-tabs__item.is-left) {
  height: 48px;
  justify-content: flex-start;
  padding: 0 20px;
  color: #475569;
  font-weight: 600;
}

.profile-tabs :deep(.el-tabs__item.is-active) {
  color: #064e3b;
  background: #ecfdf5;
}

.profile-tabs :deep(.el-tabs__active-bar.is-left) {
  width: 3px;
  background: #064e3b;
}

.profile-tabs :deep(.el-tabs__content) {
  min-height: 560px;
}

.tab-panel {
  padding: 24px;
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f5f9;
}

.panel-heading h3 {
  color: #020617;
  font-size: 16px;
  font-weight: 700;
}

.panel-heading p {
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
}

.profile-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.profile-form :deep(.el-form-item__label) {
  color: #334155;
  font-weight: 700;
}

.avatar-uploader :deep(.el-upload) {
  display: block;
}

.avatar-trigger {
  position: relative;
  display: flex;
  width: 132px;
  height: 132px;
  margin: 0 auto;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 1px solid #d1fae5;
  border-radius: 999px;
  background: #ecfdf5;
  cursor: pointer;
}

.avatar-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: rgba(6, 78, 59, 0.72);
  color: #ffffff;
  font-size: 13px;
  font-weight: 700;
  opacity: 0;
  transition: opacity 160ms ease;
}

.avatar-trigger:hover .avatar-mask {
  opacity: 1;
}

.category-checks {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.category-checks :deep(.el-checkbox-button__inner) {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: none;
}

.category-checks :deep(.el-checkbox-button.is-checked .el-checkbox-button__inner) {
  border-color: #064e3b;
  background: #064e3b;
}

@media (max-width: 1024px) {
  .profile-tabs :deep(.el-tabs) {
    display: block;
  }

  .profile-tabs :deep(.el-tabs__header.is-left) {
    width: 190px;
  }
}

@media (max-width: 720px) {
  .profile-tabs :deep(.el-tabs__header.is-left) {
    width: 160px;
  }

  .tab-panel {
    padding: 18px;
  }
}
</style>