#!/usr/bin/env node

/**
 * End-to-End Test Runner
 * Executes all end-to-end integration tests and provides comprehensive reporting
 */

import { execSync } from 'child_process';
import { existsSync } from 'fs';
import { join } from 'path';

interface TestSuite {
  name: string;
  file: string;
  description: string;
  requirements: string[];
}

interface TestResult {
  suite: string;
  passed: number;
  failed: number;
  total: number;
  duration: number;
  status: 'PASS' | 'FAIL';
  errors?: string[];
}

class E2ETestRunner {
  private testSuites: TestSuite[] = [
    {
      name: 'Core User Journeys',
      file: 'core-user-journeys.test.ts',
      description: 'Tests complete workflows from patient consent setting to research query processing',
      requirements: ['9.1', '9.4']
    },
    {
      name: 'Chat Protocol Integration',
      file: 'chat-protocol-integration.test.ts',
      description: 'Tests natural language interactions and ASI:One compatibility',
      requirements: ['6.1', '6.2', '6.3', '6.4']
    },
    {
      name: 'Agentverse Compliance',
      file: 'agentverse-compliance.test.ts',
      description: 'Tests ASI Alliance technology integration and compliance',
      requirements: ['9.2', '9.3']
    }
  ];

  async runAllTests(): Promise<void> {
    console.log('🚀 Starting End-to-End Integration Tests');
    console.log('=' .repeat(60));
    
    const results: TestResult[] = [];
    let totalPassed = 0;
    let totalFailed = 0;
    let totalTests = 0;

    for (const suite of this.testSuites) {
      console.log(`\n📋 Running: ${suite.name}`);
      console.log(`📄 Description: ${suite.description}`);
      console.log(`📋 Requirements: ${suite.requirements.join(', ')}`);
      console.log('-'.repeat(40));

      const result = await this.runTestSuite(suite);
      results.push(result);
      
      totalPassed += result.passed;
      totalFailed += result.failed;
      totalTests += result.total;

      this.printSuiteResult(result);
    }

    this.printSummary(results, totalPassed, totalFailed, totalTests);
  }

  private async runTestSuite(suite: TestSuite): Promise<TestResult> {
    const startTime = Date.now();
    
    try {
      const testPath = join(__dirname, suite.file);
      
      if (!existsSync(testPath)) {
        return {
          suite: suite.name,
          passed: 0,
          failed: 1,
          total: 1,
          duration: 0,
          status: 'FAIL',
          errors: [`Test file not found: ${suite.file}`]
        };
      }

      // Run the specific test file
      const output = execSync(
        `npx jest "${testPath}" --verbose --no-coverage --silent`,
        { 
          encoding: 'utf8',
          cwd: process.cwd(),
          timeout: 60000 // 60 second timeout
        }
      );

      const duration = Date.now() - startTime;
      const { passed, failed, total } = this.parseJestOutput(output);

      return {
        suite: suite.name,
        passed,
        failed,
        total,
        duration,
        status: failed === 0 ? 'PASS' : 'FAIL'
      };

    } catch (error: any) {
      const duration = Date.now() - startTime;
      const { passed, failed, total } = this.parseJestOutput(error.stdout || '');
      
      return {
        suite: suite.name,
        passed,
        failed: failed || 1,
        total: total || 1,
        duration,
        status: 'FAIL',
        errors: [error.message]
      };
    }
  }

  private parseJestOutput(output: string): { passed: number; failed: number; total: number } {
    // Parse Jest output to extract test results
    const passMatch = output.match(/(\d+) passed/);
    const failMatch = output.match(/(\d+) failed/);
    const totalMatch = output.match(/Tests:\s+.*?(\d+) total/);

    const passed = passMatch ? parseInt(passMatch[1]) : 0;
    const failed = failMatch ? parseInt(failMatch[1]) : 0;
    const total = totalMatch ? parseInt(totalMatch[1]) : passed + failed;

    return { passed, failed, total };
  }

  private printSuiteResult(result: TestResult): void {
    const status = result.status === 'PASS' ? '✅ PASS' : '❌ FAIL';
    const duration = (result.duration / 1000).toFixed(2);
    
    console.log(`${status} ${result.suite}`);
    console.log(`   Tests: ${result.passed} passed, ${result.failed} failed, ${result.total} total`);
    console.log(`   Duration: ${duration}s`);
    
    if (result.errors && result.errors.length > 0) {
      console.log('   Errors:');
      result.errors.forEach(error => {
        console.log(`     - ${error}`);
      });
    }
  }

  private printSummary(results: TestResult[], totalPassed: number, totalFailed: number, totalTests: number): void {
    console.log('\n' + '='.repeat(60));
    console.log('📊 END-TO-END TEST SUMMARY');
    console.log('='.repeat(60));

    const overallStatus = totalFailed === 0 ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED';
    console.log(`\n${overallStatus}`);
    console.log(`\nOverall Results:`);
    console.log(`  ✅ Passed: ${totalPassed}`);
    console.log(`  ❌ Failed: ${totalFailed}`);
    console.log(`  📊 Total:  ${totalTests}`);
    console.log(`  📈 Success Rate: ${((totalPassed / totalTests) * 100).toFixed(1)}%`);

    console.log('\nTest Suite Breakdown:');
    results.forEach(result => {
      const status = result.status === 'PASS' ? '✅' : '❌';
      const successRate = result.total > 0 ? ((result.passed / result.total) * 100).toFixed(1) : '0.0';
      console.log(`  ${status} ${result.suite}: ${result.passed}/${result.total} (${successRate}%)`);
    });

    console.log('\nRequirement Coverage:');
    const allRequirements = [...new Set(this.testSuites.flatMap(s => s.requirements))];
    allRequirements.forEach(req => {
      const suitesForReq = this.testSuites.filter(s => s.requirements.includes(req));
      const passedSuites = suitesForReq.filter(s => {
        const result = results.find(r => r.suite === s.name);
        return result?.status === 'PASS';
      });
      
      const status = passedSuites.length === suitesForReq.length ? '✅' : '❌';
      console.log(`  ${status} Requirement ${req}: ${passedSuites.length}/${suitesForReq.length} test suites passed`);
    });

    if (totalFailed === 0) {
      console.log('\n🎉 All end-to-end integration tests are passing!');
      console.log('✅ Task 14: Create end-to-end integration tests - COMPLETED');
      console.log('\nThe system is ready for:');
      console.log('  - Patient consent workflows');
      console.log('  - Research query processing');
      console.log('  - Chat Protocol integration');
      console.log('  - ASI Alliance compliance');
      console.log('  - Multi-agent coordination');
      console.log('  - Performance under load');
    } else {
      console.log('\n⚠️  Some tests are failing. Please review the errors above.');
      console.log('🔧 Fix the failing tests before proceeding to deployment.');
    }

    console.log('\n' + '='.repeat(60));
  }
}

// Run the tests if this file is executed directly
if (require.main === module) {
  const runner = new E2ETestRunner();
  runner.runAllTests().catch(error => {
    console.error('❌ Test runner failed:', error);
    process.exit(1);
  });
}

export { E2ETestRunner };