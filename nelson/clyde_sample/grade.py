import sys
import os

def main():
  with open(os.path.join('workspace', "grade.json"), "r") as fd:
    sys.stdout.write(fd.read())

if __name__ == '__main__':
  main()
