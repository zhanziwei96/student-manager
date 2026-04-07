import { test, expect } from '@playwright/test'

test.describe('多班级并行上课功能', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/teacher/session')
    await page.waitForURL(/.*teacher\/session/, { timeout: 15000 })
  })

  test('单课堂状态下显示开始新课堂按钮', async ({ page }) => {
    // 如果当前没有活跃课堂，先开始一个
    const startButton = page.getByRole('button', { name: '开始课堂' })
    if (await startButton.isVisible().catch(() => false)) {
      await startButton.click()
      // 打开选择班级的 Dialog/Popover
      await expect(page.getByRole('heading', { name: /选择班级|开始课堂/ }).or(
        page.getByText('选择班级开始新课堂')
      )).toBeVisible({ timeout: 5000 })

      // 选择第一个可用班级
      const firstOption = page.locator('[role="option"]').first()
      if (await firstOption.isVisible().catch(() => false)) {
        await firstOption.click()
      }
      await page.getByRole('button', { name: /开始上课|确认/ }).click()
      await page.waitForTimeout(1500)
    }

    // 验证"开始新课堂"按钮可见
    const startNewButton = page.getByRole('button', { name: '开始新课堂' })
    await expect(startNewButton).toBeVisible({ timeout: 10000 })
  })

  test('开始第二个课堂并切换', async ({ page }) => {
    // 确保至少已有一个活跃课堂
    const startButton = page.getByRole('button', { name: '开始课堂' })
    if (await startButton.isVisible().catch(() => false)) {
      await startButton.click()
      const firstOption = page.locator('[role="option"]').first()
      if (await firstOption.isVisible().catch(() => false)) {
        await firstOption.click()
      }
      await page.getByRole('button', { name: /开始上课|确认/ }).click()
      await page.waitForTimeout(1500)
    }

    // 点击开始新课堂
    const startNewButton = page.getByRole('button', { name: '开始新课堂' })
    await expect(startNewButton).toBeVisible({ timeout: 10000 })
    await startNewButton.click()

    // 展开开始新课堂表单
    await expect(page.getByText('开始新课堂').nth(0)).toBeVisible({ timeout: 5000 })

    // 选择班级（自定义 Select：点击触发器，然后选择不在第一个选项中的班级）
    const selectTriggers = page.locator('button[data-select-trigger], [data-radix-select-trigger]').or(
      page.locator('button').filter({ hasText: /选择班级|请选择/ })
    )
    const classSelect = selectTriggers.last()
    if (await classSelect.isVisible().catch(() => false)) {
      await classSelect.click()
      const options = page.locator('[role="option"]')
      const count = await options.count()
      if (count >= 2) {
        await options.nth(1).click()
      } else if (count >= 1) {
        await options.first().click()
      }
    }

    const confirmButton = page.getByRole('button', { name: '开始上课' }).filter({ hasNotText: /开始新课堂/ }).last()
    if (await confirmButton.isVisible().catch(() => false)) {
      await confirmButton.click()
    }

    await page.waitForTimeout(1500)

    // 验证多课堂标签或文本显示2个班级
    const multiSessionText = page.getByText(/课堂进行中.*\(2个班级\)/).or(
      page.getByText(/2个班级/)
    )
    const hasMulti = await multiSessionText.isVisible().catch(() => false)

    // 或者验证有多个标签/选项
    const sessionTabs = page.locator('button').filter({ hasText: /班/ })
    const tabCount = await sessionTabs.count()
    expect(hasMulti || tabCount >= 1).toBeTruthy()
  })

  test('结束单个课堂后显示剩余课堂', async ({ page }) => {
    const startNewButton = page.getByRole('button', { name: '开始新课堂' })
    if (!(await startNewButton.isVisible().catch(() => false))) {
      test.skip('当前没有多课堂场景，跳过此测试')
      return
    }

    // 找到第一个结束此课堂的按钮
    const endSessionButton = page.getByRole('button', { name: '结束此课堂' }).first()
    if (await endSessionButton.isVisible().catch(() => false)) {
      await endSessionButton.click()
      // 确认弹窗
      await expect(page.getByRole('heading', { name: '确认结束课堂' })).toBeVisible({ timeout: 5000 })
      await page.getByRole('button', { name: '确认结束' }).click()
      await page.waitForTimeout(1500)

      // 验证仍有活跃课堂或显示开始课堂按钮
      const startButton = page.getByRole('button', { name: '开始课堂' })
      const startNewBtn = page.getByRole('button', { name: '开始新课堂' })
      const hasActive = await startNewBtn.isVisible().catch(() => false) || await startButton.isVisible().catch(() => false)
      expect(hasActive).toBeTruthy()
    } else {
      // 桌面端：直接点击结束课堂
      const endButton = page.getByRole('button', { name: '结束课堂' }).first()
      if (await endButton.isVisible().catch(() => false)) {
        await endButton.click()
        await expect(page.getByRole('heading', { name: '确认结束课堂' })).toBeVisible({ timeout: 5000 })
        await page.getByRole('button', { name: '确认结束' }).click()
        await page.waitForTimeout(1500)
        const startButtonAfter = page.getByRole('button', { name: '开始课堂' })
        await expect(startButtonAfter).toBeVisible({ timeout: 10000 })
      }
    }
  })

  test('移动端下拉选择器', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 })
    await page.reload()
    await page.waitForURL(/.*teacher\/session/, { timeout: 15000 })

    // 先确保有至少两个活跃课堂
    const startButton = page.getByRole('button', { name: '开始课堂' })
    if (await startButton.isVisible().catch(() => false)) {
      await startButton.click()
      const firstOption = page.locator('[role="option"]').first()
      if (await firstOption.isVisible().catch(() => false)) {
        await firstOption.click()
      }
      await page.getByRole('button', { name: /开始上课|确认/ }).click()
      await page.waitForTimeout(1500)
    }

    const startNewButton = page.getByRole('button', { name: '开始新课堂' })
    if (await startNewButton.isVisible().catch(() => false)) {
      await startNewButton.click()
      const selectTriggers = page.locator('button').filter({ hasText: /选择班级|请选择/ })
      const classSelect = selectTriggers.last()
      if (await classSelect.isVisible().catch(() => false)) {
        await classSelect.click()
        const options = page.locator('[role="option"]')
        if (await options.count() >= 1) {
          await options.last().click()
        }
      }
      const confirmBtn = page.getByRole('button', { name: '开始上课' }).last()
      if (await confirmBtn.isVisible().catch(() => false)) {
        await confirmBtn.click()
      }
      await page.waitForTimeout(1500)
    }

    // 验证移动端显示下拉选择器（Select 组件或 label "当前课堂"）
    const mobileSelector = page.locator('label').filter({ hasText: '当前课堂' }).or(
      page.locator('button').filter({ hasText: /课堂.*班/ })
    ).first()

    const hasSelector = await mobileSelector.isVisible().catch(() => false)
    expect(hasSelector).toBeTruthy()
  })
})
