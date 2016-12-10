import mock
import unittest
import os
import sys
import shutil
import tempfile
import requests
import requests_mock
import json
from collections import namedtuple

import nelson.developer
import nelson.gtomscs
import nelson.udacity

ArgSet = namedtuple('ArgSet',['object', 'data_file', 'environment', 'id_provider', 'jwt_path'])

class TestDeveloper(unittest.TestCase):
  def setUp(self):
    self.tmp_path = tempfile.mkdtemp()
    self.cwd = os.getcwd()
    os.chdir(self.tmp_path)

  def tearDown(self):
    os.chdir(self.cwd)
    shutil.rmtree(self.tmp_path) 

class TestHelperMethods(TestDeveloper):

  @mock.patch('nelson.developer.sp')
  def test_infer_git_url(self, mock_sp):
    ssh_remote = 'git@github.com:udacity/ssh.git'
    http_remote = 'https://github.com/udacity/http.git'

    mock_sp.check_output.return_value = "origin  %s (fetch)\norigin  %s (push)\nupstream  %s (fetch)\nupstream  %s (push)" \
                                  % (ssh_remote, ssh_remote, http_remote, http_remote)

    self.assertEqual(ssh_remote, nelson.developer.infer_git_url('origin'))
    self.assertEqual('git@github.com:udacity/http.git', nelson.developer.infer_git_url('upstream'))

    expected_error_message = "Unable to infer git_url.  Please set the parameter in the config file."

    with self.assertRaises(RuntimeError) as cm:
      nelson.developer.infer_git_url('fake')
    the_exception = cm.exception
    self.assertEqual(the_exception.message, expected_error_message)


    mock_sp.check_output.return_value = "fatal: Not a git repository (or any of the parent directories): .git"
    with self.assertRaises(RuntimeError) as cm:
      nelson.developer.infer_git_url('fake')
    the_exception = cm.exception
    self.assertEqual(the_exception.message, expected_error_message)

class TestCourseHelper(TestDeveloper):

  def checkDeployKeyCreated(self):
    self.assertTrue(os.path.isfile('deploy_key/deploy_id_rsa'))

  @mock.patch('nelson.developer.build_gtomscs_session')
  def test_course_can_be_created(self, mock_build_session):
    """A course can be created with the correct parameters"""

    data = {
      'gtcode': 'csXXXX',
      'title': 'An Example Course',
      'git_url': 'git@github.com:udacity/nelson.git'
    }

    with open("course.json", "w") as fd:
      json.dump(data, fd)

    with requests_mock.Mocker() as m:
      m.post(nelson.gtomscs.root_url('production') + "/courses/", text=json.dumps({}))

      mock_build_session.return_value = requests.Session()

      args = ArgSet(object='course', data_file='course.json', environment='production', id_provider = 'gt', jwt_path='./jwt')

      nelson.developer.main(args)

      sent_data = m.request_history[0].json()
      sent_data = sent_data['course']

      self.assertEqual(sent_data['gtcode'], data['gtcode'])
      self.assertEqual(sent_data['title'], data['title'])
      self.assertEqual(sent_data['git_url'], data['git_url'])
      self.assertEqual(sent_data['deploy_key'], nelson.developer.read_deploy_key())

    self.checkDeployKeyCreated()

class TestNanodegreeHelper(TestDeveloper):

  def checkDeployKeyCreated(self):
    self.assertTrue(os.path.isfile('deploy_key/deploy_id_rsa'))

  @mock.patch('nelson.developer.build_udacity_session')
  def test_nanodegree_can_be_created(self, mock_build_session):
    """A nanodegree can be created with the correct parameters"""

    data = {
      'ndkey': 'nd123',
      'name': 'Test Nanodegree',
      'git_url': 'git@github.com:udacity/nelson.git'
    }

    with open("nanodegree.json", "w") as fd:
      json.dump(data, fd)

    with requests_mock.Mocker() as m:
      m.post(nelson.udacity.root_url('production') + "/nanodegrees/", text=json.dumps({}))

      mock_build_session.return_value = requests.Session()

      args = ArgSet(object='nanodegree', data_file='nanodegree.json', environment='production', id_provider = 'udacity', jwt_path='./jwt')

      nelson.developer.main(args)

      sent_data = m.request_history[0].json()
      sent_data = sent_data['nanodegree']

      for k in data:
        self.assertEqual(sent_data[k], data[k])

      self.assertEqual(sent_data['deploy_key'], nelson.developer.read_deploy_key())

    self.checkDeployKeyCreated()

class TestQuizHelper(TestDeveloper):

  def checkFilesCreated(self):
    self.assertTrue(os.path.isfile(os.path.join('app', self.data['name'], 'grade.py')))
    self.assertTrue(os.path.isfile(os.path.join('app', self.data['name'], 'run.py')))
    self.assertTrue(os.path.isfile(os.path.join('app', self.data['name'], 'workspace', 'main.c')))

  @mock.patch('nelson.developer.build_gtomscs_session')
  def test_quiz_can_be_created(self, mock_build_session):
    """A quiz can be created with the correct parameters"""

    self.data = {
      'gtcode': 'csXXXX',
      'name': 'helloworld',
      'executor': 'docker',
      'docker_image': 'gtomscs/default'
    }

    with open("quiz.json", "w") as fd:
      json.dump(self.data, fd)

    with requests_mock.Mocker() as m:
      m.post("%s/courses/%s/quizzes" % (nelson.gtomscs.root_url('production'), self.data['gtcode']), text=json.dumps({}))

      mock_build_session.return_value = requests.Session()

      args = ArgSet(object='quiz', data_file='quiz.json', environment='production', id_provider = 'gt', jwt_path='./jwt')

      nelson.developer.main(args)

      sent_data = m.request_history[0].json()
      sent_data = sent_data['quiz']

      for k in self.data:
        self.assertEqual(sent_data[k], self.data[k])

    self.checkFilesCreated()

class TestProjectHelper(TestDeveloper):

  def checkFilesCreated(self):
    self.assertTrue(os.path.isfile(os.path.join('app', self.data['name'], 'grade.py')))
    self.assertTrue(os.path.isfile(os.path.join('app', self.data['name'], 'run.py')))
    self.assertTrue(os.path.isfile(os.path.join('app', self.data['name'], 'workspace', 'main.c')))

  @mock.patch('nelson.developer.build_udacity_session')
  def test_project_can_be_created(self, mock_build_session):
    """A project can be created with the correct parameters"""

    self.data = {
      'ndkey': 'csXXXX',
      'name': 'helloworld',
      'executor': 'docker',
      'docker_image': 'gtomscs/default'
    }

    with open("project.json", "w") as fd:
      json.dump(self.data, fd)

    with requests_mock.Mocker() as m:
      m.post("%s/nanodegrees/%s/projects" % (nelson.udacity.root_url('production'), self.data['ndkey']), text=json.dumps({}))

      mock_build_session.return_value = requests.Session()

      args = ArgSet(object='project', data_file='project.json', environment='production', id_provider = 'udacity', jwt_path='./jwt')

      nelson.developer.main(args)

      sent_data = m.request_history[0].json()
      sent_data = sent_data['project']

      for k in self.data:
        self.assertEqual(sent_data[k], self.data[k])

    self.checkFilesCreated()

if __name__ == '__main__':
    unittest.main()


