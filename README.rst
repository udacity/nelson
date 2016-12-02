===========
nelson
===========

Projects for Georgia Tech's OMSCS program or for Udacity's advanced nanodegree programs are typically distributed with project-specific submission scripts that handle the submission to Udacity's advanced automatic feedback service.  These scripts typically rely on this underlying library, which contains most of the shared functionality.


Examples
---------

This is simple example for GTOMSCS.  It submits the file hello_world.py to the quiz named "hello_world" within the course "cs101".
::
    from nelson.gtomscs import submit

    def main():
        course = 'cs101'
        quiz = 'hello_world'
        filenames = ['hello_world.py']

        submit(course, quiz, filenames)

    if __name__ == '__main__':
        main()

For Udacity, simply import from ``nelson.udacity`` instead of ``nelson.gtomscs``.
