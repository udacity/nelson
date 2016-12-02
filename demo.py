from nelson.gtomscs import submit

def main():
  course = 'cs101'
  quiz = 'hello_world'
  filenames = ['hello_world.py']

  submit(course, quiz, filenames)

if __name__ == '__main__':
  main()