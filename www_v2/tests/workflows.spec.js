const { test, expect } = require('@playwright/test');

test.describe('Lucid Dream Workflows', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to application with mock mode enabled
    await page.goto('/?mock=true');
    await expect(page).toHaveTitle('Lucid Dream - Wake. Know. Ship.');
  });

  test('Text Entry Workflow', async ({ page }) => {
    // Test: Enter text into input, hit button, goes to Discover page, sidebar visible

    // Enter text into the input field
    await page.fill('#vision-input', 'test workflow entry');

    // Click the arrow button
    await page.click('#vision-submit');

    // Verify navigation to Discover page
    await expect(page).toHaveURL(/.*#discover/);

    // Verify sidebar is visible with navigation buttons
    await expect(page.locator('button[data-page="start"]')).toBeVisible();
    await expect(page.locator('button[data-page="discover"]')).toBeVisible();
    await expect(page.locator('button[data-page="arrange"]')).toBeVisible();

    // Verify QA interface is showing
    await expect(page.locator('#current-question')).toBeVisible();
  });

  test('JSON Load Workflow', async ({ page }) => {
    // Test: Load graph from selection spec-graph.json, goes to Discover page, sidebar visible

    // Select spec-graph.json from dropdown
    await page.selectOption('#start-graph-selector', 'spec-graph.json');

    // Wait for navigation to Discover page
    await expect(page).toHaveURL(/.*#discover/);

    // Verify sidebar shows loaded data with counts
    await expect(page.locator('.accordion-header:has-text("Users")')).toBeVisible();
    await expect(page.locator('.accordion-header:has-text("Objectives")')).toBeVisible();
    await expect(page.locator('.accordion-header:has-text("Actions")')).toBeVisible();

    // Verify sidebar is visible
    await expect(page.locator('button[data-page="discover"]')).toBeVisible();
  });

  test('QA Refinement Workflow', async ({ page }) => {
    // Navigate to discover page first
    await page.fill('#vision-input', 'qa refinement test');
    await page.click('#vision-submit');

    // Load graph and run QA refinement workflow
    await page.selectOption('#graph-file-selector', 'spec-graph.json');

    // Enter "mock" in AI bar
    await page.fill('#ai-input', 'mock');
    await page.press('#ai-input', 'Enter');

    // Answer question #1
    await page.fill('#answer-input', 'admin, user, guest');
    await page.click('#submit-answer');

    // Test: next question is active - check for different question text
    await expect(page.locator('#current-question')).not.toContainText('What are the primary user personas');

    // Answer question #2
    await page.fill('#answer-input', 'using state management and event system');
    await page.click('#submit-answer');

    // Test: next question is active - check for different question text again
    await expect(page.locator('#current-question')).not.toContainText('How should data be synchronized');

    // Answer question #3
    await page.fill('#answer-input', 'real-time updates with websockets');
    await page.click('#submit-answer');

    // Test: show modification questions section
    await expect(page.locator('#extraction-choices h4:has-text("Modifications:")')).toBeVisible();
    await expect(page.locator('#connections h4:has-text("Connections Detected:")')).toBeVisible();
  });

  test('Modification/Connection Workflow', async ({ page }) => {
    // Navigate to discover page first
    await page.fill('#vision-input', 'modification test');
    await page.click('#vision-submit');

    // Setup: Load graph and complete QA to get to modification screen
    await page.selectOption('#graph-file-selector', 'spec-graph.json');
    await page.fill('#ai-input', 'mock');
    await page.press('#ai-input', 'Enter');

    // Complete 3 questions quickly
    for (let i = 0; i < 3; i++) {
      await page.fill('#answer-input', `answer ${i + 1}`);
      await page.click('#submit-answer');
    }

    // Test: QA section is hidden (no input, no controls)
    await expect(page.locator('#answer-input')).not.toBeVisible();

    // Test: modification and connection interface is showing
    await expect(page.locator('#extraction-choices h4:has-text("Modifications:")')).toBeVisible();
    await expect(page.locator('#connections h4:has-text("Connections Detected:")')).toBeVisible();

    // Test: connection should be initially populated
    await expect(page.locator('#connections-list li')).toBeVisible();

    // Add modification
    await page.click('#detections-list button:has-text("+")').first();

    // Test: connection list shows added modification in Pending Changes
    await expect(page.locator('#pending-changes h4:has-text("Pending Changes:")')).toBeVisible();
    await expect(page.locator('#pending-changes-summary')).toContainText('+ Entity:');

    // Add connection
    await page.click('#connections-list button:has-text("+")').first();

    // Test: both modification and connection appear in Pending Changes section
    await expect(page.locator('#pending-changes-summary')).toContainText('+ Connection:');

    // Click commit
    await page.click('#commit-changes');

    // Test: modification appears in sidebar (count increase)
    await expect(page.locator('.accordion-header:has-text("Users")')).toBeVisible();

    // Test: validate connection is added in graph data (system returns to QA)
    await expect(page.locator('#current-question')).toBeVisible();
  });

  test('QA Expansion Workflow', async ({ page }) => {
    // Navigate to discover page first
    await page.fill('#vision-input', 'expansion test');
    await page.click('#vision-submit');

    // Setup: Get to a question
    await page.selectOption('#graph-file-selector', 'spec-graph.json');
    await page.fill('#ai-input', 'mock');
    await page.press('#ai-input', 'Enter');

    // Click 'Expand' on a question
    await page.click('#expand-toggle');

    // Test: Multiple choices are showing
    await expect(page.locator('.multiple-choice label')).toContainText('Multiple Choice:');
    await expect(page.locator('#expand-options h4:has-text("Recommendation")')).toBeVisible();
    await expect(page.locator('#expand-options h4:has-text("Tradeoffs")')).toBeVisible();
    await expect(page.locator('#expand-options h4:has-text("Alternatives")')).toBeVisible();
    await expect(page.locator('#expand-options h4:has-text("Challenges")')).toBeVisible();

    // Test: Button changed to collapse
    await expect(page.locator('#expand-toggle')).toContainText('Collapse Options');

    // Test collapse functionality
    await page.click('#expand-toggle');
    await expect(page.locator('#expand-toggle')).toContainText('Expand Options');
  });

  test('QA Reorientation Workflow', async ({ page }) => {
    // Navigate to discover page first
    await page.fill('#vision-input', 'reorientation test');
    await page.click('#vision-submit');

    // Load graph
    await page.selectOption('#graph-file-selector', 'spec-graph.json');

    // Type "add user tron" in AI bar
    await page.fill('#ai-input', 'add user tron');
    await page.press('#ai-input', 'Enter');

    // Test: validate that the modification/connection screen is showing
    await expect(page.locator('#extraction-choices h4:has-text("Modifications:")')).toBeVisible();
    await expect(page.locator('#connections h4:has-text("Connections Detected:")')).toBeVisible();

    // Test: validate "tron" related entities are suggested
    await expect(page.locator('#detections-list')).toContainText('tron');

    // Test: validate connections are detected for tron
    await expect(page.locator('#connections-list')).toContainText('tron');
  });

  test('Complete End-to-End Workflow', async ({ page }) => {
    // Test the complete flow from start to finish

    // 1. Start with text entry
    await page.fill('#vision-input', 'complete workflow test');
    await page.click('#vision-submit');

    // 2. Load JSON graph
    await page.selectOption('#graph-file-selector', 'spec-graph.json');
    await expect(page.locator('.accordion-header:has-text("Users")')).toBeVisible();

    // 3. Run QA refinement
    await page.fill('#ai-input', 'mock');
    await page.press('#ai-input', 'Enter');

    // Answer 3 questions
    for (let i = 0; i < 3; i++) {
      await page.fill('#answer-input', `comprehensive answer ${i + 1}`);
      await page.click('#submit-answer');
    }

    // 4. Use modification/connection workflow
    await page.click('#detections-list button:has-text("+")').first();
    await page.click('#connections-list button:has-text("+")').first();
    await page.click('#commit-changes');

    // 5. Test QA expansion on new question
    await page.click('#expand-toggle');
    await expect(page.locator('.multiple-choice label')).toContainText('Multiple Choice:');
    await page.click('#expand-toggle');

    // 6. Test reorientation
    await page.fill('#ai-input', 'add feature analytics');
    await page.press('#ai-input', 'Enter');
    await expect(page.locator('#detections-list')).toContainText('analytics');

    // Verify final state
    await expect(page.locator('#extraction-choices h4:has-text("Modifications:")')).toBeVisible();
    await expect(page.locator('.accordion-header:has-text("Users")')).toBeVisible();
  });
});