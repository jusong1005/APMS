<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Building2,
  CheckCircle2,
  Eye,
  EyeOff,
  Leaf,
  LineChart,
  LoaderCircle,
  LockKeyhole,
  Mail,
  Phone,
  ShieldCheck,
  Smartphone,
  UserRound
} from 'lucide-vue-next'
import { authApi } from '../../lib/api'

const emit = defineEmits(['back-login', 'registered'])

const formRef = ref(null)
const loading = ref(false)
const passwordVisible = ref(false)
const confirmVisible = ref(false)

const registerForm = reactive({
  account: '',
  name: '',
  phone: '',
  email: '',
  organization: '',
  password: '',
  confirmPassword: ''
})

const organizations = ['国家农产品监测中心', '北京新发地', '寿光研发部', '郑州万邦监测站', '上海江桥监测点', '成都白家市场', '广州江南市场']

const validateConfirmPassword = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入密码'))
    return
  }
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
    return
  }
  callback()
}

const rules = {
  account: [
    { required: true, message: '请输入登录账号', trigger: 'blur' },
    { min: 4, max: 32, message: '账号长度为 4 到 32 位', trigger: 'blur' }
  ],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入 11 位中国大陆手机号', trigger: ['blur', 'change'] }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: ['blur', 'change'] }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
  ],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: ['blur', 'change'] }]
}

const passwordStrength = computed(() => {
  let score = 0
  if (registerForm.password.length >= 6) score += 1
  if (/[A-Z]/.test(registerForm.password) && /[a-z]/.test(registerForm.password)) score += 1
  if (/\d/.test(registerForm.password)) score += 1
  if (/[^A-Za-z0-9]/.test(registerForm.password)) score += 1
  return score
})

const strengthLabel = computed(() => ['未输入', '基础', '中等', '较强', '高强度'][passwordStrength.value])

