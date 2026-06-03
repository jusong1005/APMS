<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Eye,
  EyeOff,
  KeyRound,
  Leaf,
  LineChart,
  LoaderCircle,
  LockKeyhole,
  Phone,
  ShieldCheck,
  UserRound
} from 'lucide-vue-next'
import { authApi } from '../../lib/api'

const emit = defineEmits(['back-login', 'reset-success'])

const formRef = ref(null)
const submitting = ref(false)
const passwordVisible = ref(false)
const confirmVisible = ref(false)

const resetForm = reactive({
  account: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入新密码'))
    return
  }
  if (value !== resetForm.password) {
    callback(new Error('两次输入的新密码不一致'))
    return
  }
  callback()
}

const rules = {
  account: [{ required: true, message: '请输入账号、手机号或邮箱', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
  ],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: ['blur', 'change'] }]
}

const passwordStrength = computed(() => {
  let score = 0
  if (resetForm.password.length >= 6) score += 1
  if (/[A-Z]/.test(resetForm.password) && /[a-z]/.test(resetForm.password)) score += 1
  if (/\d/.test(resetForm.password)) score += 1
  if (/[^A-Za-z0-9]/.test(resetForm.password)) score += 1
  return score
})

const strengthLabel = computed(() => ['未输入', '基础', '中等', '较强', '高强度'][passwordStrength.value])

