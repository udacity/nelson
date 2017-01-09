import unittest
import os
import sys
import errno
import requests
import requests_mock
import nelson
import zipfile
import json

from nelson.gtomscs import Submission

class TestGTOMSCS(unittest.TestCase):

  def setUp(self):
    pass

  def tearDown(self):
    try:
      os.unlink('student.zip')
    except:
      pass

  def create_randomfiles(self, filenames, nbytes):
    for f in filenames:
      with open(f,"wb") as fd:
        fd.write(os.urandom(nbytes))

  def test_uploads_correctly(self):
    """Creates valid zipfile and uploads without errors"""
    filenames = ['student_file1.py', 'student_file2.py']

    self.create_randomfiles(filenames, 1 << 10)

    with requests_mock.Mocker() as m:
      m.post('https://bonnie.udacity.com/student/course/csXXXX/quiz/letsmakeadeal/submission',
             text=json.dumps({}))

      s = Submission('csXXXX', 'letsmakeadeal', requests.Session(), filenames, 
                      max_zip_size = 4 << 10,
                      environment = 'production').submit()

    with zipfile.ZipFile('student.zip', 'r') as z:
      z.testzip()
      self.assertEqual(sorted(z.namelist()), sorted(filenames))

    for f in filenames:
      os.unlink(f)

  def test_rejects_too_large(self):
    """Rejects zipfiles that are too large"""
    filenames = ['student_file1.py', 'student_file2.py']

    self.create_randomfiles(filenames, 1 << 10)

    max_zip_size = 1

    with self.assertRaises(ValueError) as cm:
      s = Submission('csXXXX', 'letsmakeadeal', requests.Session(), filenames, 
                      max_zip_size = max_zip_size,
                      environment = 'production').submit()

    self.assertEqual(str(cm.exception), "Your zipfile exceeded the limit of %d bytes" % max_zip_size)

    for f in filenames:
      os.unlink(f)

  def test_rejects_parent_path(self):
    """Rejects filenames that involve parents in path"""
    filenames = ['student_file1.py', './../student_file2.py']

    self.create_randomfiles(filenames, 1 << 10)


    with self.assertRaises(ValueError) as cm:
      s = Submission('csXXXX', 'letsmakeadeal', requests.Session(), filenames, 
                      max_zip_size = 8 << 20,
                      environment = 'production').submit()
    self.assertEqual(str(cm.exception), "Submitted files must in subdirectories of ./.")

    for f in filenames:
      os.unlink(f)

  def test_rejects_bad_path(self):
    """Simple submission creates valid zipfile and uploads without errors"""

    filenames = ['student_file1.py', '/tmp/student_file2.py']

    self.create_randomfiles(filenames, 1 << 10)


    with self.assertRaises(ValueError) as cm:
      s = Submission('csXXXX', 'letsmakeadeal', requests.Session(), filenames, 
                      max_zip_size = 8 << 20,
                      environment = 'production').submit()
    self.assertEqual(str(cm.exception), "Submitted files must in subdirectories of ./.")

    for f in filenames:
      os.unlink(f)

  def test_handles_unauthorized_submissions(self):
    """Handles unauthorized submissions with the appropriate message"""

    filenames = ['student_file1.py', 'student_file2.py']

    self.create_randomfiles(filenames, 1 << 10)

    environment = 'production'
    provider = 'udacity'
    max_zip_size = 8 << 20

    with requests_mock.Mocker() as m:
      m.post('https://bonnie.udacity.com/student/course/csXXXX/quiz/letsmakeadeal/submission',
             status_code = 403,
             text = json.dumps({}))

      with self.assertRaises(RuntimeError) as cm:
        s = Submission('csXXXX', 'letsmakeadeal', requests.Session(), filenames, 
                      max_zip_size = 8 << 20,
                      environment = 'production').submit()
    self.assertEqual(str(cm.exception), "You don't have access to this quiz.")

    for f in filenames:
      os.unlink(f)

  def test_handles_quota_violations(self):
    """Handles quota violations with the appropriate message"""

    filenames = ['student_file1.py', 'student_file2.py']

    self.create_randomfiles(filenames, 1 << 10)

    environment = 'production'
    provider = 'udacity'
    max_zip_size = 8 << 20

    with requests_mock.Mocker() as m:
      m.post('https://bonnie.udacity.com/student/course/csXXXX/quiz/letsmakeadeal/submission',
             status_code = 429,
             text = json.dumps({"message": "quota exceeded"}))

      with self.assertRaises(RuntimeError) as cm:
        s = Submission('csXXXX', 'letsmakeadeal', requests.Session(), filenames, 
                      max_zip_size = 8 << 20,
                      environment = 'production').submit()
    self.assertEqual(str(cm.exception), "quota exceeded")

    for f in filenames:
      os.unlink(f)

if __name__ == '__main__':
    unittest.main()


