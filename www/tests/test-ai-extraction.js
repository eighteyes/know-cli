#!/usr/bin/env node

// Test script to demonstrate AI entity extraction
// Run with: ANTHROPIC_API_KEY=your-key node test-ai-extraction.js

const Anthropic = require('@anthropic-ai/sdk');

// Example of how the extraction works
async function testExtraction(apiKey) {
  const anthropic = new Anthropic({
    apiKey: apiKey,
  });

  const testAnswer = "We need real-time telemetry for monitoring robot positions, fleet tracking to manage multiple robots, and predictive maintenance to prevent failures. The system should also include a map visualization component and alert management service.";

  const testQuestion = {
    text: "What are the main features your system needs to provide?",
    type: "feature"
  };

  console.log("\n🧪 Testing AI Entity Extraction");
  console.log("================================\n");
  console.log("Question:", testQuestion.text);
  console.log("Answer:", testAnswer);
  console.log("\nExtracting entities...\n");

  try {
    const prompt = `You are a knowledge graph expert helping to extract entities from user answers.

Current context:
- Question: ${testQuestion.text}
- Question type: ${testQuestion.type}

User's answer: "${testAnswer}"

Extract entities from the answer and return them as a JSON array. Each entity should have:
- type: one of (feature, component, interface, requirement, user, objective, action, platform)
- id: a snake_case identifier
- name: human-readable name
- description: brief description of what it does
- dependencies: array of entity references this depends on (format: "type:id")

Focus on concrete entities mentioned in the answer. Don't invent entities not mentioned.

Return ONLY valid JSON array, no explanation:`;

    const message = await anthropic.messages.create({
      model: 'claude-3-haiku-20240307',
      max_tokens: 1000,
      temperature: 0.3,
      messages: [{
        role: 'user',
        content: prompt
      }]
    });

    const content = message.content[0].text;
    console.log("Raw AI Response:");
    console.log(content);

    const jsonMatch = content.match(/\[[\s\S]*\]/);
    if (jsonMatch) {
      const entities = JSON.parse(jsonMatch[0]);
      console.log("\n✅ Extracted Entities:");
      console.log(JSON.stringify(entities, null, 2));
      return entities;
    }
  } catch (error) {
    console.error("❌ Error:", error.message);
  }
}

// Check if API key is provided
if (process.env.ANTHROPIC_API_KEY) {
  console.log("✅ API Key found");
  testExtraction(process.env.ANTHROPIC_API_KEY);
} else {
  console.log(`
⚠️  No API key found!

To test AI entity extraction:
1. Get your API key from https://console.anthropic.com/
2. Run: ANTHROPIC_API_KEY=your-key node test-ai-extraction.js

Or set it permanently:
export ANTHROPIC_API_KEY=your-key

The webapp will automatically use AI extraction when the key is available.
`);
}