const handleResetPassword = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await authApi.resetPassword({
      account: resetForm.account,
      newPassword: resetForm.password
    })
    ElMessage.success('密码已重置，请返回登录')
    emit('reset-success', { account: resetForm.account })
  } catch (error) {
    ElMessage.error(error.message || '密码重置失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="forgot-page grid min-h-screen bg-white text-slate-950 lg:grid-cols-[minmax(420px,0.92fr)_minmax(520px,1.08fr)]">
    <section class="relative hidden min-h-screen overflow-hidden bg-[#064e3b] text-white lg:flex lg:items-center lg:justify-center">
      <svg class="pointer-events-none absolute inset-0 h-full w-full opacity-20" viewBox="0 0 980 980" fill="none" aria-hidden="true">
        <path d="M-80 620C70 470 175 525 310 410C438 300 520 138 716 205C845 248 915 375 1060 300" stroke="white" stroke-width="3" stroke-linecap="round" />
        <path d="M-120 705C78 560 214 660 378 520C514 404 626 330 762 376C874 414 945 505 1100 428" stroke="#a7f3d0" stroke-width="2" stroke-linecap="round" />
        <path d="M-70 342C76 290 196 322 318 236C450 143 596 78 742 112C842 135 928 202 1012 166" stroke="#d99b2b" stroke-width="2" stroke-linecap="round" />
      </svg>
      <div class="absolute inset-0 bg-[linear-gradient(135deg,rgba(255,255,255,0.08)_0,rgba(255,255,255,0)_38%,rgba(217,155,43,0.08)_100%)]" />
      <div class="absolute inset-x-0 bottom-0 h-44 border-t border-white/10 bg-gradient-to-t from-black/16 to-transparent" />

      <div class="relative z-10 flex max-w-[520px] flex-col items-center px-12 text-center">
        <div class="mb-8 flex h-20 w-20 items-center justify-center rounded-2xl border border-white/20 bg-white/12 shadow-[0_24px_70px_rgba(0,0,0,0.25)] backdrop-blur">
          <Leaf class="h-10 w-10 text-emerald-100" />
        </div>
        <p class="text-sm font-medium uppercase text-emerald-100/80">AgriPulse Secure Access</p>
        <h1 class="mt-3 text-4xl font-semibold tracking-normal">找回访问权限</h1>
        <p class="mt-5 text-base leading-7 text-emerald-50/82">输入账号并设置新密码，继续进入农产品价格监控平台</p>

        <div class="mt-12 grid w-full grid-cols-3 gap-3 text-left">
          <div class="rounded-lg border border-white/14 bg-white/10 px-4 py-3 backdrop-blur">
            <LineChart class="h-4 w-4 text-emerald-100" />
            <p class="mt-3 text-xs text-emerald-50/70">实时价格</p>
          </div>
          <div class="rounded-lg border border-white/14 bg-white/10 px-4 py-3 backdrop-blur">
            <ShieldCheck class="h-4 w-4 text-emerald-100" />
            <p class="mt-3 text-xs text-emerald-50/70">账号确认</p>
          </div>
          <div class="rounded-lg border border-white/14 bg-white/10 px-4 py-3 backdrop-blur">
            <Phone class="h-4 w-4 text-emerald-100" />
            <p class="mt-3 text-xs text-emerald-50/70">密码重置</p>
          </div>
        </div>
      </div>
    </section>

    <section class="flex min-h-screen items-center justify-center bg-white px-5 py-10 sm:px-8">
      <div class="forgot-card-enter w-full max-w-[430px]">
        <button type="button" class="mb-5 inline-flex items-center gap-2 text-sm font-semibold text-[#064e3b] transition-colors hover:text-[#043829]" @click="emit('back-login')">
          <ArrowLeft class="h-4 w-4" />返回登录
        </button>

        <div class="mb-8 text-center lg:text-left">
          <div class="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-[#064e3b] text-white shadow-[0_18px_36px_rgba(6,78,59,0.22)] lg:mx-0">
            <KeyRound class="h-6 w-6" />
          </div>
          <p class="text-sm font-medium text-[#064e3b]">Password Recovery</p>
          <h2 class="mt-2 text-3xl font-semibold tracking-normal text-slate-950">重置登录密码</h2>
          <p class="mt-3 text-sm leading-6 text-slate-500">输入账号信息，直接设置新的登录密码。</p>
        </div>

        <div class="rounded-lg border border-slate-100 bg-white p-6 shadow-[0_22px_70px_rgba(15,23,42,0.10)] sm:p-7">
          <el-form ref="formRef" :model="resetForm" :rules="rules" label-position="top" @submit.prevent="handleResetPassword">
            <el-form-item label="账号 / 手机号 / 邮箱" prop="account">
              <el-input v-model="resetForm.account" class="forgot-input" placeholder="请输入账号、手机号或邮箱" autocomplete="username">
                <template #prefix><UserRound class="h-4 w-4 text-slate-400" /></template>
              </el-input>
            </el-form-item>

            <el-form-item label="新密码" prop="password">
              <el-input v-model="resetForm.password" class="forgot-input" :type="passwordVisible ? 'text' : 'password'" placeholder="至少 6 位" autocomplete="new-password">
                <template #prefix><LockKeyhole class="h-4 w-4 text-slate-400" /></template>
                <template #suffix>
                  <button type="button" class="password-toggle" :aria-label="passwordVisible ? '隐藏密码' : '显示密码'" @mousedown.prevent @click="passwordVisible = !passwordVisible">
                    <EyeOff v-if="passwordVisible" class="h-4 w-4" />
                    <Eye v-else class="h-4 w-4" />
                  </button>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input v-model="resetForm.confirmPassword" class="forgot-input" :type="confirmVisible ? 'text' : 'password'" placeholder="再次输入新密码" autocomplete="new-password">
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

            <button type="button" class="forgot-submit-native" :disabled="submitting" @click="handleResetPassword">
              <LoaderCircle v-if="submitting" class="h-4 w-4 animate-spin" />
              <span>{{ submitting ? '正在重置' : '确认重置密码' }}</span>
            </button>
          </el-form>

          <div class="relative z-0 mt-6 border-t border-slate-100 pt-5 text-center text-sm text-slate-500">
            <span>想起密码了？</span>
            <button type="button" class="ml-1 font-semibold text-[#064e3b] transition-colors hover:text-[#043829]" @click="emit('back-login')">返回登录监测平台</button>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.forgot-card-enter {
  animation: forgotPanelUp 520ms cubic-bezier(0.16, 1, 0.3, 1);
}

.forgot-page :deep(.el-form-item__label) {
  color: #334155;
  font-weight: 600;
  padding-bottom: 8px;
}

.forgot-page :deep(.forgot-input .el-input__wrapper) {
  min-height: 48px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 10px 26px rgba(15, 23, 42, 0.035);
  padding: 0 12px;
  transition: border-color 180ms ease, box-shadow 180ms ease;
}

.forgot-page :deep(.forgot-input .el-input__wrapper.is-focus) {
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

.forgot-submit-native {
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

.forgot-submit-native:hover,
.forgot-submit-native:focus-visible {
  background: #043829;
}

.forgot-submit-native:focus-visible {
  outline: 3px solid rgba(6, 78, 59, 0.18);
  outline-offset: 3px;
}

.forgot-submit-native:disabled {
  cursor: wait;
  opacity: 0.9;
}

@keyframes forgotPanelUp {
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