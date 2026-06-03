<script setup>
import { onMounted, ref } from 'vue'
import AppShell from './components/layout/AppShell.vue'
import ForgotPasswordPage from './components/pages/ForgotPasswordPage.vue'
import LoginPage from './components/pages/LoginPage.vue'
import RegisterPage from './components/pages/RegisterPage.vue'
import { authApi, tokenStore } from './lib/api'

const authenticated = ref(Boolean(tokenStore.getAccessToken()))
const currentUser = ref(tokenStore.getUser())
const authMode = ref('login')

const handleLoginSuccess = ({ user }) => {
  currentUser.value = user
  authenticated.value = true
}

const handleRegisterSuccess = ({ account }) => {
  window.localStorage.setItem('agri-login-account', account)
  authMode.value = 'login'
}

const handleResetSuccess = ({ account }) => {
  if (account) window.localStorage.setItem('agri-login-account', account)
  authMode.value = 'login'
}

const handleLogout = async () => {
  const refreshToken = tokenStore.getRefreshToken()
  try {
    if (refreshToken) await authApi.logout(refreshToken)
  } catch {
    // Local session cleanup still runs when the backend token is already invalid.
  }
  tokenStore.clear()
  currentUser.value = null
  authenticated.value = false
  authMode.value = 'login'
}

onMounted(async () => {
  window.addEventListener('agri-auth-expired', handleLogout)
  if (!tokenStore.getAccessToken()) return
  try {
    const user = await authApi.me()
    tokenStore.setUser(user)
    currentUser.value = user
    authenticated.value = true
  } catch {
    tokenStore.clear()
    currentUser.value = null
    authenticated.value = false
  }
})
</script>

<template>
  <LoginPage v-if="!authenticated && authMode === 'login'" @login-success="handleLoginSuccess" @show-register="authMode = 'register'" @show-forgot="authMode = 'forgot'" />
  <RegisterPage v-else-if="!authenticated && authMode === 'register'" @back-login="authMode = 'login'" @registered="handleRegisterSuccess" />
  <ForgotPasswordPage v-else-if="!authenticated && authMode === 'forgot'" @back-login="authMode = 'login'" @reset-success="handleResetSuccess" />
  <AppShell v-else :user="currentUser" @logout="handleLogout" />
</template>