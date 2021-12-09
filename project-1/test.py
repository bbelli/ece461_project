import os
import subprocess

import tests

if __name__ == '__main__':
    test_output = subprocess.Popen(['coverage', 'run', 'tests.py'], stdout=subprocess.PIPE)
    test_output.wait()

    coverage_output = subprocess.Popen(['coverage', 'report', '-m'], stdout=subprocess.PIPE)
    coverage_output.wait()

    test_results                  = test_output.stdout.readlines()[-1].decode('utf-8')
    tests_passed, tests_completed = test_results[:-1].split('/')

    coverage_results = coverage_output.stdout.readlines()[-1].decode('utf-8')
    coverage         = coverage_results.split()[-1]

    print(f"Total: {tests_completed}")
    print(f"Passed: {tests_passed}")
    print(f"Coverage: {coverage}%")
    print(f"{tests_passed}/{tests_completed} test cases passed. {coverage}% line coverage achieved.")

    # print()

    # for line in test_output.stdout.readlines():
        # print(line.decode('utf-8'))