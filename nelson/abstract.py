from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import input
from builtins import object
import os
import sys
import zipfile
import json
import re
import getpass
import errno
import copy
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
import requests
import time
import datetime
from itertools import cycle
from urllib.parse import urlsplit
from .uploadcallbacks import default_upload_progress_callback, progressbar_callback

SUBMISSION_FILENAME = 'student.zip'

def submit(submission, refresh_time = 3):

    print("Submission includes the following files:")
    print('\n'.join(['    ' + f for f in submission.filenames]))
    print("")

    print("Uploading submission...")
    submission.submit()
    print("\n")

    wheel = cycle(['|', '/', '-', '\\'])
    spin_freq = 8.
    while not submission.poll():
      for _ in range(int(refresh_time * spin_freq)):
        sys.stdout.write("\rWaiting for results... {}".format(wheel.next()))
        sys.stdout.flush()
        time.sleep(1. / spin_freq)
    sys.stdout.write("\rWaiting for results...Done!\n\n")

    print("Results:\n--------")
    if submission.feedback():
      if submission.console():
        print(submission.console())

      timestamp = "{:%Y-%m-%d-%H-%M-%S}".format(datetime.datetime.now())
      filename = "%s-result-%s.json" % (submission.project_name(), timestamp)

      with open(filename, "w") as fd:
          json.dump(submission.feedback(), fd, indent=4, separators=(',', ': '))

      print("\n(Details available in %s)\n" % filename)

    elif submission.error_report():
        print(json.dumps(submission.error_report(), indent=4))

    else:
        print("Unknown error.")

#Abstract class for uploading submissions
class Submission(object):
  
  def _root_url(self):
    raise NotImplementedError()

  def _get_submit_url(self):
    raise NotImplementedError()

  def _get_poll_url(self):
    raise NotImplementedError()

  def project_name(self):
    raise NotImplementedError()

  def __init__(self,
               session,
               filenames,
               max_zip_size = 8 << 20,
               upload_progress_callback = None):

    self.s = session
    self.filenames = copy.deepcopy(filenames)
    self.max_zip_size = max_zip_size
    self.upload_progress_callback = upload_progress_callback or default_upload_progress_callback

  def submit(self):

    self.submit_url = self._get_submit_url()

    mkzip(os.path.dirname(sys.argv[0]), SUBMISSION_FILENAME, self.filenames, self.max_zip_size)

    fd = open(SUBMISSION_FILENAME, "rb")

    m = MultipartEncoder(fields={'zipfile': ('student.zip', fd, 'application/zip')})
    monitor = MultipartEncoderMonitor(m, self.upload_progress_callback)

    try:
      r = self.s.post(self.submit_url, 
                      data=monitor,
                      headers={'Content-Type': monitor.content_type})
      r.raise_for_status()
    except requests.exceptions.HTTPError as e:
      if r.status_code == 403:
        raise RuntimeError("You don't have access to this quiz.")
      elif r.status_code in [404,429,500]:
        try:
          response_json = r.json()
          message = response_json.get("message") or "An internal server error occurred."
        except:
          message = "An unknown error occurred"
        raise RuntimeError(message)
      else:
        raise

    fd.close()

    self.submission = r.json()

  def poll(self):
    r = self.s.get(self._get_poll_url())
    r.raise_for_status()

    self.submission = r.json()

    return self.submission['feedback'] is not None or self.submission['error_report'] is not None

  def result(self):
    return self.feedback()

  def feedback(self):
    return self.submission['feedback']

  def console(self):
    return self.submission['console']

  def error_report(self):
    return self.submission['error_report']


#Zipfile helper function
def mkzip(root_path, zipfilename, filenames, max_zip_size):
  abs_root_path = os.path.abspath(root_path)
  abspaths = [os.path.abspath(x) for x in filenames]

  if os.path.commonprefix([abs_root_path] + abspaths) != abs_root_path:
    raise ValueError("Submitted files must in subdirectories of %s." % (root_path or "./"))

  with zipfile.ZipFile(zipfilename,'w') as z:
    for f in filenames:
      zpath = os.path.relpath(f, root_path)
      z.write(f, zpath)

  if os.stat(zipfilename).st_size > max_zip_size:
    raise ValueError("Your zipfile exceeded the limit of %d bytes" % max_zip_size)
