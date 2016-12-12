import sys
import os
import json
import StringIO

def console_summary(feedback):
  output = StringIO.StringIO()
  for t in feedback['tests']:
    description = '{:70s}'.format(t['description'][:69]+":")
    points = "%d/%d" % (t["output"].get("points_awarded") or 0, t["output"]["points_available"])
    output.write('%s %s\n' % (description, points.rjust(9)))

  return output.getvalue()

def main():
  with open("workspace/grade.json", "r") as fd:
    feedback = json.load(fd)

  sys.stdout.write(console_summary(feedback))

if __name__ == '__main__':
  main()
