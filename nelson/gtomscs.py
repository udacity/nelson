import os
from .abstract import Submission as AbstractSubmission
from .abstract import submit as abstractsubmit
from .uploadcallbacks import progressbar_callback
from .sessionbuilder import SessionBuilder, default_app_data_dir

def root_url(environment):
  url = {'local': 'http://local-dev.udacity.com:3000',
         'development': 'https://bonnie-dev.udacity.com',
         'staging': 'https://bonnie-staging.udacity.com',
         'production': 'https://bonnie.udacity.com'}

  return url[environment]

def build_session(environment = 'production', id_provider = 'gt', jwt_path = None):
    jwt_path = jwt_path or os.path.join(default_app_data_dir(), 'gtomscs_jwt')

    return SessionBuilder(root_url(environment),
                          id_provider,
                          jwt_path).new()

def submit(gtcode, 
           quiz_name, 
           filenames,
           environment = 'production', 
           id_provider = 'gt',
           max_zip_size = 8 << 20,
           jwt_path = None,
           refresh_time = 3):

    session = build_session(environment, id_provider, jwt_path)
    
    submission = Submission(gtcode,
                            quiz_name,
                            session,
                            filenames,
                            max_zip_size = max_zip_size,
                            upload_progress_callback = progressbar_callback,
                            environment = environment)

    return abstractsubmit(submission, refresh_time = refresh_time)


#Submissions for GTOMSCS
class Submission(AbstractSubmission):
  def __init__(self, 
               gtcode, 
               quiz_name,
               session,
               filenames,
               max_zip_size = 8 << 20,
               upload_progress_callback = None,
               environment = 'production'):

    self.gtcode = gtcode
    self.quiz_name = quiz_name
    self.environment = environment

    super(Submission, self).__init__(session,
                                     filenames,
                                     max_zip_size = max_zip_size,
                                     upload_progress_callback = upload_progress_callback)

  def project_name(self):
    return self.quiz_name

  def _get_submit_url(self):
    return root_url(self.environment) + "/student/course/%s/quiz/%s/submission" % (self.gtcode, self.quiz_name)   

  def _get_poll_url(self):
    return root_url(self.environment) + "/student/course/%s/quiz/%s/submission/%s" % (self.gtcode, self.quiz_name, self.submission['id'])

