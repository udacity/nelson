import os
from .abstract import Submission as AbstractSubmission
from .abstract import submit as abstractsubmit
from .uploadcallbacks import progressbar_callback
from .sessionbuilder import SessionBuilder, default_app_data_dir

def root_url(environment):
  url = {'development': 'http://local-dev.udacity.com:3000',
         'staging': 'https://autograder-staging.udacity.com',
         'production': 'https://autograder.udacity.com'}

  return url[environment]

def build_session(environment = 'production', id_provider = 'udacity', jwt_path = None):
    jwt_path = jwt_path or os.path.join(default_app_data_dir(), 'udacity_jwt')

    return SessionBuilder(root_url(environment),
                          id_provider,
                          jwt_path).new()

def submit(nanodegree, 
           project, 
           filenames,
           environment = 'production', 
           id_provider = 'udacity',
           max_zip_size = 8 << 20,
           jwt_path = None,
           refresh_time = 3):

    session = build_session(environment, id_provider, jwt_path)
    
    submission = Submission(nanodegree,
                            project,
                            session,
                            filenames,
                            max_zip_size = max_zip_size,
                            upload_progress_callback = progressbar_callback,
                            environment = environment)

    return abstractsubmit(submission, refresh_time = refresh_time)


#Submissions for GTOMSCS
class Submission(AbstractSubmission):
  def __init__(self, 
               nanodegree, 
               project,
               session,
               filenames,
               max_zip_size = 8 << 20,
               upload_progress_callback = None,
               environment = 'production'):

    self.nanodegree = nanodegree
    self.project = project
    self.environment = environment

    super(Submission, self).__init__(session,
                                     filenames,
                                     max_zip_size = max_zip_size,
                                     upload_progress_callback = upload_progress_callback)

  def project_name(self):
    return self.project

  def _get_submit_url(self):
    return root_url(self.environment) + "/student/nanodegree/%s/project/%s/submission" % (self.nanodegree, self.project)   

  def _get_poll_url(self):
    return root_url(self.environment) + "/student/nanodegree/%s/project/%s/submission/%s" % (self.nanodegree, self.project, self.submission['id'])

