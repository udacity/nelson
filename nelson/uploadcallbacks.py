import sys

def default_upload_progress_callback(encoder):
  pass

def progressbar_callback(monitor):
  total_bytes = monitor.encoder.len
  pct = float(monitor.bytes_read) / total_bytes

  l_fill = "{:<27}".format("=" * min(int((min(0.5, pct) / 0.5) / 0.5 * 30), 27))
  p_fill = "{:^4}".format(str(int(pct * 100)) + "%")
  r_fill = "{:<27}".format("=" * min(int(min(pct - 0.5, 0.5) / 0.5 * 30), 27))
  ratio = "{!s}/{!s}".format(monitor.bytes_read, total_bytes)
  line = "[{} {} {}] {}".format(l_fill, p_fill, r_fill, ratio)
  sys.stdout.write("\r{}".format(line))
  sys.stdout.flush()