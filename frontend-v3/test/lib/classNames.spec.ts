/**
 * 班级名输入解析测试 - parseClassNames
 */
import { describe, it, expect } from 'vitest'
import { parseClassNames } from '@/lib/classNames'

describe('parseClassNames', () => {
  it('范围写法：1-5 展开为 5 个班级', () => {
    expect(parseClassNames('1-5')).toEqual(['1班', '2班', '3班', '4班', '5班'])
  })

  it('范围倒序：5-1 自动交换为 1~5', () => {
    expect(parseClassNames('5-1')).toEqual(['1班', '2班', '3班', '4班', '5班'])
  })

  it('纯数字枚举：1,2,3 补"班"后缀', () => {
    expect(parseClassNames('1,2,3')).toEqual(['1班', '2班', '3班'])
  })

  it('带后缀枚举：1班,3班 原样保留', () => {
    expect(parseClassNames('1班,3班')).toEqual(['1班', '3班'])
  })

  it('范围与枚举混写：1-3,5班', () => {
    expect(parseClassNames('1-3,5班')).toEqual(['1班', '2班', '3班', '5班'])
  })

  it('非数字 token 原样保留：计算机1班', () => {
    expect(parseClassNames('计算机1班')).toEqual(['计算机1班'])
  })

  it('支持中文分隔符（顿号、中文逗号）并去空白', () => {
    expect(parseClassNames('1班、2班，3班')).toEqual(['1班', '2班', '3班'])
    expect(parseClassNames(' 1班 , 2班 ')).toEqual(['1班', '2班'])
  })

  it('空输入返回空数组', () => {
    expect(parseClassNames('')).toEqual([])
    expect(parseClassNames('  ')).toEqual([])
    expect(parseClassNames(' , 、 ')).toEqual([])
  })

  it('结果去重且保留首次出现顺序', () => {
    expect(parseClassNames('1班,1班')).toEqual(['1班'])
    expect(parseClassNames('2班,1-2')).toEqual(['2班', '1班'])
  })

  it('支持其他连字符（~ ～ —）', () => {
    expect(parseClassNames('1~3')).toEqual(['1班', '2班', '3班'])
    expect(parseClassNames('1～3')).toEqual(['1班', '2班', '3班'])
    expect(parseClassNames('1—2')).toEqual(['1班', '2班'])
  })

  it('单段范围超过 100 个时不报错且结果不超过 100 个', () => {
    const names = parseClassNames('1-500')
    expect(names).toHaveLength(100)
    expect(names[0]).toBe('1班')
    expect(names[99]).toBe('100班')
  })
})
