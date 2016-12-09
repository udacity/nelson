import os
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

  logging.warning("Deploy key already exists")

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
        ans = 'git@github.com:' + words[1][19:] + '.git'

  if ans == None:
    raise RuntimeError("Unable to infer git_url")

  if ans == 'git@github.com:udacity/clyde-starter':
    raise RuntimeError("You must create a new remote repository.")

  return ans

def create_quiz(http, gtcode, quiz_data):
  data = {'quiz': quiz_data}

  r = http.post("%s/courses/%s/quizzes" % (http.root_url, gtcode), data = json.dumps(data))
  r.raise_for_status()

def create_project(http, ndkey, project_data):
  data = {'project': project_data}

  r = http.post("%s/nanodegrees/%s/projects" % (http.root_url, ndkey), data = json.dumps(data))
  r.raise_for_status()

def create_course(http, course_data):
  r = http.post(http.root_url + '/courses/', data = json.dumps(course_data))
  r.raise_for_status()

def create_nanodegree(http, nanodegree_data):
  r = http.post(http.root_url + '/nanodegrees/', data = json.dumps(course_data))
  r.raise_for_status()

def create_files(name):
  src = os.path.dirname(resource_filename(Requirement.parse("nelson"),"/nelson/clyde_sample/run.py"))

  dst = os.path.join('app', name)
  if not os.path.isfile(dst):
    shutil.copyfile(src, dst)

  linkname = os.path.join('development', name, 'workspace', 'main.c')
  if not os.path.isfile(linkname) and not os.path.islink(linkname):
    os.symlink(os.path.relpath(dst,os.path.join('development', name, 'workspace')), linkname)

def params_missing_for_gtomscs_course(data):
  return {'gtcode', 'title'} - frozenset(_ for _ in data)

def params_missing_for_udacity_nanodegree(data):
  return {'ndkey', 'name'} - frozenset(_ for _ in data)

def params_missing_for_gtomscs_quiz(data):
  return {'gtcode', 'name', 'executor', 'docker_image'} - frozenset(_ for _ in data)

def params_missing_for_udacity_project(data):
  return {'ndkey', 'name', 'executor', 'docker_image'} - frozenset(_ for _ in data)

def generate_course(args):
  with open(args.data_file, "r") as fd:
    data = json.load(fd)

  missing_params = params_missing_for_gtomscs_course(data)
  if len(missing_params) > 0:
     raise ValueError("The data file %s is missing required parameters: %s" \
                      % (data_file, str(missing_params)))

  create_deploy_key()
  data['git_url'] = infer_git_url(data.get('remote') or 'origin')
  data['deploy_key'] = read_deploy_key()

  session = build_gtomscs_session(environment, id_provider, jwt_path)
  create_course(session, data)

def seed_local_files(name):
  #Creating the needed directories
  safe_mkdirs('app')
  safe_mkdirs(os.path.join('development', name, 'workspace'))
  safe_mkdirs(os.path.join('coaching', name))

  #Seeding with sample files
  src = os.path.dirname(resource_filename(Requirement.parse("nelson"),
                                          "/nelson/clyde_sample/grade.py"))
  dst = os.path.join('app', name)
  shutil.copyfile(src, dst)

  #Creating appropriate links
  for dirpath, dirs, files in os.walk(dst):
    for f in files:
      linkname = os.path.join('development', name, os.path.join(dirpath,f))
      if not os.path.isfile(linkname) and not os.path.islink(linkname):
        os.symlink(os.path.relpath(dst, os.path.dirname(linkname)), linkname)

def generate(args, find_missing_params, build_session):
  with open(args.data_file, "r") as fd:
    data = json.load(fd)

  missing_params = find_missing_params(data)
  if len(missing_params) > 0:
    raise ValueError("The data file %s is missing required parameters: %s" \
                      % (args.data_file, str(missing_params)))

  session = build_session(args.environment, args.id_provider, args.jwt_path)
  create_project(session, data)

  if args.object in ['quiz', 'project']:
    seed_local_files(data['name']) 

def main_func():
  parser = argparse.ArgumentParser(description='Generator for clyde.')
  parser.add_argument('object', choices = ['course', 'nanodegree', 'quiz', 'project'])
  parser.add_argument('data_file')

  parser.add_argument('--environment', default='production')
  parser.add_argument('--id_provider', default=None)
  parser.add_argument('--jwt_path', default=None)

  args = parser.parse_args()

  if args.action == 'course':
    generate_course(args, params_missing_for_gtomscs_course, build_gtomscs_session)
  elif args.action == 'nanodegree':
    generate_quiz(args, params_missing_for_udacity_nanodegree, build_udacity_session)
  elif args.action == 'quiz':
    generate_course(args, params_missing_for_gtomscs_quiz, build_gtomscs_session)
  elif args.action == 'project':
    generate_project(args, params_missing_for_udacity_project, build_udacity_session)

  return 0
