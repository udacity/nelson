import subprocess as sp
import os

def main():
  sp.call(['gcc', '-o', 'helloworld', 'main.c', 'helloworld.c'], cwd = 'workspace')

  with open(os.path.join("workspace", "helloworld_stdout.txt"), "w") as fd:
    sp.call(['./helloworld'], stdout=fd, cwd = 'workspace')

if __name__ == '__main__':
  main()
