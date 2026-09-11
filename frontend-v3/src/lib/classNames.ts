/**
 * 班级名输入解析
 *
 * 供"创建班级"弹窗使用：用户可一次输入多个班级名，
 * 支持范围写法与枚举写法混写，前端解析后交给批量创建接口。
 */

/** 分隔符：英文逗号、中文逗号、顿号 */
const SEPARATOR = /[,，、]/

/** 范围写法：数字 + 连字符 + 数字（- ~ ～ — 均视为连字符） */
const RANGE = /^(\d+)\s*[-~～—]\s*(\d+)$/

/** 纯数字 token */
const PURE_NUMBER = /^\d+$/

/** 单个范围段展开的上限，超出部分丢弃（不报错） */
const MAX_RANGE_SIZE = 100

/**
 * 解析班级名输入（支持范围与枚举混写）
 *
 *   "1-5"       → ["1班","2班","3班","4班","5班"]
 *   "1,2,3"     → ["1班","2班","3班"]
 *   "1班,3班"   → ["1班","3班"]
 *   "1-3,5班"   → ["1班","2班","3班","5班"]
 *   "计算机1班"  → ["计算机1班"]
 *
 * 规则：
 * 1. 按 , ， 、 分隔，去空白，丢空项
 * 2. 形如 "N-M"（含 - ~ ～ — 等连字符）→ 展开为 "N班".."M班"（起止含；N>M 时自动交换；单段上限 100 个，超限只取前 100 并保持不报错）
 * 3. 纯数字 token → 补 "班" 后缀
 * 4. 其余 token 原样保留
 * 5. 结果去重（保留首次出现顺序）
 * 6. 空输入返回 []
 */
export function parseClassNames(input: string): string[] {
  if (!input || !input.trim()) return []

  const result: string[] = []
  const seen = new Set<string>()

  const push = (name: string) => {
    if (seen.has(name)) return
    seen.add(name)
    result.push(name)
  }

  for (const raw of input.split(SEPARATOR)) {
    const token = raw.trim()
    if (!token) continue

    const range = token.match(RANGE)
    if (range) {
      const start = Math.min(Number(range[1]), Number(range[2]))
      const end = Math.max(Number(range[1]), Number(range[2]))
      const limit = Math.min(end, start + MAX_RANGE_SIZE - 1)
      for (let i = start; i <= limit; i++) push(`${i}班`)
      continue
    }

    if (PURE_NUMBER.test(token)) {
      push(`${token}班`)
      continue
    }

    push(token)
  }

  return result
}
