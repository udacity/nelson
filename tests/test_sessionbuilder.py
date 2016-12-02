import unittest
import os
import sys
import errno
import requests
import requests_mock
import nelson
import zipfile
import json

from nelson.sessionbuilder import SessionBuilder, udacity_login, gt_login

class TestSessionBuilder(unittest.TestCase):

  def create_jwt(self):
    jwt_obj = {'udacity': os.environ.get('BONNIE_TEST_JWT')}
    jwt_path = os.path.join('.test_nelson','gtomscs_jwt')


    try:
      os.makedirs(os.path.dirname(jwt_path))
    except OSError as exception:
      if exception.errno != errno.EEXIST:
        raise

    with open(jwt_path, 'w') as fd:
      json.dump(jwt_obj,fd)    

    return jwt_path

  @unittest.skipIf(os.environ.get('BONNIE_TEST_JWT') is None,
    "No bonnie specified.")
  def test_loads_jwt_from_file(self):
    jwt_path = self.create_jwt()

    session = SessionBuilder('https://bonnie.udacity.com', 'udacity', jwt_path).new()

    self.assertEqual(session.headers['authorization'], 'Bearer ' + os.environ.get('BONNIE_TEST_JWT'))

    try:
      os.unlink(jwt_path)
    except:
      pass

  @unittest.skipIf(os.environ.get('UDACITY_TEST_EMAIL') is None or os.environ.get('UDACITY_TEST_PASSWORD') is None,
    "No udacity credentials specified.")
  def test_build_udacity_session(self):
    session = requests.Session()
    udacity_login(session, 
                  'https://bonnie.udacity.com', 
                  os.environ['UDACITY_TEST_EMAIL'],
                  os.environ['UDACITY_TEST_PASSWORD'])

  @unittest.skipIf(os.environ.get('GT_TEST_USERNAME') is None or os.environ.get('GT_TEST_PASSWORD') is None,
    "No gt credentials specified.")
  def test_gt_login(self):
    session = requests.Session()
    gt_login(session, 
            'https://bonnie.udacity.com', 
            os.environ['GT_TEST_USERNAME'],
            os.environ['GT_TEST_PASSWORD'])

if __name__ == '__main__':
    unittest.main()


