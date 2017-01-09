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

ArgSet = namedtuple('ArgSet',['action', 'object', 'data_file', 'environment', 'id_provider', 'jwt_path'])

class TestDeveloper(unittest.TestCase):
  def setUp(self):
    self.tmp_path = tempfile.mkdtemp()
    self.cwd = os.getcwd()
    os.chdir(self.tmp_path)

  def tearDown(self):
    os.chdir(self.cwd)
    shutil.rmtree(self.tmp_path) 

  def checkDeployKeyCreated(self):
    self.assertTrue(os.path.isfile('deploy_key/deploy_id_rsa'))

  def checkFilesCreated(self, name):
    self.assertTrue(os.path.isfile(os.path.join('app', name, 'grade.py')))
    self.assertTrue(os.path.isfile(os.path.join('app', name, 'run.py')))
    self.assertTrue(os.path.isfile(os.path.join('app', name, 'workspace', 'main.c')))
    self.assertTrue(os.path.isfile(os.path.join('app', name, 'workspace', 'helloworld.c')))
    self.assertTrue(os.path.isfile(os.path.join('app', name, 'workspace', '.gitignore')))


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
    self.assertEqual(str(cm.exception), expected_error_message)


    mock_sp.check_output.return_value = "fatal: Not a git repository (or any of the parent directories): .git"
    with self.assertRaises(RuntimeError) as cm:
      nelson.developer.infer_git_url('fake')
    self.assertEqual(str(cm.exception), expected_error_message)

class TestCourseHelper(TestDeveloper):

  @mock.patch('nelson.developer.build_gtomscs_session')
  def test_course_can_be_created(self, mock_build_session):
    """A course can be created with the correct parameters"""

    course = {
      'gtcode': 'csXXXX',
      'title': 'An Example Course',
      'git_url': 'git@github.com:udacity/nelson.git'
    }

    data = { 'course': course }

    with open("course.json", "w") as fd:
      json.dump(data, fd)

    with requests_mock.Mocker() as m:
      m.post(nelson.gtomscs.root_url('production') + "/courses", text=json.dumps({}))

      mock_build_session.return_value = requests.Session()

      args = ArgSet(action='create',
                    object='course', 
                    data_file='course.json', 
                    environment='production', 
                    id_provider = 'gt', 
                    jwt_path='./jwt')

      nelson.developer.main(args)

      sent_data = m.request_history[0].json()
      sent_data = sent_data['course']

      course = data['course']

      for k in course:
        self.assertEqual(sent_data[k], course[k])
      self.assertEqual(sent_data['deploy_key'], nelson.developer.read_deploy_key())

    self.checkDeployKeyCreated()

class TestNanodegreeHelper(TestDeveloper):

  @mock.patch('nelson.developer.build_udacity_session')
  def test_nanodegree_can_be_created(self, mock_build_session):
    """A nanodegree can be created with the correct parameters"""

    nanodegree = {
        'ndkey': 'nd123',
        'name': 'Test Nanodegree',
        'git_url': 'git@github.com:udacity/nelson.git'
      }

    data = { 'nanodegree': nanodegree }

    with open("nanodegree.json", "w") as fd:
      json.dump(data, fd)

    with requests_mock.Mocker() as m:
      m.post(nelson.udacity.root_url('production') + "/nanodegrees", text=json.dumps({}))

      mock_build_session.return_value = requests.Session()

      args = ArgSet(action='create',
                    object='nanodegree',
                    data_file='nanodegree.json',
                    environment='production',
                    id_provider = 'udacity',
                    jwt_path='./jwt')

      nelson.developer.main(args)

      sent_data = m.request_history[0].json()
      sent_data = sent_data['nanodegree']

      for k in nanodegree:
        self.assertEqual(sent_data[k], nanodegree[k])

      self.assertEqual(sent_data['deploy_key'], nelson.developer.read_deploy_key())

    self.checkDeployKeyCreated()

class TestQuizHelper(TestDeveloper):

  @mock.patch('nelson.developer.build_gtomscs_session')
  def test_quiz_can_be_created(self, mock_build_session):
    """A quiz can be created with the correct parameters"""

    quiz = {
      'name': 'helloworld',
      'executor': 'docker',
      'docker_image': 'gtomscs/default',
      'timeout': 30
    }

    data = {'gtcode': 'csXXXX', 'quiz': quiz}

    with open("quiz.json", "w") as fd:
      json.dump(data, fd)

    with requests_mock.Mocker() as m:
      m.post("%s/courses/%s/quizzes" % (nelson.gtomscs.root_url('production'), data['gtcode']), text=json.dumps({}))

      mock_build_session.return_value = requests.Session()

      args = ArgSet(action='create',
                    object='quiz',
                    data_file='quiz.json',
                    environment='production',
                    id_provider = 'gt',
                    jwt_path='./jwt')

      nelson.developer.main(args)

      sent_data = m.request_history[0].json()
      sent_data = sent_data['quiz']

      for k in quiz:
        self.assertEqual(sent_data[k], quiz[k])

    self.checkFilesCreated(quiz['name'])

class TestProjectHelper(TestDeveloper):

  @mock.patch('nelson.developer.build_udacity_session')
  def test_project_can_be_created(self, mock_build_session):
    """A project can be created with the correct parameters"""

    project = {      
      'name': 'helloworld',
      'udacity_key': '123456789',
      'executor': 'docker',
      'docker_image': 'gtomscs/default',
      'timeout': 30
    }

    data = {'ndkey': 'csXXXX', 'project': project}

    with open("project.json", "w") as fd:
      json.dump(data, fd)

    with requests_mock.Mocker() as m:
      m.post("%s/nanodegrees/%s/projects" % (nelson.udacity.root_url('production'), data['ndkey']), text=json.dumps({}))

      mock_build_session.return_value = requests.Session()

      args = ArgSet(action='create',
                    object='project',
                    data_file='project.json',
                    environment='production',
                    id_provider = 'udacity',
                    jwt_path='./jwt')

      nelson.developer.main(args)

      sent_data = m.request_history[0].json()
      sent_data = sent_data['project']

      for k in project:
        self.assertEqual(sent_data[k], project[k])

    self.checkFilesCreated(project['name'])

if __name__ == '__main__':
    unittest.main()


