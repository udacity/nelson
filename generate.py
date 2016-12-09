import os
import stat
import argparse
import errno
import requests
import json
import logging
import getpass
import subprocess as sp

from bonnie_session import BonnieSession

def safe_mkdirs(path):
	try:
		os.makedirs(path)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise

def create_run(quiz_name):
	s = """import subprocess as sp
import os

def main():
	sp.call(['gcc', '-o', 'helloworld', 'main.c', 'helloworld.c'], cwd = 'workspace')

	with open(os.path.join("workspace", "helloworld_stdout.txt"), "w") as fd:
		sp.call(['./helloworld'], stdout=fd, cwd = 'workspace')

if __name__ == '__main__':
	main()
"""
	filename = os.path.join('app', quiz_name, 'run.py')
	if not os.path.isfile(filename):
		with open(filename, 'w') as fd:
			fd.write(s)

	linkname = os.path.join('development', quiz_name, 'run.py')
	if not os.path.isfile(linkname) and not os.path.islink(linkname):
		os.symlink(os.path.relpath(filename,os.path.join('development', quiz_name)), linkname)

def create_grade(quiz_name):
	s = """import sys
import subprocess as sp
import json
import os

def main():
	with open(os.path.join('workspace', "helloworld_stdout.txt"), "r") as fd:
		output = fd.read()
		if output.rstrip() == "Hello World!":
			result = {"correct" : True, "output" : output}
		else:
			result = {"correct" : False, "output" : output}

	json.dump(result, sys.stdout)

if __name__ == '__main__':
	main()
"""

	filename = os.path.join('app', quiz_name, 'grade.py')
	if not os.path.isfile(filename):
		with open(filename, 'w') as fd:
			fd.write(s)

	linkname = os.path.join('development', quiz_name, 'grade.py')
	if not os.path.isfile(linkname) and not os.path.islink(linkname):
		os.symlink(os.path.relpath(filename,os.path.join('development', quiz_name)), linkname)


def create_main(quiz_name):
	s = """#include <stdlib.h>

extern void printHelloWorld();

int main(int argc, char **argv){
        printHelloWorld();
}
"""
	filename = os.path.join('app', quiz_name, 'workspace', 'main.c')
	if not os.path.isfile(filename):
		with open(filename, 'w') as fd:
			fd.write(s)

	linkname = os.path.join('development', quiz_name, 'workspace', 'main.c')
	if not os.path.isfile(linkname) and not os.path.islink(linkname):
		os.symlink(os.path.relpath(filename,os.path.join('development', quiz_name, 'workspace')), linkname)


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


def create_quiz(http, quiz_name, executor, docker_image, timeout, quota_limit, quota_window, git_url):
	r = http.get(http.root_url + "/courses", params = {'git_url': git_url})
	r.raise_for_status()

	course_id = r.json()[0]['id']

	data = {'course_id': course_id, 'quiz': {'name': quiz_name, 
																					 'executor': executor,
																					 'docker_image': docker_image,
																					 'timeout': timeout, 
																					 'quota_limit': quota_limit,
																					 'quota_window': quota_window,
																					 'active?': True}}

	r = http.post(http.bonnie_url("/courses/%s/quizzes" % course_id), data = json.dumps(data))
	r.raise_for_status()

def create_course(http, gtcode, title, git_url, deploy_key):
	data = {"gtcode": gtcode, "title": title, "git_url": git_url, "deploy_key":deploy_key}
	r = http.post(http.bonnie_url('/courses/'), data = json.dumps(data))
	r.raise_for_status()


def generate_course(args):
	create_deploy_key()

	gtcode = args.gtcode
	title = args.title
	git_url = infer_git_url(args.remote)
	deploy_key = read_deploy_key()

	http = BonnieSession(args.environment, args.provider)
	create_course(http, gtcode, title, git_url, deploy_key)

def generate_quiz(args):
	deploy_key = read_deploy_key()

	quiz_name = args.quiz_name
	git_url = infer_git_url(args.remote)

	http = BonnieSession(args.environment, args.provider)
	create_quiz(http, quiz_name, args.executor, args.docker_image, args.timeout, args.quota_limit, args.quota_window, git_url)

	safe_mkdirs(os.path.join('app', quiz_name, 'workspace'))
	safe_mkdirs(os.path.join('development', quiz_name, 'workspace'))
	safe_mkdirs(os.path.join('coaching', quiz_name))

	create_run(quiz_name)
	create_grade(quiz_name)
	create_main(quiz_name)

	params = {}
	params['quiz_name'] = quiz_name
	params['deploy_key'] = deploy_key
	params['timeout'] = args.timeout
	params['git_url'] = git_url
	params['zipfile_path'] = 'student.zip'
	params['git_branch'] = 'develop'

def main():
	parser = argparse.ArgumentParser(description='Generator for clyde.')
	subparsers = parser.add_subparsers(dest="action", help="Action")

	parent_parser = argparse.ArgumentParser()

	course_parser = subparsers.add_parser("course")
	course_parser.add_argument('--gtcode', help="specify the gtcode of the course, e.g. CS6210", required=True)
	course_parser.add_argument('--title', help="specify the title of the course", required = True)
	course_parser.add_argument('--environment', default='production')
	course_parser.add_argument('--provider', default='gt')
	course_parser.add_argument('--remote', default='origin')

	quiz_parser = subparsers.add_parser("quiz")
	quiz_parser.add_argument('--quiz_name', help="specify the name of the quiz.", required=True)
	quiz_parser.add_argument('--executor', help="specify the executor for the quiz", required=True)
	quiz_parser.add_argument('--docker_image', help='specify the docker_image', default=None)
	quiz_parser.add_argument('--timeout', help="specify the timeout of the quiz", type=int, default=30)
	quiz_parser.add_argument('--quota_limit', 
	                         help="specify the number of submissions permitted within the quota_window", type=int, default=0)
	quiz_parser.add_argument('--quota_window', 
	                         help="specify amount of time to which the quota_limit applies", type=int, default=0)
	quiz_parser.add_argument('--environment', choices=['production', 'staging', 'development', 'local'], default='production')
	quiz_parser.add_argument('--provider', default='gt')
	quiz_parser.add_argument('--remote', default='origin')

	args = parser.parse_args()

	if args.action == 'course':
		generate_course(args)
	elif args.action == 'quiz':
		generate_quiz(args)
	else:
		raise ValueError('Invalid action ' + args.action)

if __name__ == '__main__':
	main()