const handleRegister = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authApi.register({
      account: registerForm.account,
      password: registerForm.password,
      name: registerForm.name,
      phone: registerForm.phone,
      email: registerForm.email,
      organization: registerForm.organization
    })
    ElMessage.success('注册成功，请使用新账号登录')
    emit('registered', { account: registerForm.account })
  } catch (error) {
    ElMessage.error(error.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="register-page grid min-h-screen bg-white text-slate-950 lg:grid-cols-[minmax(420px,0.92fr)_minmax(560px,1.08fr)]">
    <section class="relative hidden min-h-screen overflow-hidden bg-[#064e3b] text-white lg:flex lg:items-center lg:justify-center">
      <svg class="pointer-events-none absolute inset-0 h-full w-full opacity-20" viewBox="0 0 980 980" fill="none" aria-hidden="true">
        <path d="M-80 620C70 470 175 525 310 410C438 300 520 138 716 205C845 248 915 375 1060 300" stroke="white" stroke-width="3" stroke-linecap="round" />
        <path d="M-120 705C78 560 214 660 378 520C514 404 626 330 762 376C874 414 945 505 1100 428" stroke="#a7f3d0" stroke-width="2" stroke-linecap="round" />
        <path d="M-70 342C76 290 196 322 318 236C450 143 596 78 742 112C842 135 928 202 1012 166" stroke="#d99b2b" stroke-width="2" stroke-linecap="round" />
      </svg>
      <div class="absolute inset-0 bg-[linear-gradient(135deg,rgba(255,255,255,0.08)_0,rgba(255,255,255,0)_38%,rgba(217,155,43,0.08)_100%)]" />
      <div class="absolute inset-x-0 bottom-0 h-44 border-t border-white/10 bg-gradient-to-t from-black/16 to-transparent" />

      <div class="relative z-10 flex max-w-[540px] flex-col items-center px-12 text-center">
        <div class="mb-8 flex h-20 w-20 items-center justify-center rounded-2xl border border-white/20 bg-white/12 shadow-[0_24px_70px_rgba(0,0,0,0.25)] backdrop-blur">
          <Leaf class="h-10 w-10 text-emerald-100" />
        </div>
        <p class="text-sm font-medium uppercase text-emerald-100/80">AgriPulse Access</p>
        <h1 class="mt-3 text-4xl font-semibold tracking-normal">注册监测账号</h1>
        <p class="mt-5 text-base leading-7 text-emerald-50/82">统一身份接入全国农产品价格大数据实时监测与预警平台</p>

        <div class="mt-12 grid w-full grid-cols-3 gap-3 text-left">
          <div class="rounded-lg border border-white/14 bg-white/10 px-4 py-3 backdrop-blur">
            <LineChart class="h-4 w-4 text-emerald-100" />
            <p class="mt-3 text-xs text-emerald-50/70">价格监测</p>
          </div>
          <div class="rounded-lg border border-white/14 bg-white/10 px-4 py-3 backdrop-blur">
            <ShieldCheck class="h-4 w-4 text-emerald-100" />
            <p class="mt-3 text-xs text-emerald-50/70">权限分配</p>
          </div>
          <div class="rounded-lg border border-white/14 bg-white/10 px-4 py-3 backdrop-blur">
            <Phone class="h-4 w-4 text-emerald-100" />
            <p class="mt-3 text-xs text-emerald-50/70">协同处置</p>
          </div>
        </div>
      </div>
    </section>

    <section class="flex min-h-screen items-center justify-center bg-white px-5 py-10 sm:px-8">
      <div class="register-card-enter w-full max-w-[430px]">
        <button type="button" class="mb-5 inline-flex items-center gap-2 text-sm font-semibold text-[#064e3b] transition-colors hover:text-[#043829]" @click="emit('back-login')">
          <ArrowLeft class="h-4 w-4" />返回登录
        </button>

        <div class="mb-7 text-center lg:text-left">
          <div class="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-[#064e3b] text-white shadow-[0_18px_36px_rgba(6,78,59,0.22)] lg:mx-0">
            <UserRound class="h-6 w-6" />
          </div>
          <p class="text-sm font-medium text-[#064e3b]">Step 02 · Registration</p>
          <h2 class="mt-2 text-3xl font-semibold tracking-normal text-slate-950">创建监测账号</h2>
          <p class="mt-3 text-sm leading-6 text-slate-500">填写基础信息，立即开通平台基础监测权限。</p>
        </div>

        <div class="rounded-lg border border-slate-100 bg-white p-6 shadow-[0_22px_70px_rgba(15,23,42,0.10)] sm:p-7">
          <el-form ref="formRef" :model="registerForm" :rules="rules" label-position="top" @submit.prevent="handleRegister">
            <el-form-item label="登录账号" prop="account">
              <el-input v-model="registerForm.account" class="register-input" placeholder="请输入登录账号" autocomplete="username">
                <template #prefix><UserRound class="h-4 w-4 text-slate-400" /></template>
              </el-input>
            </el-form-item>

            <el-form-item label="姓名" prop="name">
              <el-input v-model="registerForm.name" class="register-input" placeholder="请输入姓名" autocomplete="name">
                <template #prefix><CheckCircle2 class="h-4 w-4 text-slate-400" /></template>
              </el-input>
            </el-form-item>

            <el-form-item label="手机号" prop="phone">
              <el-input v-model="registerForm.phone" class="register-input" placeholder="请输入手机号" autocomplete="tel">
                <template #prefix><Smartphone class="h-4 w-4 text-slate-400" /></template>
              </el-input>
            </el-form-item>

            <el-form-item label="电子邮箱" prop="email">
              <el-input v-model="registerForm.email" class="register-input" placeholder="name@agripulse.gov.cn" autocomplete="email">
                <template #prefix><Mail class="h-4 w-4 text-slate-400" /></template>
              </el-input>
            </el-form-item>

            <el-form-item label="所属机构（选填）" prop="organization">
              <el-select v-model="registerForm.organization" class="register-select w-full" placeholder="可选择监测机构，也可以暂不填写" filterable clearable>
                <template #prefix><Building2 class="h-4 w-4 text-slate-400" /></template>
                <el-option v-for="organization in organizations" :key="organization" :label="organization" :value="organization" />
              </el-select>
            </el-form-item>

            <el-form-item label="登录密码" prop="password">
              <el-input v-model="registerForm.password" class="register-input" :type="passwordVisible ? 'text' : 'password'" placeholder="至少 6 位" autocomplete="new-password">
                <template #prefix><LockKeyhole class="h-4 w-4 text-slate-400" /></template>
                <template #suffix>
                  <button type="button" class="password-toggle" :aria-label="passwordVisible ? '隐藏密码' : '显示密码'" @mousedown.prevent @click="passwordVisible = !passwordVisible">
                    <EyeOff v-if="passwordVisible" class="h-4 w-4" />
                    <Eye v-else class="h-4 w-4" />
                  </button>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="registerForm.confirmPassword" class="register-input" :type="confirmVisible ? 'text' : 'password'" placeholder="再次输入密码" autocomplete="new-password">
                <template #prefix><LockKeyhole class="h-4 w-4 text-slate-400" /></template>
                <template #suffix>
                  <button type="button" class="password-toggle" :aria-label="confirmVisible ? '隐藏密码' : '显示密码'" @mousedown.prevent @click="confirmVisible = !confirmVisible">
                    <EyeOff v-if="confirmVisible" class="h-4 w-4" />
                    <Eye v-else class="h-4 w-4" />
                  </button>
                </template>
              </el-input>
            </el-form-item>

            <div class="mb-5 rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
              <div class="mb-2 flex items-center justify-between text-xs">
                <span class="font-medium text-slate-500">密码强度</span>
                <span class="font-semibold text-[#064e3b]">{{ strengthLabel }}</span>
              </div>
              <div class="grid grid-cols-4 gap-2">
                <span v-for="level in 4" :key="level" :class="['h-1.5 rounded-full', passwordStrength >= level ? 'bg-[#064e3b]' : 'bg-slate-200']" />
              </div>
            </div>

            <div>
              <button type="button" class="register-submit-native" :disabled="loading" @click="handleRegister">
                <LoaderCircle v-if="loading" class="h-4 w-4 animate-spin" />
                <span>{{ loading ? '正在注册' : '立即注册账号' }}</span>
              </button>
            </div>
          </el-form>

          <div class="relative z-0 mt-6 border-t border-slate-100 pt-5 text-center text-sm text-slate-500">
            <span>已有账号？</span>
            <button type="button" class="ml-1 font-semibold text-[#064e3b] transition-colors hover:text-[#043829]" @click="emit('back-login')">返回登录监测平台</button>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.register-card-enter {
  animation: registerPanelUp 520ms cubic-bezier(0.16, 1, 0.3, 1);
}

.register-page :deep(.el-form-item) {
  margin-bottom: 18px;
}

.register-page :deep(.el-form-item__label) {
  color: #334155;
  font-weight: 600;
  padding-bottom: 8px;
}

.register-page :deep(.register-input .el-input__wrapper),
.register-page :deep(.register-select .el-select__wrapper) {
  min-height: 48px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 10px 26px rgba(15, 23, 42, 0.035);
  padding: 0 12px;
  transition: border-color 180ms ease, box-shadow 180ms ease;
}

.register-page :deep(.register-input .el-input__wrapper.is-focus),
.register-page :deep(.register-select .el-select__wrapper.is-focused) {
  border-color: #064e3b;
  box-shadow: 0 0 0 3px rgba(6, 78, 59, 0.12), 0 18px 38px rgba(15, 23, 42, 0.08);
}

.password-toggle {
  display: flex;
  height: 28px;
  width: 28px;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: #94a3b8;
  transition: background-color 160ms ease, color 160ms ease;
}

.password-toggle:hover,
.password-toggle:focus-visible {
  background: #f1f5f9;
  color: #064e3b;
}

.register-submit-native {
  position: relative;
  z-index: 10;
  display: inline-flex;
  width: 100%;
  height: 48px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 0;
  border-radius: 8px;
  background: #064e3b;
  color: #fff;
  font-weight: 700;
  isolation: isolate;
  box-shadow: 0 18px 36px rgba(6, 78, 59, 0.24);
  transition: background-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}

.register-submit-native:hover,
.register-submit-native:focus-visible {
  background: #043829;
}

.register-submit-native:focus-visible {
  outline: 3px solid rgba(6, 78, 59, 0.18);
  outline-offset: 3px;
}

.register-submit-native:disabled {
  cursor: wait;
  opacity: 0.9;
}

@keyframes registerPanelUp {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>