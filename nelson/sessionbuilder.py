from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import input
from builtins import object
import os
import sys
import json
import re
import getpass
import errno
import copy
import requests
from urllib.parse import urlsplit

HOTH_URL = "https://hoth.udacity.com"

def default_app_data_dir():
  APPNAME = "nelson"
  
  if sys.platform == 'win32':
    return os.path.join(os.environ['APPDATA'], APPNAME)
  else:
    return os.path.expanduser(os.path.join("~", "." + APPNAME))

class NelsonAuthenticationError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class SessionBuilder():
  def __init__(self, root_url, id_provider, jwt_path):
    self.root_url = root_url
    self.id_provider = id_provider
    self.jwt_path = jwt_path

  def new(self):
    session = requests.Session()
    session.headers.update({'content-type':'application/json', 'accept': 'application/json'})

    jwt = self.load_jwt_from_file()

    if jwt is None or not self.jwt_works(jwt):
      jwt = self.login_for_jwt()

      if jwt is None or not self.jwt_works(jwt):
        raise RuntimeError("Authentication Failed.")

      save = input('Save the jwt?[y,N]')
      if save.lower() == 'y':
        self.save_the_jwt(jwt)

    self.set_auth_headers(session, jwt)

    return session

  def set_auth_headers(self, session, jwt):
    session.headers.update({'authorization': 'Bearer ' + jwt})

  def jwt_works(self, jwt):
    session = requests.Session()
    session.headers.update({'content-type':'application/json', 'accept': 'application/json'})

    self.set_auth_headers(session, jwt)

    r = session.get(url = self.root_url + '/users/me')

    return r.status_code == 200

  def save_the_jwt(self, jwt):
    try:
      os.makedirs(os.path.dirname(self.jwt_path))
    except OSError as exception:
      if exception.errno != errno.EEXIST:
        raise

    try:
      with open(self.jwt_path, "r") as fd:
        jwt_obj = json.load(fd)
    except:
      jwt_obj = {}

    jwt_obj[self.id_provider] = jwt
    with open(self.jwt_path, "w") as fd:
      json.dump(jwt_obj, fd)


  def load_jwt_from_file(self):
    try:
      with open(self.jwt_path, "r") as fd:
        jwt_obj = json.load(fd)

      jwt = jwt_obj[self.id_provider]
      
      if jwt is None or not self.jwt_works(jwt):
        jwt = None

    except (requests.exceptions.HTTPError, IOError, ValueError, KeyError) as e:
      jwt = None

    return jwt

  def login_for_jwt(self):
    try:
      session = requests.Session()
      session.headers.update({'content-type':'application/json', 'accept': 'application/json'})

      if self.id_provider == 'udacity':
        print("Udacity Login required.")
        email = input('Email :')
        password = getpass.getpass('Password :')
        udacity_login(session, self.root_url, email, password)
      elif self.id_provider == 'gt':
        print("GT Login required.")
        username = input('Username :')
        password = getpass.getpass('Password :')
        gt_login(session, self.root_url, username, password)
      elif self.id_provider == 'developer':
        print("Developer Login required.")
        username = input('Username :')
        developer_login(session, self.root_url, username)
    except requests.exceptions.HTTPError as e:
      if e.response.status_code == 403:
        raise NelsonAuthenticationError("Authentication failed")
      else:
        raise e

    r = session.post(self.root_url + '/auth_tokens')
    r.raise_for_status()

    jwt = r.json()['auth_token']

    return jwt

#Helper functions for logins
def udacity_login(http, root_url, email, password):
  data = {'email' : email, 'password' : password, "next": root_url + "/auth/udacity/callback"}

  #Logging into udacity
  r = http.post(HOTH_URL + '/v2/authenticate', 
                data=data,
                headers={"content-type": "application/x-www-form-urlencoded", "accept": "*/*"})
  r.raise_for_status()

def gt_login(http, root_url, username, password):
  r = http.get(root_url + '/auth/cas',
               headers = {'accept': '*/*'})
  r.raise_for_status

  host = '://'.join(urlsplit(r.url)[0:2])

  action = re.search('action="([^"]*)" method="post">', r.text).group(1)
  data = {}
  data['lt'] = re.search('<input type="hidden" name="lt" value="([^"]*)" />', r.text).group(1)
  data['execution'] = re.search('<input type="hidden" name="execution" value="([^"]*)" />', r.text).group(1)
  data['_eventId'] = re.search('<input type="hidden" name="_eventId" value="([^"]*)" />', r.text).group(1)
  data['warn'] = False

  data['username'] = username
  data['password'] = password

  r = http.post(host + action, data=data, 
                  headers = {'content-type': 'application/x-www-form-urlencoded', 'accept': '*/*'})
  r.raise_for_status()

  if not r.url.startswith(root_url):
    raise ValueError("Username and password failed (Do you use two-factor?)")

def developer_login(http, root_url, username):
  r = http.post(root_url + '/auth/developer/callback', 
                  json = {"username": username},
                  headers = {'accept': '*/*'})
  r.raise_for_status






