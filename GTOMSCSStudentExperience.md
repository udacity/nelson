# Student Experience
GTOMSCS classes may also use nelson to help them create submission scripts for their students.  (Udacity uses [udacity-pa](https://github.com/udacity/udacity-pa))

Ideally, the student's experience should be as simple as follows.  First, they should install nelson with
<pre><code>pip install nelson </code></pre>
Then they should checkout out the git repository with the student-facing code for the project.  This should contain a script *submit.py*, which they can then use to submit their code with
<pre><code>python submit.py OPTIONS </code></pre>

# Writing submit.py

Just an example for now
<pre><code>
from nelson.gtomscs import submit

def main():
    course = 'csXXXX'
    quiz = 'helloworld'
    filenames = ['hello_world.py']

    submit(course, quiz, filenames)

if __name__ == '__main__':
    main()
</code></pre>

