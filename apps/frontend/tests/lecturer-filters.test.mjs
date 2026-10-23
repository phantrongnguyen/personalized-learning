import { test } from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';

const { outputFiles } = await build({
  entryPoints: ['src/utils/lecturerFilters.ts'], bundle: true, write: false,
  format: 'esm', platform: 'node',
});
const { filterCourseStudents } = await import(`data:text/javascript;base64,${Buffer.from(outputFiles[0].text).toString('base64')}`);
const students = [
  { student_code: 'OULAD-3', full_name: 'Nguyễn Bảo', risk_status: 'HIGH_RISK', risk_probability: .91, submission_rate: .25 },
  { student_code: 'OULAD-1', full_name: 'An', risk_status: 'SAFE', risk_probability: .2, submission_rate: .8 },
  { student_code: 'OULAD-2', full_name: 'Bình', risk_status: 'NOT_PREDICTED', risk_probability: null, submission_rate: null },
];

test('lecturer search ignores accents and filters risk within a course', () => {
  assert.deepEqual(filterCourseStudents(students, 'nguyen bao', 'HIGH_RISK', 'risk').map(item => item.student_code), ['OULAD-3']);
  assert.deepEqual(filterCourseStudents(students, 'OULAD-2', 'ALL', 'risk').map(item => item.student_code), ['OULAD-2']);
  assert.deepEqual(filterCourseStudents(students, '', 'SAFE', 'risk').map(item => item.student_code), ['OULAD-1']);
  assert.deepEqual(filterCourseStudents(students, 'nobody', 'ALL', 'risk'), []);
});

test('sorts by risk by default and places missing submission data last', () => {
  assert.deepEqual(filterCourseStudents(students, '', 'ALL', 'risk').map(item => item.student_code), ['OULAD-3', 'OULAD-1', 'OULAD-2']);
  assert.deepEqual(filterCourseStudents(students, '', 'ALL', 'submission').map(item => item.student_code), ['OULAD-3', 'OULAD-1', 'OULAD-2']);
  assert.deepEqual(filterCourseStudents(students, '', 'ALL', 'name').map(item => item.student_code), ['OULAD-1', 'OULAD-2', 'OULAD-3']);
  assert.equal(students[0].student_code, 'OULAD-3');
});