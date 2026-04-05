import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';

test.describe('Authentication', () => {
  test('should register a new user', async ({ page }) => {
    await page.goto(`${BASE_URL}/register`);
    
    await page.fill('input[name="email"]', `test${Date.now()}@example.com`);
    await page.fill('input[name="password"]', 'Test123456');
    await page.fill('input[name="confirmPassword"]', 'Test123456');
    await page.fill('input[name="fullName"]', 'Test User');
    
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(/\/dashboard|\/login/, { timeout: 10000 });
  });

  test('should login with existing user', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Test123456');
    
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    
    await page.fill('input[name="email"]', 'invalid@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=/错误|失败|invalid/i')).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Task Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Test123456');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
  });

  test('should create a new analysis task', async ({ page }) => {
    await page.click('text=/新建任务|创建任务/i');
    
    await page.fill('input[name="address"]', '北京市朝阳区望京街道');
    await page.selectOption('select[name="propertyType"]', 'residential');
    await page.fill('input[name="area"]', '120');
    await page.fill('input[name="floor"]', '15');
    await page.fill('input[name="totalFloors"]', '30');
    
    await page.click('button:has-text("开始分析")');
    
    await expect(page.locator('text=/任务已创建|分析中/i')).toBeVisible({ timeout: 10000 });
  });

  test('should display task list', async ({ page }) => {
    await page.click('text=/任务列表|任务/i');
    
    await expect(page.locator('table, [role="list"]')).toBeVisible({ timeout: 5000 });
  });

  test('should filter tasks by status', async ({ page }) => {
    await page.click('text=/任务列表|任务/i');
    
    await page.selectOption('select[name="status"]', 'completed');
    
    await expect(page).toHaveURL(/status=completed/);
  });
});

test.describe('Report Viewing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Test123456');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
  });

  test('should navigate to report page', async ({ page }) => {
    await page.click('text=/我的报告|报告/i');
    
    await expect(page).toHaveURL(/\/reports/);
  });

  test('should search reports', async ({ page }) => {
    await page.goto(`${BASE_URL}/reports`);
    
    await page.fill('input[placeholder*="搜索"]', '测试关键词');
    await page.click('button:has-text("搜索")');
    
    await expect(page).toHaveURL(/q=/);
  });

  test('should filter reports by date', async ({ page }) => {
    await page.goto(`${BASE_URL}/reports`);
    
    await page.click('button:has-text("筛选")');
    await page.fill('input[name="start_date"]', '2024-01-01');
    await page.fill('input[name="end_date"]', '2024-12-31');
    await page.click('button:has-text("搜索")');
    
    await expect(page).toHaveURL(/start_date=/);
  });
});

test.describe('Report Sharing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Test123456');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
  });

  test('should create share link', async ({ page }) => {
    await page.goto(`${BASE_URL}/reports`);
    
    const firstReport = page.locator('[data-testid="report-card"], .report-item').first();
    if (await firstReport.isVisible()) {
      await firstReport.click();
      
      const shareButton = page.locator('button:has-text("分享")');
      if (await shareButton.isVisible()) {
        await shareButton.click();
        
        await expect(page.locator('text=/链接已生成|复制链接/i')).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('should access public report', async ({ page }) => {
    await page.goto(`${BASE_URL}/public/test-token-123`);
    
    await expect(page.locator('text=/报告不存在|无法访问/i')).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Comments', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Test123456');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
  });

  test('should add a comment', async ({ page }) => {
    await page.goto(`${BASE_URL}/reports`);
    
    const firstReport = page.locator('[data-testid="report-card"], .report-item').first();
    if (await firstReport.isVisible()) {
      await firstReport.click();
      
      const commentInput = page.locator('textarea[placeholder*="评论"]');
      if (await commentInput.isVisible()) {
        await commentInput.fill('这是一条测试评论');
        await page.click('button:has-text("发布评论")');
        
        await expect(page.locator('text=/评论已发布|测试评论/i')).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('should reply to a comment', async ({ page }) => {
    await page.goto(`${BASE_URL}/reports`);
    
    const firstReport = page.locator('[data-testid="report-card"], .report-item').first();
    if (await firstReport.isVisible()) {
      await firstReport.click();
      
      const replyButton = page.locator('button:has-text("回复")').first();
      if (await replyButton.isVisible()) {
        await replyButton.click();
        
        const replyInput = page.locator('textarea').nth(1);
        await replyInput.fill('这是一条回复');
        await page.click('button:has-text("发送回复")');
        
        await expect(page.locator('text=/回复已发布|这是一条回复/i')).toBeVisible({ timeout: 5000 });
      }
    }
  });
});

test.describe('Notifications', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Test123456');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
  });

  test('should display notification bell', async ({ page }) => {
    const bellIcon = page.locator('[data-testid="notification-bell"], button:has(svg)');
    await expect(bellIcon.first()).toBeVisible();
  });

  test('should open notification dropdown', async ({ page }) => {
    const bellButton = page.locator('button:has(svg)').filter({ hasText: '' }).first();
    await bellButton.click();
    
    await expect(page.locator('text=/通知|暂无通知/i')).toBeVisible({ timeout: 5000 });
  });

  test('should navigate to notifications page', async ({ page }) => {
    await page.goto(`${BASE_URL}/notifications`);
    
    await expect(page.locator('text=/通知中心|通知/i')).toBeVisible();
  });
});

test.describe('Navigation', () => {
  test('should navigate between pages', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Test123456');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
    
    await page.click('text=/任务列表|任务/i');
    await expect(page).toHaveURL(/\/tasks/);
    
    await page.click('text=/我的报告|报告/i');
    await expect(page).toHaveURL(/\/reports/);
    
    await page.click('text=/团队|团队管理/i');
    await expect(page).toHaveURL(/\/teams/);
    
    await page.click('text=/个人资料/i');
    await expect(page).toHaveURL(/\/profile/);
  });

  test('should logout', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Test123456');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
    
    await page.click('text=/退出登录|退出/i');
    
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('Responsive Design', () => {
  test('should display mobile menu', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Test123456');
    await page.click('button[type="submit"]');
    
    const menuButton = page.locator('button:has(svg)').first();
    await expect(menuButton).toBeVisible();
  });

  test('should display desktop sidebar', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Test123456');
    await page.click('button[type="submit"]');
    
    const sidebar = page.locator('nav, aside, [role="navigation"]');
    await expect(sidebar.first()).toBeVisible();
  });
});
