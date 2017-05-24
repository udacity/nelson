# Summary
For autograding of large projects that requires extensive testing, udacity uses the clyde sandboxed remote execution environment.  To submit jobs and allow TAs to pull submissions, GTOMSCS uses the [bonnie](https://github.com/udacity/bonnie) webserver.  Analogously, Udacity Nanodegrees use [project-assistant](https://github.com/udacity/project-assistant).

Nelson is a CLI tool for creating the required directory structure and populating the necessary databases behind the webserver.

# Nanodegree/Course Generation
Course/Nanodegree generation is typically done by a Udacity employee (TA collaborators may skip this section).  

Typically
<pre><code>
nelson nanodegree data.json
</code></pre>
where data.json contains something like
<pre><code>
{
    "nanodegree": {
        "ndkey": "nd123",
        "name": "Test Nanodegree",
        "git_url": "git@github.com:udacity/nd123-autograder.git"
    }
}
</code></pre>
The git_url parameter should point to the repository of autograding code to be used for course or nanodegree.  For the required organization of this repo, see below.

The analogous data file for a GTOMSCS course would be
<pre><code>
{
    "course": {
        "gtcode": "csXXXX",
        "name": "Test Course",
        "git_url": "git@github.com:udacity/csXXXX-autograder.git"
    }
}
</code></pre>

See `nelson --help` for details on controlling environment and login.

# Project/Quiz Generation
To add a new project to your nanodegree (or quiz to your course), run
<pre><code>nelson create project data.json OPTIONS </code></pre>
This will both register the project with the webserver and the necessary generate directories and files in the current directory.  A typical data.json file would look like
<pre><code>
{
    "ndkey": "csXXXX",
    "project": {
        "name": "helloworld",
        "udacity_key": "123456789",
        "executor": "docker",
        "docker_image": "gtomscs/default",
        "timeout": 30,
        "quota_window": null, 
        "quota_limit": null,
        "active" : true
    }
}
</code></pre>
For OMSCS, run
<pre><code>nelson --id_provider gt create quiz data.json OPTIONS </code></pre>, where data.json is like
<pre><code>
{
    "gtcode": "csXXXX",
    "quiz": {
        "name": "helloworld",
        "executor": "docker",
        "docker_image": "gtomscs/default",
        "timeout": 30,
        "quota_window": null, 
        "quota_limit": null,
        "active" : true
    }
}
</code></pre>

## Essential Parameters
The parameters `ndkey`, `name`, `timeout`, and `executor` are always required when creating a project or quiz.  For most, it is possible to run the test code inside of a docker container.  In this case, the `executor` parameter should be "docker" and you must use the `docker_image` parameter, e.g. `gtomscs/default`.  All docker images can be see at [gtomscs docker organization](https://hub.docker.com/r/gtomscs/).

## Additional Project/Quiz Parameters
Some additional parameters are:

1. *Timeout* -- how many seconds the quiz may run.
2. *Quota Limit* -- how many times a quiz may be submitted within the "Quota Window"
3. *Quota Window* -- the quota window specified in seconds.
4. *Active?* -- whether the quiz is active.  Use this to prevent students from submitting to the quiz.

These can be specified at the time of the project/quiz creation or they can be adjusted by visiting the appropriate page on the webserver (/admin for Udacity, the Course Developer portal for GTOMSCS).

## Generated Files
For illustrative purposes we will assume that the project/quiz name "lab01." was chosen.  Nelson will create the following files and directories

- app/
    - lab01/
        - run.py
        - grade.py
        - workspace/

- deploy_keys
    - deploy_id_rsa
    - deploy_id_rsa.pub

In brief, the **app/** directory is where you should place the files to be used as part of the autograding process.  The **deploy_keys/** directory contains the public/private key pair that will be used to deploy your code (Because it will be read-only, it's okay to keep it in the repository.)  Feel free to add other directories such as test/ that might aid in development.

# How it works
Only the **app** directory on your autograding git repo will be deployed to the autograding machines.  It should contain the all the code  that you use for grading.  Symlinks internal to the **app** directory are okay, ones external to **app** are not.  Thus, **app/lab01/util.py** can link to **app/shared/util.py**, but it should not link to **shared/util.py**.

During actual evaluation of the student's code, the contents of the **app/lab01/** directory is placed in the student's home directory and the students code is place inside of the **workspace** folder.  Thus, if your **app** directory contains the files

- app/
    - lab01/
        - run.py
        - grade.py
        - workspace/
            - lab01_grader.py
            - test_images/
                - foo.png
                - bar.png


and the zipfile submitted by the student has the contents

- lab01.pdf
- lab01.py
- lib/
    - libfoo.py

then the resulting merged structure on the executor would be

- /home/vmuser_xyz
    - run.py
    - grade.py    
    - workspace/
        - lab01.pdf
        - lab01.py
        - lab01_grader.py
        - lib/
            - libfoo.py
        - test_images/
            - foo.png
            - bar.png

## Available Hooks
After merging the files into this structure, the autograder will try to run five scripts from the level above workspace.  These are **setup.py**, **run.py**, **grade.py**, **feedback.py** and **console.py**.  Only **grade.py** is required.

### setup.py
If the file **setup.py** exists, it will be executed it passing in the name of the quiz, e.g.
<pre><code>python setup.py lab01</code></pre>
This script is executed under a user with passwordless sudo privileges.  Common uses for this hook include setting permission on files that the student should not be able to read and starting services like rpcbind within a docker container.

### run.py  
Next, the autograder will execute the **run.py** script, again passing in the quiz name as the sole argument.
<pre><code>python run.py lab01</code></pre>
For security, this script is run as the student user (vmuser_xyz above) with limited permissions, available memory, and time.  *This is the only place that it is safe to call student code.*  Usually, this is where the bulk of the grading is performed.

### grade.py  
Next, the autograder will execute the **grade.py** script.
<pre><code>python grade.py lab01</code></pre>
The output of this script is what gets stored in the "result" field of the submission and it should contain all feedback that you wish to give to the TA.  Most often **run.py** actually produces the key results and saves them to a file.  Then **grade.py** just writes this content to stdout.

### feedback.py
If a file named **feedback.py** exists , the autograder will execute it.
<pre><code>python feedback.py lab01</code></pre>
The output of this script is what gets stored in the "feedback" field of the submission and it should contain all feedback that you wish to give to the student.  If this script is absent, then the same content will be shown to the TA as to the student.

### console.py
Finally, if a file named **console.py** exists, the autograder will execute it.
<pre><code>python console.py lab01</code></pre>
The output of this script is what gets stored in the "console" field of the submission.  This should contain easy-to-read text, as it will be displayed first to the students when they view their submission in a web-browser.  By convention, it is also typically the text that is displayed to students when they submit via the console.

## Limitations
Here is a list of limits enforced by the system.

1. The serialized json object returned by the sandbox cannot exceed 64KB.  Thus, the combined output of **grade.py** and **feedback.py** should be kept a little under 64KB.
2. The execution of **run.py** cannot use more than 500MB of memory.
3. Assorted limits on the number of open files and the like, which we have not encountered yet.

# Local development and testing

Although many development strategies are possible, a common practice is to include sample student code in the **app/project_name/workspace/** directory and call `python run.py`, `python grade.py` etc. from the **app/project_name/** directory.  One danger is that it is easy to accidentally commit these files to the git repository and thus include them with the autograder code, clobbering the actual student submission.  Therefore, it is suggested that you use a whitelist pattern in your **workspace/.gitignore** directory.  The sample code created with each quiz illustrates this pattern.

Another good practice is to include sample submissions as part of the repository, so that collaborators may access the same code that you are using to develop and test.  These files should be placed *outside* of **app/** directory for the purposes of source control.  But they can be copied in linked into **app/project_name/workspace** as needed.


## Vagrant/Docker
Although the test code runs in a docker container, docker is usually not friendly enough for CDs and students to use.  Therefore, along with every docker image, we also provision an analogous vagrant image.

Although it is not necessary, it is recommended that you develop your tests on the Vagrant box that is analogous to the autograding machine.  For now, this means running something like 
<pre><code>
vagrant init udacity/compphoto
vagrant up --provider virtualbox
</code></pre>

See instructions given to the students or the [Vagrant site](https://www.vagrantup.com/)
