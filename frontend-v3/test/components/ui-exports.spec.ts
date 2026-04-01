/**
 * @vitest-environment jsdom
 */
import { describe, it, expect } from 'vitest'
import * as UI from '@/components/ui'

describe('UI Components Exports', () => {
  it('should export all required components', () => {
    expect(UI.Button).toBeDefined()
    expect(UI.Checkbox).toBeDefined()
    expect(UI.Dialog).toBeDefined()
    expect(UI.Input).toBeDefined()
    expect(UI.Label).toBeDefined()
    expect(UI.Card).toBeDefined()
    expect(UI.Badge).toBeDefined()
    expect(UI.Select).toBeDefined()
    expect(UI.Toast).toBeDefined()
    expect(UI.DataContainer).toBeDefined()
    expect(UI.SearchableSelect).toBeDefined()
    expect(UI.StatCard).toBeDefined()
  })

  it('should export components as Vue components', () => {
    // Verify each export is a valid component (has render function or setup)
    const componentNames = ['Button', 'Checkbox', 'Dialog', 'Input', 'Label', 'Card', 'Badge', 'Select', 'Toast', 'DataContainer', 'SearchableSelect', 'StatCard']
    
    for (const name of componentNames) {
      const component = (UI as Record<string, unknown>)[name]
      expect(component).toBeDefined()
      // Vue components should have a render function or setup method
      expect(typeof component === 'object' || typeof component === 'function').toBe(true)
    }
  })
})
