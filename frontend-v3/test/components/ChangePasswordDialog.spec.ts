/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import ChangePasswordDialog from '../../src/components/ui/ChangePasswordDialog.vue'

// --- Mocks ---

const changePasswordMock = vi.fn()
vi.mock('@/api', () => ({
  authApi: {
    changePassword: (...args: unknown[]) => changePasswordMock(...args),
  },
}))

const successToastMock = vi.fn()
const errorToastMock = vi.fn()
vi.mock('@/composables', () => ({
  useToast: () => ({
    success: successToastMock,
    error: errorToastMock,
  }),
}))

vi.mock('@/lib/error', () => ({
  getErrorMessage: (err: unknown) =>
    err instanceof Error ? err.message : '操作失败',
}))

vi.mock('@vueuse/core', () => ({
  useScrollLock: () => ({ value: false }),
}))

// --- Query Client Helper ---

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
    },
  })
}

// --- Stubs ---

/**
 * Dialog stub: renders slot content, exposes onSubmit via props.
 * When the internal form is "submitted" by the user, the stub calls props.onSubmit.
 * The stub renders a <form> element so tests can dispatch a submit event on it.
 */
const DialogStub = defineComponent({
  name: 'Dialog',
  props: {
    open: { type: Boolean, default: false },
    title: { type: String, default: '' },
    description: { type: String, default: '' },
    asForm: { type: Boolean, default: false },
    onSubmit: { type: Function, default: undefined },
  },
  emits: ['update:open'],
  setup(props, { slots }) {
    const handleSubmit = (e: Event) => {
      e.preventDefault()
      props.onSubmit?.(e)
    }
    return () =>
      h(
        'form',
        {
          'data-test': 'dialog-stub',
          'data-open': props.open,
          onSubmit: handleSubmit,
        },
        [
          slots.default?.(),
          h('div', { 'data-test': 'dialog-footer' }, slots.footer?.()),
        ],
      )
  },
})

/**
 * Input stub: renders a native <input> and emits update:modelValue on input.
 */
const InputStub = defineComponent({
  name: 'Input',
  props: {
    modelValue: { type: [String, Number], default: '' },
    id: { type: String, default: undefined },
    type: { type: String, default: 'text' },
    placeholder: { type: String, default: '' },
    disabled: { type: Boolean, default: false },
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('input', {
        id: props.id,
        'data-test': `input-${props.id}`,
        value: props.modelValue,
        type: props.type,
        placeholder: props.placeholder,
        disabled: props.disabled,
        onInput: (e: Event) => {
          const target = e.target as HTMLInputElement
          emit('update:modelValue', target.value)
        },
      })
  },
})

const LabelStub = {
  name: 'Label',
  template: '<label><slot /></label>',
}

const ButtonStub = {
  name: 'Button',
  template: '<button><slot /></button>',
  props: ['variant', 'type', 'loading'],
}

// --- Helpers ---

function mountComponent(props = { open: true }) {
  const queryClient = createTestQueryClient()
  return mount(ChangePasswordDialog, {
    props,
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        Dialog: DialogStub,
        Input: InputStub,
        Label: LabelStub,
        Button: ButtonStub,
      },
    },
  })
}

/**
 * Fill an input identified by data-test attribute.
 */
async function fillInput(
  wrapper: ReturnType<typeof mount>,
  testId: string,
  value: string,
) {
  const input = wrapper.find(`[data-test="${testId}"]`)
  await input.setValue(value)
}

/**
 * Submit the dialog form.
 */
async function submitForm(wrapper: ReturnType<typeof mount>) {
  await wrapper.find('[data-test="dialog-stub"]').trigger('submit')
  await flushPromises()
}

// --- Tests ---

