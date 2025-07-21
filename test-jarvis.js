#!/usr/bin/env node
/**
 * Jarvis Test Script
 * Test the Jarvis orchestration agent responses
 */

import fetch from 'node-fetch';
import readline from 'readline';

const API_URL = 'http://localhost:3010/api';

// Create readline interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Test queries
const testQueries = [
  "Jarvis?",
  "Hey Jarvis",
  "jarvis",
  "Are you there Jarvis?",
  "Is Jarvis online?",
  "Hello", // Should not trigger Jarvis
  "What's your status?", // Should not trigger Jarvis
];

async function testJarvisEndpoint() {
  console.log('\n🤖 Testing Jarvis Direct Endpoint...\n');
  
  try {
    const response = await fetch(`${API_URL}/jarvis`);
    const data = await response.json();
    
    console.log('Response:', data.message);
    console.log('Status:', data.status);
    console.log('Agent:', data.agent);
    if (data.details) {
      console.log('Details:', JSON.stringify(data.details, null, 2));
    }
  } catch (error) {
    console.error('Error:', error.message);
  }
}

async function testJarvisQuery(message) {
  try {
    const response = await fetch(`${API_URL}/jarvis/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
    });
    
    const data = await response.json();
    
    if (data.isJarvisQuery) {
      console.log(`\n✅ "${message}" - Jarvis responds:`);
      console.log(`   ${data.response.message}`);
    } else {
      console.log(`\n❌ "${message}" - Not a Jarvis query`);
    }
  } catch (error) {
    console.error(`Error testing "${message}":`, error.message);
  }
}

async function testJarvisCommand(command) {
  console.log(`\n📝 Sending command: "${command}"`);
  
  try {
    const response = await fetch(`${API_URL}/jarvis/command`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ command })
    });
    
    const data = await response.json();
    console.log('Response:', data);
  } catch (error) {
    console.error('Error:', error.message);
  }
}

async function interactiveMode() {
  console.log('\n💬 Interactive Mode - Type messages to test Jarvis recognition');
  console.log('   Type "exit" to quit\n');
  
  const askQuestion = () => {
    rl.question('You: ', async (input) => {
      if (input.toLowerCase() === 'exit') {
        rl.close();
        return;
      }
      
      await testJarvisQuery(input);
      askQuestion();
    });
  };
  
  askQuestion();
}

async function main() {
  console.log('===========================================');
  console.log('       JARVIS ORCHESTRATION AGENT TEST     ');
  console.log('===========================================');
  
  // Test direct endpoint
  await testJarvisEndpoint();
  
  // Test various queries
  console.log('\n🧪 Testing Query Recognition...');
  for (const query of testQueries) {
    await testJarvisQuery(query);
  }
  
  // Test commands
  console.log('\n🎯 Testing Commands...');
  await testJarvisCommand('status');
  await testJarvisCommand('help');
  
  // Interactive mode
  await interactiveMode();
}

// Check if server is running
fetch(`${API_URL}/health`)
  .then(() => {
    console.log('✅ Server is running\n');
    main();
  })
  .catch(() => {
    console.error('❌ Server is not running. Please start the dashboard server first.');
    console.error('   Run: cd agent-dashboard && npm start');
    process.exit(1);
  });