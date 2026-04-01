/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, computed, nextTick } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import ManageClassesDialog from '@/components/admin/ManageClassesDialog.vue'

// Create a test query client
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      gcTime: 0,
      staleTime: 0,
    },
  },
})

// Mock the API
vi.mock('@/api/users', () => ({
  usersApi: {
    update: vi.fn(() => Promise.resolve({ id: 1, assigned_classes: ['一年级一班', '一年级二班'] }))
  }
}))

// Mock useClasses composable
const mockClasses = ref([
  { name: '一年级一班', status: 'active' },
  { name: '一年级二班', status: 'active' },
  { name: '二年级一班', status: 'inactive' },
  { name: '二年级二班', status: 'active' }
])

vi.mock('@/composables/useClasses', () => ({
  useClasses: () => ({
    data: mockClasses,
    isPending: ref(false)
  })
}))

// Mock useToast
vi.mock('@/composables/useToast', () => ({
  useToast: () => ({
    showToast: vi.fn()
  })
}))

// Mock Dialog component to avoid Teleport issues
const MockDialog = {
  name: 'Dialog',
  props: ['open', 'title'],
  emits: ['update:open'],
  template: `
    <div v-if="open" class="mock-dialog">
      <h3>{{ title }}</h3>
      <slot />
      <slot name="footer" />
    </div>
  `
}

// Mock Button component with proper click handling
const MockButton = {
  name: 'Button',
  props: ['type', 'variant', 'size', 'disabled'],
  emits: ['click'],
  template: `
    <button 
      :type="type || 'button'" 
      :disabled="disabled"
      @click="$emit('click')"
    >
      <slot />
    </button>
  `
}

