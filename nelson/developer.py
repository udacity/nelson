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
    self.object = args.object
    self.data_file = args.data_file
    self.environment = args.environment
    self.id_provider = args.id_provider
    self.jwt_path = args.jwt_path

  def generate(self):
    with open(self.data_file, "r") as fd:
      data = json.load(fd)

    missing_params = self.find_missing_params(data)
    if len(missing_params) > 0:
      raise ValueError("The data file %s is missing required parameters: %s" \
                        % (self.data_file, str(missing_params)))

    return self.create_on_webserver(data)
    
class CourseHelper(CDHelper):

  def __init__(self, args):
    super(CourseHelper, self).__init__(args)
    self.root_url = gtomscs_root_url(self.environment)

  def find_missing_params(self, data):
    return {'gtcode', 'title'} - frozenset(_ for _ in data)

  def create_on_webserver(self, data):
    if 'git_url' not in data:
      data['git_url'] = infer_git_url('origin')

    data['deploy_key'] = read_deploy_key()

    data = {'course': data}

    http = build_gtomscs_session(self.environment, self.id_provider, self.jwt_path)
    r = http.post(self.root_url + '/courses/', data = json.dumps(data))
    r.raise_for_status()

    return r.json()

  def generate(self):
    create_deploy_key()

    return super(CourseHelper, self).generate()


class NanodegreeHelper(CDHelper):

  def __init__(self, args):
    super(NanodegreeHelper, self).__init__(args)
    self.root_url = udacity_root_url(self.environment)

  def find_missing_params(self, data):
    return {'ndkey', 'name'} - frozenset(_ for _ in data)

  def create_on_webserver(self, data):
    if 'git_url' not in data:
      data['git_url'] = infer_git_url('origin')

    data['deploy_key'] = read_deploy_key()

    data = {'nanodegree': data}

    http = build_udacity_session(self.environment, self.id_provider, self.jwt_path)
    r = http.post(self.root_url + '/nanodegrees/', data = json.dumps(data))
    r.raise_for_status()

    return r.json()

  def generate(self):
    create_deploy_key()

    return super(NanodegreeHelper, self).generate()

class QuizHelper(CDHelper):

  def __init__(self, args):
    super(QuizHelper, self).__init__(args)
    self.root_url = gtomscs_root_url(self.environment)

  def find_missing_params(self, data):
    return {'gtcode', 'name', 'executor', 'docker_image'} - frozenset(_ for _ in data)

  def create_on_webserver(self, data):
    data = {'quiz': data}

    http = build_gtomscs_session(self.environment, self.id_provider, self.jwt_path)
    r = http.post("%s/courses/%s/quizzes" % (self.root_url, data['quiz']['gtcode']), data = json.dumps(data))
    r.raise_for_status()

    return r.json()

  def generate(self):
    ans = super(QuizHelper, self).generate()

    with open(self.data_file, "r") as fd:
      data = json.load(fd)

    create_files(data['name']) 

    return ans

class ProjectHelper(CDHelper):

  def __init__(self, args):
    super(ProjectHelper, self).__init__(args)
    self.root_url = udacity_root_url(self.environment)

  def find_missing_params(self, data):
    return {'ndkey', 'name', 'timeout', 'executor', 'docker_image'} - frozenset(_ for _ in data)

  def create_on_webserver(self, data):
    data = {'project': data}

    http = build_udacity_session(self.environment, self.id_provider, self.jwt_path)
    r = http.post("%s/nanodegrees/%s/projects" % (self.root_url, data['project']['ndkey']), data = json.dumps(data))
    r.raise_for_status()

    return r.json()

  def generate(self):
    ans = super(ProjectHelper, self).generate()

    with open(self.data_file, "r") as fd:
      data = json.load(fd)

    create_files(data['name']) 

    return ans

def main(args):
  if args.object == 'course':
    return CourseHelper(args).generate()
  elif args.object == 'nanodegree':
    return NanodegreeHelper(args).generate()
  elif args.object == 'quiz':
    return QuizHelper(args).generate()
  elif args.object == 'project':
    return ProjectHelper(args).generate()

def main_func():
  parser = argparse.ArgumentParser(description='Generator for clyde.')
  parser.add_argument('object', choices = ['course', 'nanodegree', 'quiz', 'project'], help="what to create")
  parser.add_argument('data_file', help="json file containing configuration")

  parser.add_argument('--environment', default='production', help="webserver environment")
  parser.add_argument('--id_provider', default='udacity', help="identity provider (gt for OMSCS TAs)")
  parser.add_argument('--jwt_path', default=None, help="path to file containing auth information")

  args = parser.parse_args()

  obj = main(args)

  json.dump(obj, sys.stdout, indent = 4)

  return 0
