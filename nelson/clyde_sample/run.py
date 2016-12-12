import subprocess as sp
import os
import unittest
import json

class MyResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super(MyResult, self).__init__(stream, descriptions, verbosity)
        self._successes = []

    def addSuccess(self, test):
        self._successes.append(test)
        super(MyResult, self).addSuccess(test)

    def tests(self):
        return self.errors + self.failures + [(x,"") for x in self._successes]

def points_available(npoints):
    def points_available_decorator(func):
        def func_wrapper(self):
            try:
                self.result['points_available'] = npoints
                self.result['points_awarded'] = None
            except:
                self.result = {'points_available' : npoints, 'points_awarded': None}

            ans = func(self)

            if self.result['points_awarded'] is None:
                self.result['points_awarded'] = npoints

            return ans

        func_wrapper.__doc__ = func.__doc__

        return func_wrapper

    return points_available_decorator

class HWTest(unittest.TestCase):
  def setUp(self):
    self.result = {}

  def tearDown(self):
    try:
      os.unlink('./helloworld')
    except:
      pass 

class HWCompilationTest(HWTest):

  @points_available(5)
  def test_compiles(self):
    """Tests that the code compiles cleanly"""
    returncode = sp.call(['gcc', '-o', 'helloworld', 'main.c', 'helloworld.c'])
    self.assertEqual(returncode, 0, "Your code did not compile cleanly.")

class HWExecutionTest(HWTest):

  def setUp(self):
    super(HWExecutionTest, self).setUp()
    sp.call(['gcc', '-o', 'helloworld', 'main.c', 'helloworld.c'])

  @points_available(5)
  def test_print_hello_world(self):
    """Tests that the code prints "Hello World!" """
    with open(os.path.join("helloworld_stdout.txt"), "wb") as fd:
      sp.call(['./helloworld'], stdout=fd)

    with open(os.path.join("helloworld_stdout.txt"), "r") as fd:
      output = fd.read()

    self.assertEqual(output.rstrip() , "Hello World!")

def main():
    cwd = os.getcwd()

    os.chdir('workspace')

    compilation_test_suite = unittest.TestLoader().loadTestsFromTestCase(HWCompilationTest)
    execution_test_suite = unittest.TestLoader().loadTestsFromTestCase(HWExecutionTest)

    test_result = unittest.TextTestRunner(resultclass=MyResult).run(unittest.TestSuite([compilation_test_suite, execution_test_suite]))
    all_tests = test_result.tests()

    data = {'total_points_available': sum( (x[0].result.get('points_available') or 0) for x in all_tests),
            'total_points_awarded': sum( (x[0].result.get('points_awarded') or 0) for x in all_tests),
            'tests': [{"description": x[0].shortDescription(), 
                       "traceback": x[1],
                       "output": x[0].result} for x in all_tests]}

    with open("grade.json", "w") as fd:
        json.dump(data, fd) 

    os.chdir(cwd)

if __name__ == '__main__':
  main()
