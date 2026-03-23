<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores'
import { Button } from '@/components/ui'
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  Calendar,
  LogOut,
  User,
  School,
} from 'lucide-vue-next'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const user = computed(() => authStore.user)

// Navigation items based on role
const navItems = computed(() => {
  const items: { name: string; path: string; icon: any }[] = []

  if (authStore.isAdmin) {
    items.push(
      { name: 'Dashboard', path: '/admin', icon: LayoutDashboard },
      { name: 'Students', path: '/admin/students', icon: Users },
      { name: 'Teachers', path: '/admin/teachers', icon: User },
      { name: 'Classes', path: '/admin/classes', icon: School }
    )
  } else if (authStore.isTeacher) {
    items.push(
      { name: 'Dashboard', path: '/teacher', icon: LayoutDashboard },
      { name: 'Students', path: '/teacher/students', icon: Users },
      { name: 'Class Session', path: '/teacher/session', icon: Calendar }
    )
  } else if (authStore.isStudent) {
    items.push({ name: 'Dashboard', path: '/student', icon: LayoutDashboard })
  }

  return items
})

const isActive = (path: string) => {
  return route.path === path
}

const handleLogout = async () => {
  await authStore.logout()
}
</script>

<template>
  <div class="min-h-screen bg-background">
    <!-- Sidebar -->
    <aside
      class="fixed left-0 top-0 z-40 h-screen w-64 border-r border-white/10 bg-[#0a0a0f] transition-transform"
    >
      <!-- Logo -->
      <div class="flex h-16 items-center border-b border-white/10 px-6">
        <GraduationCap class="h-8 w-8 text-primary" />
        <span class="ml-3 text-xl font-bold text-white">ClassHub</span>
      </div>

      <!-- User info -->
      <div class="border-b border-white/10 p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/20">
            <User class="h-5 w-5 text-primary" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="truncate text-sm font-medium text-white">{{ user?.name }}</p>
            <p class="truncate text-xs text-white/50 capitalize">{{ user?.role }}</p>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="space-y-1 p-4">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
            isActive(item.path)
              ? 'bg-primary/10 text-primary'
              : 'text-white/70 hover:bg-white/10 hover:text-white',
          ]"
        >
          <component :is="item.icon" class="h-5 w-5" />
          {{ item.name }}
        </RouterLink>
      </nav>

      <!-- Bottom actions -->
      <div class="absolute bottom-0 left-0 right-0 border-t border-white/10 p-4">
        <Button variant="ghost" class="w-full justify-start gap-2 text-white/70" @click="handleLogout">
          <LogOut class="h-5 w-5" />
          Logout
        </Button>
      </div>
    </aside>

    <!-- Main content -->
    <main class="ml-64 min-h-screen p-8">
      <div class="mx-auto max-w-7xl">
        <slot />
        <RouterView />
      </div>
    </main>
  </div>
</template>
