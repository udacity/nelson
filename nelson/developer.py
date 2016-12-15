import os
import sys
import shutil
import stat
import argparse
import errno
import requests
import json
import subprocess as sp
from pkg_resources import Requirement, resource_filename
from .gtomscs import build_session as build_gtomscs_session
from .udacity import build_session as build_udacity_session

from .gtomscs import root_url as gtomscs_root_url
from .udacity import root_url as udacity_root_url

def safe_mkdirs(path):
  try:
    os.makedirs(path)
  except OSError as exception:
    if exception.errno != errno.EEXIST:
      raise

def create_deploy_key():
  if not os.path.isdir('deploy_key'):
    os.mkdir('deploy_key')
    os.chmod('deploy_key', stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
  
  if not os.path.isfile("deploy_key/deploy_id_rsa"):
    sp.check_call(["ssh-keygen", "-f", "deploy_key/deploy_id_rsa", "-t", "rsa", "-q", "-N", ""])
    return

  print "Deploy key already exists"

def read_deploy_key():
  with open('deploy_key/deploy_id_rsa', 'rb') as fd:
    ans = fd.read()
  return ans

def infer_git_url(remote):
  output = sp.check_output(['git', 'remote', '-v'])

  ans = None

  for line in output.splitlines():
    words = line.split()
    if words[0] == remote:
      if words[1].startswith('git@github.com:'):
        ans = words[1]
      elif words[1].startswith('https://github.com'):
        ans = 'git@github.com:' + words[1][19:]

  if ans == None:
    raise RuntimeError("Unable to infer git_url.  Please set the parameter in the config file.")

  if ans == 'git@github.com:udacity/clyde-starter':
    raise RuntimeError("You must create a new remote repository.")

  return ans

def create_files(name):
  src = os.path.dirname(resource_filename(Requirement.parse("nelson"),"/nelson/clyde_sample/run.py"))

  dst = os.path.join('app', name)

  try:
    if not os.path.isfile(dst):
      shutil.copytree(src, dst)
  except OSError as exception:
    if exception.errno != errno.EEXIST:
      raise
    else:
      print exception.message
  else:
    shutil.move(os.path.join(dst, 'workspace', '._gitignore'), os.path.join(dst, 'workspace', '.gitignore'))


class CDHelper(object):
  def __init__(self, args):
    self.action = args.action
    self.object = args.object
    self.data_file = args.data_file
    self.environment = args.environment
    self.id_provider = args.id_provider
    self.jwt_path = args.jwt_path

  def act(self):
    if self.action == 'get':
      return self.get()
    elif self.action == 'create':
      return self.create()
    elif self.action == 'update':
      return self.update()
    else:
      raise ValueError("Unknown action %s." % self.action)

  def load_data(self):
    with open(self.data_file, "r") as fd:
      data = json.load(fd)
    return data

  def check_params(self, data):

    if self.action == 'create':
      bad_params = self.find_missing_create_path_params(data)
    else:
      bad_params = self.find_missing_get_path_params(data)

    if len(bad_params) > 0:
      raise ValueError("The data file %s is missing required parameters %s at the top level." \
                        % (self.data_file, str(tuple(bad_params))))

    if self.action != 'get' and self.object not in data:
      raise ValueError("The data file %s is missing required parameters %s." \
                        % (self.data_file, self.object))      

    if self.action == 'create':
      bad_params = self.find_missing_params(data[self.object])
      if len(bad_params) > 0:
        raise ValueError("The data file %s is missing required parameters %s inside of %s" \
                          % (self.data_file, str(tuple(bad_params)), self.object))

      bad_params = self.find_disallowed_params(data[self.object])
      if len(bad_params) > 0:
        raise ValueError("The data file %s contains the following disallowed parameters %s" \
                         "inside of %s"
                          % (self.data_file, str(tuple(bad_params)), self.object))   

  def create(self):
    data = self.load_data()

    self.check_params(data)

    url = self.create_url(data)

    http = self.build_session()

    body = {self.object : data[self.object]}

    r = http.post(url, json = body)

    r.raise_for_status()

    return json.loads(r.text)

  def update(self):
    data = self.load_data()

    self.check_params(data)

    url = self.update_url(data)

    http = self.build_session()

    body = {self.object : data[self.object]}

    r = http.patch(url, json = body)

    r.raise_for_status()

    return json.loads(r.text)

  def get(self):
    data = self.load_data()

    self.check_params(data)

    url = self.update_url(data)

    http = self.build_session()
    r = http.get(url)

    r.raise_for_status()

    return r.json()

class CourseHelper(CDHelper):

  def __init__(self, args):
    super(CourseHelper, self).__init__(args)
    self.root_url = gtomscs_root_url(self.environment)

  def find_missing_get_path_params(self, data):
    return {'gtcode'} - frozenset(_ for _ in data)

  def find_missing_create_path_params(self, data):
    return {}

  def find_missing_params(self, data):
    return {'gtcode', 'title'} - frozenset(_ for _ in data)

  def find_disallowed_params(self, data):
    return frozenset(_ for _ in data) - {'gtcode', 'title', 'cd_group_id', 'git_url', 'deploy_key'}

  def build_session(self):
    return build_gtomscs_session(self.environment, self.id_provider, self.jwt_path)

  def create_url(self, data):
    return self.root_url + '/courses'

  def update_url(self, data):
    return self.root_url + '/courses/' + data['gtcode']

  def load_data(self):
    data = super(CourseHelper, self).load_data()
    if self.action == 'create' and 'course' in data:
      if 'git_url' not in data['course']:
        data['course']['git_url'] = infer_git_url('origin')
      data['course']['deploy_key'] = read_deploy_key()      

    return data

  def create(self):
    create_deploy_key()

    return super(CourseHelper, self).create()

  def update(self):
    raise NotImplementedError("Please visit %s to update your course." % self.root_url)

  def get(self):
    raise NotImplementedError("Please visit %s to see your course configuration." % self.root_url)

class NanodegreeHelper(CDHelper):

  def __init__(self, args):
    super(NanodegreeHelper, self).__init__(args)
    self.root_url = udacity_root_url(self.environment)

  def find_missing_get_path_params(self, data):
    return {'ndkey'} - frozenset(_ for _ in data)

  def find_missing_create_path_params(self, data):
    return {}

  def find_missing_params(self, data):
    return {'ndkey', 'name'} - frozenset(_ for _ in data)

  def find_disallowed_params(self, data):
    return frozenset(_ for _ in data) - {'ndkey', 'name', 'cd_group_id', 'git_url', 'deploy_key'}

  def build_session(self):
    return build_udacity_session(self.environment, self.id_provider, self.jwt_path)

  def create_url(self, data):
    return self.root_url + '/nanodegrees'

  def update_url(self, data):
    return self.root_url + '/nanodegrees/' + data['ndkey']

  def load_data(self):
    data = super(NanodegreeHelper, self).load_data()
    if self.action == 'create'and 'nanodegree' in data:
      if 'git_url' not in data['nanodegree']:
        data['nanodegree']['git_url'] = infer_git_url('origin')
      data['nanodegree']['deploy_key'] = read_deploy_key()      

    return data

  def create(self):
    create_deploy_key()

    return super(NanodegreeHelper, self).create()

class QuizHelper(CDHelper):

  def __init__(self, args):
    super(QuizHelper, self).__init__(args)
    self.root_url = gtomscs_root_url(self.environment)

  def find_missing_get_path_params(self, data):
    return {'gtcode', 'quiz_name'} - frozenset(_ for _ in data)

  def find_missing_create_path_params(self, data):
    return {'gtcode'} - frozenset(_ for _ in data)

  def find_missing_params(self, data):
    return {'name', 'timeout', 'executor'} - frozenset(_ for _ in data)

  def find_disallowed_params(self, data):
    return frozenset(_ for _ in data) - {'name', 'executor', 'docker_image', 
                                         'timeout', 'quota_limit', 
                                         'quota_window', 'active'}

  def build_session(self):
    return build_gtomscs_session(self.environment, self.id_provider, self.jwt_path)

  def create_url(self, data):
    return self.root_url + '/courses/' + data['gtcode'] + '/quizzes'

  def update_url(self, data):
    return self.root_url + '/courses/' + data['gtcode'] + '/quizzes/' + data['quiz_name']

  def create(self):
    ans = super(QuizHelper, self).create()

    with open(self.data_file, "r") as fd:
      data = json.load(fd)

    create_files(data['quiz']['name']) 

    return ans

  def update(self):
    raise NotImplementedError("Please visit %s to update your quiz." % self.root_url)

  def get(self):
    raise NotImplementedError("Please visit %s to see your quiz configuration." % self.root_url)

class ProjectHelper(CDHelper):

  def __init__(self, args):
    super(ProjectHelper, self).__init__(args)
    self.root_url = udacity_root_url(self.environment)

  def find_missing_get_path_params(self, data):
    return {'ndkey', 'project_name'} - frozenset(_ for _ in data)

  def find_missing_create_path_params(self, data):
    return {'ndkey'} - frozenset(_ for _ in data)

  def find_missing_params(self, data):
    return {'name', 'udacity_key', 'timeout', 'executor'} - frozenset(_ for _ in data)

  def find_disallowed_params(self, data):
    return frozenset(_ for _ in data) - {'name', 'udacity_key', 'executor', 
                                         'docker_image', 'timeout', 'quota_limit', 
                                         'quota_window', 'active'}

  def build_session(self):
    return build_udacity_session(self.environment, self.id_provider, self.jwt_path)

  def create_url(self, data):
    return self.root_url + '/nanodegrees/' + data['ndkey'] + '/projects'

  def update_url(self, data):
    return self.root_url + '/nanodegrees/' + data['ndkey'] + '/projects/' + data['project_name']

  def create(self):
    ans = super(ProjectHelper, self).create()

    with open(self.data_file, "r") as fd:
      data = json.load(fd)

    create_files(data['project']['name']) 

    return ans

def main(args):
  if args.object == 'course':
    return CourseHelper(args).act()
  elif args.object == 'nanodegree':
    return NanodegreeHelper(args).act()
  elif args.object == 'quiz':
    return QuizHelper(args).act()
  elif args.object == 'project':
    return ProjectHelper(args).act()

def main_func():
  parser = argparse.ArgumentParser(description='CLI for creating nanodegrees and projects for udacity or courses and quizzes for GTOMSCS.')
  parser.add_argument('--environment', default='production', help="webserver environment")
  parser.add_argument('--id_provider', default='udacity', help="identity provider (gt for OMSCS TAs)")
  parser.add_argument('--jwt_path', default=None, help="path to file containing auth information")

  subparsers = parser.add_subparsers(dest="action", help="Action")

  get_parser = subparsers.add_parser("get")
  get_parser.add_argument('object', choices = ['course', 'nanodegree', 'quiz', 'project'], help="what type to act upon")
  get_parser.add_argument('data_file', help="json file containing configuration")

  create_parser = subparsers.add_parser("create")
  create_parser.add_argument('object', choices = ['course', 'nanodegree', 'quiz', 'project'], help="what type to act upon") 
  create_parser.add_argument('data_file', help="json file containing configuration")

  update_parser = subparsers.add_parser("update")
  update_parser.add_argument('object', choices = ['course', 'nanodegree', 'quiz', 'project'], help="what type to act upon") 
  update_parser.add_argument('data_file', help="json file containing configuration")

  args = parser.parse_args()

  obj = main(args)

  json.dump(obj, sys.stdout, indent = 4)

  return 0
