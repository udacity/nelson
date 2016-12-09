from nelson.gtomscs import submit

def main():
    course = 'csXXXX'
    quiz = 'helloworld'
    filenames = ['hello_world.py']

    submit(course, quiz, filenames)

if __name__ == '__main__':
    main()