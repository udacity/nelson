import sys
import subprocess as sp
import json
import os

def main():
  with open(os.path.join('workspace', "helloworld_stdout.txt"), "r") as fd:
    output = fd.read()
    if output.rstrip() == "Hello World!":
      result = {"correct" : True, "output" : output}
    else:
      result = {"correct" : False, "output" : output}

  json.dump(result, sys.stdout)

if __name__ == '__main__':
  main()
