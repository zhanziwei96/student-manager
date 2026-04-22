import { useQuery } from '@tanstack/vue-query'
import { getStudentQuestions } from '@/api/question'

const STUDENT_QUESTIONS_KEY = 'student-questions'

export function useStudentQuestions() {
  const { data: questions, isLoading, error } = useQuery({
    queryKey: [STUDENT_QUESTIONS_KEY],
    queryFn: () => getStudentQuestions(),
  })

  return {
    questions,
    isLoading,
    error,
  }
}
