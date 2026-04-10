import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merge Tailwind classes with proper precedence
 * Based on: https://github.com/shadcn/ui/blob/main/packages/lib/utils.ts
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format number with locale
 */
export function formatNumber(num: number): string {
  return new Intl.NumberFormat('zh-CN').format(num)
}

/**
 * Format date to Chinese locale
 */
export function formatDate(date: string | Date): string {
  const d = new Date(date)
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(d)
}

/**
 * Format duration in seconds to HH:MM:SS
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

/**
 * Get color class based on score
 */
export function getScoreColor(score: number): string {
  if (score >= 90) return 'text-emerald-400'
  if (score >= 80) return 'text-blue-400'
  if (score >= 60) return 'text-yellow-400'
  return 'text-red-400'
}

/**
 * Get background color class based on score
 */
export function getScoreBgColor(score: number): string {
  if (score >= 90) return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
  if (score >= 80) return 'bg-blue-500/10 text-blue-400 border-blue-500/20'
  if (score >= 60) return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
  return 'bg-red-500/10 text-red-400 border-red-500/20'
}

/**
 * Get initials from name
 */
export function getInitials(name: string): string {
  return name.slice(0, 1).toUpperCase()
}

/**
 * Generate avatar gradient based on name
 */
export function generateAvatarColor(name: string): string {
  const colors = [
    'bg-[#e5e5e5] text-[#7c3aed]',
    'bg-[#e5e5e5] text-[#0891b2]',
    'bg-[#e5e5e5] text-[#10b981]',
    'bg-[#e5e5e5] text-[#f59e0b]',
    'bg-[#e5e5e5] text-[#ec4899]',
    'bg-[#e5e5e5] text-[#6366f1]',
  ]
  const index = name.charCodeAt(0) % colors.length
  return colors[index]
}
