import { CourseStudentRiskItem, RiskLevel } from '@shared/types';

export type RiskFilter = 'ALL' | RiskLevel;
export type StudentSort = 'risk' | 'name' | 'submission';

const normalizeSearch = (value: string): string => value.trim().toLocaleLowerCase('vi-VN')
  .normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd');

export function filterCourseStudents(
  students: CourseStudentRiskItem[], search: string, filter: RiskFilter, sort: StudentSort
): CourseStudentRiskItem[] {
  const query = normalizeSearch(search);
  return students.filter((student) =>
    (filter === 'ALL' || student.risk_status === filter) &&
    (!query || normalizeSearch(`${student.student_code} ${student.full_name}`).includes(query))
  ).sort((left, right) => {
    if (sort === 'name') return left.full_name.localeCompare(right.full_name, 'vi');
    if (sort === 'submission') return (left.submission_rate ?? 2) - (right.submission_rate ?? 2)
      || left.student_code.localeCompare(right.student_code);
    const leftRisk = left.risk_status === 'HIGH_RISK' ? 1 : 0;
    const rightRisk = right.risk_status === 'HIGH_RISK' ? 1 : 0;
    return rightRisk - leftRisk || (right.risk_probability ?? -1) - (left.risk_probability ?? -1)
      || left.student_code.localeCompare(right.student_code);
  });
}