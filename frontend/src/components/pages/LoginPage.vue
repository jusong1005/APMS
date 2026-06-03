<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Eye, EyeOff, Leaf, LineChart, LoaderCircle, LockKeyhole, Phone, ShieldCheck, UserRound } from 'lucide-vue-next'
import { authApi, tokenStore } from '../../lib/api'

const emit = defineEmits(['login-success', 'show-register', 'show-forgot'])

const savedAccount = typeof window !== 'undefined' ? window.localStorage.getItem('agri-login-account') || '' : ''
const formRef = ref(null)
const loading = ref(false)
const passwordVisible = ref(false)
const captchaCode = ref('')
const captchaImage = ref('')

const loginForm = reactive({
  account: savedAccount,
  password: '',
  captcha: '',
  remember: Boolean(savedAccount)
})

const rules = {
  account: [{ required: true, message: '请输入账号或手机号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  captcha: [{ required: true, message: '请输入验证码', trigger: 'blur' }]
}

const createCaptchaCode = () => {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  return Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join('')
}

const createCaptchaImage = (code) => {
  const noiseLines = Array.from({ length: 5 }, (_, index) => {
    const y = 16 + index * 8 + Math.floor(Math.random() * 8)
    const endY = 10 + Math.floor(Math.random() * 48)
    return `<path d="M${4 + index * 12} ${y} C ${34 + index * 7} ${endY}, ${74 - index * 4} ${64 - endY}, ${116 - index * 9} ${20 + Math.random() * 30}" stroke="rgba(6,78,59,0.22)" stroke-width="1.2" fill="none"/>`
  }).join('')

  const letters = code.split('').map((letter, index) => {
    const x = 18 + index * 25
    const y = 38 + Math.floor(Math.random() * 8)
    const rotate = Math.floor(Math.random() * 18) - 9
    return `<text x="${x}" y="${y}" transform="rotate(${rotate} ${x} ${y})" font-family="Inter, Arial, sans-serif" font-size="24" font-weight="800" fill="#064e3b">${letter}</text>`
  }).join('')

  const dots = Array.from({ length: 24 }, () => `<circle cx="${Math.random() * 124}" cy="${Math.random() * 54}" r="${Math.random() * 1.5 + 0.6}" fill="rgba(6,78,59,0.18)"/>`).join('')
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="128" height="54" viewBox="0 0 128 54"><rect width="128" height="54" rx="8" fill="#f8fafc"/><path d="M0 42 C 32 24, 54 58, 88 20 S 118 10, 128 18" stroke="rgba(217,155,43,0.22)" stroke-width="8" fill="none"/>${noiseLines}${dots}${letters}</svg>`
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
}

const refreshCaptcha = () => {
  captchaCode.value = createCaptchaCode()
  captchaImage.value = createCaptchaImage(captchaCode.value)
  loginForm.captcha = ''
}

const handleLogin = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  if (loginForm.captcha.trim().toUpperCase() !== captchaCode.value) {
    ElMessage.error('验证码不正确')
    refreshCaptcha()
    return
  }

  loading.value = true
  try {
    const session = await authApi.login({ account: loginForm.account, password: loginForm.password })
    tokenStore.setSession(session)
    if (loginForm.remember) {
      window.localStorage.setItem('agri-login-account', loginForm.account)
    } else {
      window.localStorage.removeItem('agri-login-account')
    }
    ElMessage.success('登录成功')
    emit('login-success', { user: session.user })
  } catch (error) {
    ElMessage.error(error.message || '登录失败')
    refreshCaptcha()
  } finally {
    loading.value = false
  }
}

const handleForgotPassword = () => {
  emit('show-forgot')
}

const handleRegister = () => {
  emit('show-register')
}

onMounted(refreshCaptcha)
</script>

<template>
  <main class="login-page grid min-h-screen bg-white text-slate-950 lg:grid-cols-[minmax(420px,0.92fr)_minmax(520px,1.08fr)]">
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
        <p class="text-sm font-medium uppercase text-emerald-100/80">AgriPulse</p>
        <h1 class="mt-3 text-4xl font-semibold tracking-normal">农产品价格监控平台</h1>
        <p class="mt-5 text-base leading-7 text-emerald-50/82">全国农产品价格大数据实时监测与预警平台</p>

        <div class="mt-12 grid w-full grid-cols-3 gap-3 text-left">
          <div class="rounded-lg border border-white/14 bg-white/10 px-4 py-3 backdrop-blur">
            <LineChart class="h-4 w-4 text-emerald-100" />
            <p class="mt-3 text-xs text-emerald-50/70">实时价格</p>
          </div>
          <div class="rounded-lg border border-white/14 bg-white/10 px-4 py-3 backdrop-blur">
            <ShieldCheck class="h-4 w-4 text-emerald-100" />
            <p class="mt-3 text-xs text-emerald-50/70">风险预警</p>
          </div>
          <div class="rounded-lg border border-white/14 bg-white/10 px-4 py-3 backdrop-blur">
            <Phone class="h-4 w-4 text-emerald-100" />
            <p class="mt-3 text-xs text-emerald-50/70">移动协同</p>
          </div>
        </div>
      </div>
    </section>

    <section class="flex min-h-screen items-center justify-center bg-white px-5 py-10 sm:px-8">
      <div class="login-card-enter w-full max-w-[430px]">
        <div class="mb-8 text-center lg:text-left">
          <div class="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-[#064e3b] text-white shadow-[0_18px_36px_rgba(6,78,59,0.22)] lg:mx-0">
            <Leaf class="h-6 w-6" />
          </div>
          <p class="text-sm font-medium text-[#064e3b]">AgriPulse Secure Access</p>
          <h2 class="mt-2 text-3xl font-semibold tracking-normal text-slate-950">欢迎回来</h2>
          <p class="mt-3 text-sm leading-6 text-slate-500">登录监测中心，查看实时价格、预警与分析结果。</p>
        </div>

        <div class="rounded-lg border border-slate-100 bg-white p-6 shadow-[0_22px_70px_rgba(15,23,42,0.10)] sm:p-7">
          <el-form ref="formRef" :model="loginForm" :rules="rules" label-position="top" @submit.prevent="handleLogin">
            <el-form-item label="账号 / 手机号" prop="account">
              <el-input v-model="loginForm.account" class="login-input" placeholder="请输入账号或手机号" autocomplete="username">
                <template #prefix>
                  <UserRound class="h-4 w-4 text-slate-400" />
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="密码" prop="password">
              <el-input v-model="loginForm.password" class="login-input" :type="passwordVisible ? 'text' : 'password'" placeholder="请输入登录密码" autocomplete="current-password">
                <template #prefix>
                  <LockKeyhole class="h-4 w-4 text-slate-400" />
                </template>
                <template #suffix>
                  <button type="button" class="flex h-7 w-7 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-slate-100 hover:text-[#064e3b]" :aria-label="passwordVisible ? '隐藏密码' : '显示密码'" @mousedown.prevent @click="passwordVisible = !passwordVisible">
                    <EyeOff v-if="passwordVisible" class="h-4 w-4" />
                    <Eye v-else class="h-4 w-4" />
                  </button>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="验证码" prop="captcha">
              <div class="grid w-full grid-cols-[minmax(0,1fr)_128px] gap-3">
                <el-input v-model="loginForm.captcha" class="login-input" placeholder="请输入验证码" maxlength="4" autocomplete="off">
                  <template #prefix>
                    <ShieldCheck class="h-4 w-4 text-slate-400" />
                  </template>
                </el-input>
                <button type="button" class="captcha-image-button" aria-label="点击刷新验证码" title="点击刷新验证码" @click="refreshCaptcha">
                  <img :src="captchaImage" alt="验证码" class="h-[54px] w-32 rounded-lg border border-slate-200 object-cover shadow-[0_10px_24px_rgba(15,23,42,0.06)]" />
                </button>
              </div>
            </el-form-item>

            <div class="mb-6 flex items-center justify-between gap-3 text-sm">
              <el-checkbox v-model="loginForm.remember" class="login-checkbox">记住我</el-checkbox>
              <button type="button" class="font-medium text-[#064e3b] transition-colors hover:text-[#043829]" @click="handleForgotPassword">忘记密码</button>
            </div>

            <button type="button" class="login-submit-native" :disabled="loading" @click="handleLogin">
              <LoaderCircle v-if="loading" class="h-4 w-4 animate-spin" />
              <span>{{ loading ? '正在登录' : '登录监测平台' }}</span>
            </button>
          </el-form>

          <div class="relative z-0 mt-6 border-t border-slate-100 pt-5 text-center text-sm text-slate-500">
            <span>还没有账号？</span>
            <button type="button" class="ml-1 font-semibold text-[#064e3b] transition-colors hover:text-[#043829]" @click="handleRegister">立即注册账号</button>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.login-card-enter {
  animation: loginPanelUp 520ms cubic-bezier(0.16, 1, 0.3, 1);
}

.login-page :deep(.el-form-item__label) {
  color: #334155;
  font-weight: 600;
  padding-bottom: 8px;
}

.login-page :deep(.login-input .el-input__wrapper) {
  min-height: 48px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05), 0 10px 26px rgba(15, 23, 42, 0.035);
  padding: 0 12px;
  transition: border-color 180ms ease, box-shadow 180ms ease;
}

.login-page :deep(.login-input .el-input__wrapper.is-focus) {
  border-color: #064e3b;
  box-shadow: 0 0 0 3px rgba(6, 78, 59, 0.12), 0 18px 38px rgba(15, 23, 42, 0.08);
}

.login-page :deep(.login-checkbox .el-checkbox__input.is-checked .el-checkbox__inner) {
  border-color: #064e3b;
  background-color: #064e3b;
}

.login-page :deep(.login-checkbox .el-checkbox__input.is-checked + .el-checkbox__label) {
  color: #064e3b;
}

.captcha-image-button {
  display: inline-flex;
  height: 54px;
  width: 128px;
  align-items: center;
  justify-content: center;
  border: 0;
  background: transparent;
  padding: 0;
}

.login-submit-native {
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

.login-submit-native:hover,
.login-submit-native:focus-visible {
  background: #043829;
}

.login-submit-native:focus-visible {
  outline: 3px solid rgba(6, 78, 59, 0.18);
  outline-offset: 3px;
}

.login-submit-native:disabled {
  cursor: wait;
  opacity: 0.9;
}

@keyframes loginPanelUp {
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