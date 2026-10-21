import { test, expect, Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';

const fixturePath = path.join(process.env.E2E_PRIVATE_DIR!, 'fixture.json');
const readFixture = () => JSON.parse(readFileSync(fixturePath, 'utf8'));
const f = readFixture();
const headers = (token: string) => ({ Authorization: `Bearer ${token}` });

async function login(page: Page, username: string, password: string, staff = true) {
  await page.goto('/app/');
  await page.locator('#login-mode').selectOption(staff ? 'staff' : 'student');
  await page.locator('#login-username').fill(username);
  await page.locator('input[type=password]').fill(password);
  const response = page.waitForResponse(r => r.url().endsWith('/api/v1/auth/login') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).last().click();
  const result = await response;
  expect(result.status()).toBe(200);
  await expect(page.locator('#login-username')).not.toBeVisible();
  return (await result.json()).access_token as string;
}

test('account, import, reviewed suggestion, real inference, plan, task and completion', async ({ browser, request }) => {
  const pages: Page[] = [];
  async function actor() { const context = await browser.newContext(); const page = await context.newPage(); pages.push(page); return page; }
  const admin = await actor();
  const adminToken = await login(admin, 'admin@huit.edu.vn', 'admin');
  await test.step('create student through the real administrator UI', async () => {
    await admin.getByRole('button', { name: 'Cấp tài khoản', exact: true }).click();
    const dialog = admin.getByRole('dialog', { name: 'Cấp tài khoản mới' });
    await dialog.locator('[name=full_name]').fill('E2E Student');
    await dialog.locator('[name=email]').fill(f.student_email);
    await dialog.locator('[name=student_code]').fill(f.student_code);
    await dialog.locator('[name=password]').fill(f.password);
    await dialog.getByRole('button', { name: 'Cấp tài khoản', exact: true }).click();
    await expect(dialog).not.toBeVisible();
  });
  // Explicit import/API boundaries: these administration/import screens do not exist yet.
  execFileSync(process.env.E2E_PYTHON!, ['e2e/import_fixture.py'], { cwd: process.cwd(), env: process.env, stdio: 'pipe' });
  const imported = readFixture();
  const assigned = await request.post('/api/v1/admin/academic/assign-advisor', { headers: headers(adminToken), data: {
    advisor_id: f.advisor.advisor_profile.id, student_id: imported.student_id, class_name: 'E2E class',
  } });
  expect(assigned.ok()).toBeTruthy();
  const teacher = await actor();
  const teacherToken = await login(teacher, f.lecturer.email, f.password);
  const row = teacher.getByRole('row').filter({ hasText: 'E2E Student' });
  await row.getByRole('button', { name: 'Xem gợi ý', exact: true }).click();
  await test.step('missing metadata and missing active plan remain explicit', async () => {
    await expect(teacher.getByText('Chưa đủ dữ liệu đã xác nhận để gợi ý nhiệm vụ cụ thể.', { exact: true })).toBeVisible();
    await expect(teacher.getByText('Chưa thể giao nhiệm vụ:', { exact: false })).toBeVisible();
    await expect(teacher.getByRole('button', { name: 'Giao bài tập', exact: true })).toHaveCount(0);
    await teacher.screenshot({ path: '../../reports/test-results/browser/missing-evidence.png', fullPage: true });
  });
  await test.step('review demonstration explicitly; no flags preselected', async () => {
    await teacher.getByText('Rà soát và xác nhận nguồn snapshot', { exact: true }).click();
    await teacher.getByRole('button', { name: 'Đọc snapshot từ database', exact: true }).click();
    const panel = teacher.locator('details').filter({ has: teacher.getByText('Rà soát và xác nhận nguồn snapshot', { exact: true }) });
    await panel.getByRole('combobox').selectOption('demonstration');
    const checks = panel.getByRole('checkbox');
    for (let i = 0; i < 3; i++) await expect(checks.nth(i)).not.toBeChecked();
    await panel.locator('input[type=text], input:not([type])').fill('Isolated E2E database fixture');
    await panel.locator('textarea').fill('Reviewed a synthetic fixture solely to test the workflow; not real LMS evidence.');
    for (let i = 0; i < 3; i++) await checks.nth(i).check();
    await panel.getByRole('button', { name: 'Lưu xác nhận', exact: true }).click();
    await expect(teacher.getByText('Có gợi ý để giảng viên tham khảo.', { exact: true })).toBeVisible();
    await expect(teacher.getByText('Dữ liệu minh họa, không phải bằng chứng LMS thực.', { exact: true })).toBeVisible();
  });
  await test.step('batch real artifact inference via existing administrator API', async () => {
    const response = await request.post(`/api/v1/admin/ml/batch-predict?enrollment_id=${imported.enrollment_id}`, { headers: headers(adminToken) });
    expect(response.ok()).toBeTruthy(); expect((await response.json()).predictions_generated).toBe(1);
  });
  const advisor = await actor();
  const advisorToken = await login(advisor, f.advisor.email, f.password);
  await test.step('advisor creates plan and first task in browser', async () => {
    const studentRow = advisor.getByRole('row').filter({ hasText: 'E2E Student' });
    await expect(studentRow.getByRole('button', { name: 'Can thiệp', exact: true })).toBeEnabled();
    await studentRow.getByRole('button', { name: 'Can thiệp', exact: true }).click();
    await advisor.getByRole('combobox').filter({ has: advisor.locator(`option[value="${imported.enrollment_id}"]`) }).selectOption(imported.enrollment_id);
    await advisor.getByPlaceholder('Tên nhiệm vụ', { exact: true }).fill('E2E advisor task');
    await advisor.getByPlaceholder('Mô tả nhiệm vụ', { exact: true }).fill('Discuss the timetable using a synthetic test case.');
    await advisor.getByRole('button', { name: 'Lưu kế hoạch can thiệp', exact: true }).click();
    await expect(advisor.getByRole('button', { name: 'Lưu kế hoạch can thiệp', exact: true })).not.toBeVisible();
  });
  await test.step('lecturer selects a suggestion, edits draft, then explicitly assigns', async () => {
    await teacher.reload();
    await teacher.getByRole('button', { name: /Lớp học phần/ }).click();
    await teacher.getByRole('row').filter({ hasText: 'E2E Student' }).getByRole('button', { name: 'Xem gợi ý', exact: true }).click();
    await teacher.getByRole('button', { name: 'Chọn để điền nháp (có thể chỉnh sửa)', exact: true }).first().click();
    const form = teacher.locator('form').filter({ has: teacher.getByRole('button', { name: 'Giao bài tập', exact: true }) });
    await form.locator('input[type=text]').nth(0).fill('E2E lecturer edited task');
    await form.locator('textarea').fill('Lecturer edited the proposed action for this synthetic fixture.');
    await form.getByRole('combobox').selectOption('LOW');
    await form.locator('input[type=text]').nth(1).fill('Review the timetable together');
    await form.getByRole('button', { name: 'Giao bài tập', exact: true }).click();
    await expect(form).not.toBeVisible();
  });
  const student = await actor();
  const studentToken = await login(student, f.student_code, f.password, false);
  await test.step('student sees reminder and completes both persisted tasks in browser', async () => {
    await student.getByRole('button', { name: /Thông báo môn học,/ }).click();
    await expect(student.getByRole('region', { name: 'Thông báo nhắc nhở môn học' })).toContainText('BBB');
    await student.getByRole('button', { name: /Thông báo môn học,/ }).click();
    await expect(student.getByRole('button', { name: 'Đánh dấu hoàn thành', exact: true })).toHaveCount(2);
    await student.screenshot({ path: '../../reports/test-results/browser/student-tasks.png', fullPage: true });
    await student.getByRole('button', { name: 'Đánh dấu hoàn thành', exact: true }).first().click();
    await expect(student.getByRole('button', { name: 'Đánh dấu hoàn thành', exact: true })).toHaveCount(1);
    await student.getByRole('button', { name: 'Đánh dấu hoàn thành', exact: true }).click();
    await expect(student.getByText('Đã hoàn thành (2)', { exact: true })).toBeVisible();
    await student.getByRole('button', { name: /Thông báo môn học,/ }).click();
    await expect(student.getByText('Bạn chưa có nhiệm vụ môn học cần nhắc nhở.', { exact: true })).toBeVisible();
    await student.screenshot({ path: '../../reports/test-results/browser/completed.png', fullPage: true });
    const reminders = await request.get('/api/v1/student/reminders', { headers: headers(studentToken) });
    expect(await reminders.json()).toEqual([]);
    const summary = await request.get('/api/v1/advisor/students', { headers: headers(advisorToken) });
    expect((await summary.json()).find((s: any) => s.student_id === imported.student_id).uncompleted_tasks_count).toBe(0);
  });
  await test.step('server denies cross-course and student-to-staff access', async () => {
    const denied = await request.get(`/api/v1/lecturer/courses/${f.foreign_presentation.id}/students/${imported.student_id}/suggestions`, { headers: headers(teacherToken) });
    expect(denied.status()).toBe(403);
    expect((await request.get('/api/v1/lecturer/courses', { headers: headers(studentToken) })).status()).toBe(403);
    await teacher.reload();
    await teacher.getByRole('button', { name: /Lớp học phần/ }).click();
    await expect(teacher.getByText(f.foreign_presentation.code_presentation, { exact: false })).toHaveCount(0);
  });
  for (const page of pages) await page.context().close();
});

test('invalid login stays on authentication screen', async ({ page }) => {
  await page.goto('/app/');
  await page.locator('#login-mode').selectOption('staff');
  await page.locator('#login-username').fill('admin@huit.edu.vn');
  await page.locator('input[type=password]').fill('incorrect-e2e-password');
  const response = page.waitForResponse(r => r.url().endsWith('/api/v1/auth/login'));
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).last().click();
  expect((await response).status()).toBe(401);
  await expect(page.locator('#login-username')).toBeVisible();
});