describe('ManageClassesDialog', () => {
  const mockTeacher = {
    id: 1,
    username: 'teacher1',
    name: '张老师',
    role: 'teacher',
    assigned_classes: ['一年级一班']
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockClasses.value = [
      { name: '一年级一班', status: 'active' },
      { name: '一年级二班', status: 'active' },
      { name: '二年级一班', status: 'inactive' },
      { name: '二年级二班', status: 'active' }
    ]
  })

  const mountComponent = (props = {}) => {
    const queryClient = createTestQueryClient()
    return mount(ManageClassesDialog, {
      props: {
        teacher: mockTeacher,
        open: true,
        ...props
      },
      global: {
        plugins: [[VueQueryPlugin, { queryClient }]],
        stubs: {
          Dialog: MockDialog,
          Button: MockButton,
          Checkbox: { 
            props: ['checked'],
            template: '<input type="checkbox" :checked="checked" />'
          }
        }
      }
    })
  }

  it('renders correctly when open', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.find('.mock-dialog').exists()).toBe(true)
    expect(wrapper.text()).toContain('管理班级')
    expect(wrapper.text()).toContain('张老师')
  })

  it('displays assigned classes section', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('已分配班级')
    expect(wrapper.text()).toContain('一年级一班')
    expect(wrapper.text()).toContain('(1)') // 计数
  })

  it('displays available classes section', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('可分配班级')
    // 可分配班级应该显示未分配的班级
    expect(wrapper.text()).toContain('一年级二班')
    expect(wrapper.text()).toContain('二年级一班')
    expect(wrapper.text()).toContain('二年级二班')
  })

  it('shows empty state when no assigned classes', async () => {
    const teacherWithNoClasses = {
      ...mockTeacher,
      assigned_classes: []
    }
    const wrapper = mountComponent({ teacher: teacherWithNoClasses })
    await flushPromises()

    expect(wrapper.text()).toContain('暂无分配的班级')
  })

  it('adds class to assigned list when clicked', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // 初始状态：已分配 1 个
    expect(wrapper.text()).toContain('已分配班级')
    
    // 通过调用组件方法添加班级
    const vm = wrapper.vm as any
    vm.addClass('一年级二班')
    await flushPromises()

    // 验证变更摘要显示新增
    expect(wrapper.text()).toContain('+1 个新增')
  })

  it('removes class from assigned list when clicked', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // 通过调用组件方法移除班级
    const vm = wrapper.vm as any
    vm.removeClass('一年级一班')
    await flushPromises()

    // 验证变更摘要显示移除
    expect(wrapper.text()).toContain('-1 个移除')
  })

  it('adds all visible classes when add all clicked', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as any
    vm.addAllVisible()
    await flushPromises()

    // 应该添加了 3 个班级（总共 4 个，已有 1 个）
    expect(wrapper.text()).toContain('+3 个新增')
  })

  it('removes all classes when remove all clicked', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as any
    vm.removeAll()
    await flushPromises()

    // 应该移除了 1 个班级
    expect(wrapper.text()).toContain('-1 个移除')
    expect(wrapper.text()).toContain('暂无分配的班级')
  })

  it('filters available classes based on search query', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // 设置搜索查询
    const vm = wrapper.vm as any
    vm.searchQuery = '一年级'
    await flushPromises()

    // 搜索结果中应该只有一年级的班级
    const text = wrapper.text()
    expect(text).toContain('一年级二班')
    expect(text).not.toContain('二年级一班')
    expect(text).not.toContain('二年级二班')
  })

  it('shows no changes initially', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    expect(wrapper.text()).toContain('暂无变更')
  })

  it('displays correct counts in summary', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as any
    // 添加一个班级
    vm.addClass('一年级二班')
    // 移除一个班级
    vm.removeClass('一年级一班')
    await flushPromises()

    expect(wrapper.text()).toContain('+1 个新增')
    expect(wrapper.text()).toContain('-1 个移除')
  })

  it('emits update:open when cancel clicked', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as any
    vm.handleClose()
    await flushPromises()

    expect(wrapper.emitted('update:open')).toBeDefined()
    expect(wrapper.emitted('update:open')![0]).toEqual([false])
  })

  it('resets selection when dialog is closed', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as any
    // 添加一个班级
    vm.addClass('一年级二班')
    await flushPromises()

    // 验证有变更
    expect(vm.changes.hasChanges).toBe(true)

    // 关闭弹窗
    vm.handleClose()
    await flushPromises()

    // 选择应该被重置
    expect(vm.selectedClasses).toEqual(['一年级一班'])
  })

  it('displays class status correctly', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // 检查已分配班级中的状态标签
    const text = wrapper.text()
    expect(text).toContain('启用') // 一年级一班是启用的
    
    // 添加一个停用的班级到可分配区域检查
    expect(text).toContain('停用') // 二年级一班是停用的
  })

  it('save button shows correct text based on changes', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    // 无变更时
    expect(wrapper.text()).toContain('暂无变更')

    // 添加变更后
    const vm = wrapper.vm as any
    vm.addClass('一年级二班')
    await flushPromises()

    expect(wrapper.text()).toContain('保存变更 (1)')
  })

  it('handles teacher with invalid assigned classes gracefully', async () => {
    const teacherWithInvalidClasses = {
      ...mockTeacher,
      assigned_classes: ['不存在的班级', '一年级一班']
    }
    const wrapper = mountComponent({ teacher: teacherWithInvalidClasses })
    await flushPromises()

    // 只应该显示存在的班级
    const vm = wrapper.vm as any
    expect(vm.selectedClasses).toEqual(['一年级一班'])
    expect(vm.assignedClassesList.length).toBe(1)
  })

  it('computes changes correctly', async () => {
    const wrapper = mountComponent()
    await flushPromises()

    const vm = wrapper.vm as any
    
    // 初始无变更
    expect(vm.changes.added).toEqual([])
    expect(vm.changes.removed).toEqual([])
    expect(vm.changes.hasChanges).toBe(false)

    // 添加班级
    vm.addClass('一年级二班')
    await flushPromises()
    
    expect(vm.changes.added).toEqual(['一年级二班'])
    expect(vm.changes.removed).toEqual([])
    expect(vm.changes.hasChanges).toBe(true)

    // 同时移除班级
    vm.removeClass('一年级一班')
    await flushPromises()
    
    expect(vm.changes.added).toEqual(['一年级二班'])
    expect(vm.changes.removed).toEqual(['一年级一班'])
    expect(vm.changes.hasChanges).toBe(true)
  })
})