describe('ChangePasswordDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders three input fields when open', () => {
    const wrapper = mountComponent()

    expect(wrapper.find('[data-test="input-old-password"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="input-new-password"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="input-confirm-password"]').exists()).toBe(true)
  })

  it('shows "请输入旧密码" error when submitting empty form', async () => {
    const wrapper = mountComponent()

    await submitForm(wrapper)

    expect(wrapper.text()).toContain('请输入旧密码')
    expect(changePasswordMock).not.toHaveBeenCalled()
  })

  it('shows error when new password is less than 6 characters', async () => {
    const wrapper = mountComponent()

    await fillInput(wrapper, 'input-old-password', 'oldpass123')
    await fillInput(wrapper, 'input-new-password', '12345')
    await fillInput(wrapper, 'input-confirm-password', '12345')
    await submitForm(wrapper)

    expect(wrapper.text()).toContain('新密码至少需要 6 个字符')
    expect(changePasswordMock).not.toHaveBeenCalled()
  })

  it('shows "两次输入的新密码不一致" error when passwords do not match', async () => {
    const wrapper = mountComponent()

    await fillInput(wrapper, 'input-old-password', 'oldpass123')
    await fillInput(wrapper, 'input-new-password', 'newpass123')
    await fillInput(wrapper, 'input-confirm-password', 'different1')
    await submitForm(wrapper)

    expect(wrapper.text()).toContain('两次输入的新密码不一致')
    expect(changePasswordMock).not.toHaveBeenCalled()
  })

  it('calls authApi.changePassword with correct arguments on valid submit', async () => {
    changePasswordMock.mockResolvedValue(undefined)
    const wrapper = mountComponent()

    await fillInput(wrapper, 'input-old-password', 'oldpass123')
    await fillInput(wrapper, 'input-new-password', 'newpass123')
    await fillInput(wrapper, 'input-confirm-password', 'newpass123')
    await submitForm(wrapper)

    expect(changePasswordMock).toHaveBeenCalledWith({
      old_password: 'oldpass123',
      new_password: 'newpass123',
    })
  })

  it('emits update:open with false and shows success toast on successful submit', async () => {
    changePasswordMock.mockResolvedValue(undefined)
    const wrapper = mountComponent()

    await fillInput(wrapper, 'input-old-password', 'oldpass123')
    await fillInput(wrapper, 'input-new-password', 'newpass123')
    await fillInput(wrapper, 'input-confirm-password', 'newpass123')
    await submitForm(wrapper)
    await flushPromises()

    expect(wrapper.emitted('update:open')).toBeTruthy()
    expect(wrapper.emitted('update:open')!.at(-1)!).toEqual([false])
    expect(successToastMock).toHaveBeenCalledWith('密码修改成功')
  })

  it('shows error toast on API failure', async () => {
    changePasswordMock.mockRejectedValue(new Error('旧密码错误'))
    const wrapper = mountComponent()

    await fillInput(wrapper, 'input-old-password', 'wrongpass')
    await fillInput(wrapper, 'input-new-password', 'newpass123')
    await fillInput(wrapper, 'input-confirm-password', 'newpass123')
    await submitForm(wrapper)
    await flushPromises()

    expect(errorToastMock).toHaveBeenCalledWith('旧密码错误')
    // Should NOT emit close
    expect(wrapper.emitted('update:open')).toBeFalsy()
  })

  it('emits update:open with false when close handler is triggered', async () => {
    const wrapper = mountComponent()

    // The "取消" button triggers handleClose
    const cancelButton = wrapper.findAll('button').find((b) => b.text().includes('取消'))
    expect(cancelButton).toBeDefined()
    await cancelButton!.trigger('click')
    await flushPromises()

    expect(wrapper.emitted('update:open')).toBeTruthy()
    expect(wrapper.emitted('update:open')![0]).toEqual([false])
  })

  it('shows "请输入新密码" error when old password is filled but new is empty', async () => {
    const wrapper = mountComponent()

    await fillInput(wrapper, 'input-old-password', 'oldpass123')
    // new_password and confirm_password are empty
    await submitForm(wrapper)

    expect(wrapper.text()).toContain('请输入新密码')
    expect(changePasswordMock).not.toHaveBeenCalled()
  })
})
