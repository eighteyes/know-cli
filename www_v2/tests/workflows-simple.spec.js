const { test, expect } = require('@playwright/test');

test.describe('Lucid Dream Workflows - Simplified', () => {

  test.beforeEach(async ({ page, context }) => {
    // Navigate to application with mock mode enabled
    await page.goto('/?mock=true');

    // Clear storage after navigating to avoid cross-test interference
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    // Clear cookies
    await context.clearCookies();

    // Reload to ensure clean state
    await page.reload();

    await expect(page).toHaveTitle('Lucid Dream - Wake. Know. Ship.');
  });

  test('Text Entry Workflow', async ({ page }) => {
    // Enter text and navigate to discover
    await page.fill('#vision-input', 'test workflow entry');
    await page.click('#vision-submit');

    // Verify we're on discover page with sidebar
    await expect(page).toHaveURL(/.*#discover/);
    await expect(page.locator('button[data-page="discover"]')).toBeVisible();
    await expect(page.locator('#current-question')).toBeVisible();
  });

  test('JSON Load Workflow', async ({ page }) => {
    // Use the start page selector to load graph
    await page.selectOption('#start-graph-selector', 'spec-graph.json');

    // Verify navigation and sidebar with data
    await expect(page).toHaveURL(/.*#discover/);
    await expect(page.locator('.accordion-header:has-text("Users")')).toBeVisible();
    await expect(page.locator('.accordion-header:has-text("Objectives")')).toBeVisible();
  });

  test('QA Refinement Basic Flow', async ({ page }) => {
    // Create new project from vision input
    await page.fill('#vision-input', 'qa test project');
    await page.click('#vision-submit');

    // Use mock AI
    await page.fill('#ai-input', 'mock');
    await page.press('#ai-input', 'Enter');

    // Answer questions until we get to modifications
    for (let i = 0; i < 3; i++) {
      await page.fill('#answer-input', `answer ${i + 1}`);
      await page.click('#submit-answer');
      await page.waitForTimeout(500); // Small delay for UI updates
    }

    // Verify modification screen appears
    await expect(page.locator('#extraction-choices')).toBeVisible();
    await expect(page.locator('#detections-list')).toBeVisible();
  });

  test('Modification and Connection Flow', async ({ page }) => {
    // Setup: Create new project and get to modification screen
    await page.fill('#vision-input', 'modification test project');
    await page.click('#vision-submit');
    await page.fill('#ai-input', 'mock');
    await page.press('#ai-input', 'Enter');

    // Answer questions to get to modifications
    for (let i = 0; i < 3; i++) {
      await page.fill('#answer-input', `answer ${i + 1}`);
      await page.click('#submit-answer');
      await page.waitForTimeout(500);
    }

    // Wait for extraction interface to appear after batch completion
    await page.waitForTimeout(1000);

    // Add a modification - wait for the buttons to be available
    await expect(page.locator('#detections-list')).toBeVisible();
    await page.locator('#detections-list button').first().click();

    // Verify pending changes appear
    await expect(page.locator('#pending-changes')).toBeVisible();
    await expect(page.locator('#pending-changes-summary')).toContainText('Entity:');

    // Commit changes
    await page.click('#commit-changes');

    // Verify we're back in QA section (not in modifications anymore)
    await expect(page.locator('#extraction-choices')).not.toBeVisible();
    await expect(page.locator('#current-question')).toBeVisible();
  });

  test('QA Expansion Workflow', async ({ page }) => {
    // Setup: Create new project and get to a question
    await page.fill('#vision-input', 'expansion test project');
    await page.click('#vision-submit');
    await page.fill('#ai-input', 'mock');
    await page.press('#ai-input', 'Enter');

    // Expand options
    await page.click('#expand-toggle');

    // Verify expansion UI
    await expect(page.locator('#expand-options')).toBeVisible();
    await expect(page.locator('.multiple-choice label')).toContainText('Multiple Choice:');

    // Collapse
    await page.click('#expand-toggle');
    await expect(page.locator('#expand-options')).not.toBeVisible();
  });

  test('QA Reorientation Workflow', async ({ page }) => {
    // Create new project
    await page.fill('#vision-input', 'reorientation test project');
    await page.click('#vision-submit');

    // Wait for page to be ready after navigation
    await page.waitForTimeout(500);

    // Use reorientation command
    await page.fill('#ai-input', 'add user tron');
    await page.press('#ai-input', 'Enter');

    // Wait for command to process
    await page.waitForTimeout(500);

    // Verify modification screen with tron entities appears
    await expect(page.locator('#extraction-choices')).toBeVisible();
    await expect(page.locator('#detections-list')).toBeVisible();
    await expect(page.locator('#detections-list')).toContainText('tron');
  });

  test('Basic UI Navigation', async ({ page }) => {
    // Test all main navigation works
    await page.fill('#vision-input', 'navigation test');
    await page.click('#vision-submit');

    // Test page navigation buttons
    await expect(page.locator('button[data-page="start"]')).toBeVisible();
    await expect(page.locator('button[data-page="discover"]')).toBeVisible();
    await expect(page.locator('button[data-page="arrange"]')).toBeVisible();

    // Click arrange
    await page.click('button[data-page="arrange"]');
    await expect(page).toHaveURL(/.*#arrange/);

    // Go back to discover
    await page.click('button[data-page="discover"]');
    await expect(page).toHaveURL(/.*#discover/);
  });

  test('Sub-page Navigation Without Graph Shows Only Top Bar', async ({ page }) => {
    // Navigate directly to discover page without loading a graph
    await page.goto('/?mock=true#discover');

    // Verify we're on the discover page
    await expect(page).toHaveURL(/.*#discover/);

    // Verify top navigation bar is visible
    await expect(page.locator('button[data-page="start"]')).toBeVisible();
    await expect(page.locator('button[data-page="discover"]')).toBeVisible();
    await expect(page.locator('button[data-page="arrange"]')).toBeVisible();

    // Verify working interface sections are hidden (no graph loaded)
    await expect(page.locator('#sidebar')).not.toBeVisible();
    await expect(page.locator('#current-question')).not.toBeVisible();

    // Test arrange page without graph
    await page.click('button[data-page="arrange"]');
    await expect(page).toHaveURL(/.*#arrange/);

    // Top bar should still be visible
    await expect(page.locator('button[data-page="start"]')).toBeVisible();
    await expect(page.locator('button[data-page="discover"]')).toBeVisible();
    await expect(page.locator('button[data-page="arrange"]')).toBeVisible();

    // Go back to start page and load a graph to test interface activation
    await page.click('button[data-page="start"]');
    await page.selectOption('#start-graph-selector', 'spec-graph.json');

    // Now interface should be visible
    await expect(page.locator('#sidebar')).toBeVisible();
    await expect(page.locator('.accordion-header:has-text("Users")')).toBeVisible();
  });
});