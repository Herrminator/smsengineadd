#!/bin/env python

# $Id: xullint.py 41 2012-02-01 00:19:51Z hhofer69 $

import sys, os, re, optparse, tempfile, subprocess as sp, urllib

XMLLINT = os.environ.get("XMLLINT",  "xmllint")

def chrome_manifest(opts):
  loc, skin = opts.locale, opts.skin
  mf = { "content": {}, "skin": {}, "locale": {}, "resource": {} }
  
  for fn in opts.manifests:
    f = file(fn)
    for l in f:
      l = l.strip()
      if not l or l[0] == "#": continue
      ent = l.split()
      what, id, data = ent[0], None, []
      if   what in [ "content", "resource" ]:   id, data = ent[1], ent[2:]
      elif what == "locale" and ent[2] == loc:  id, data = ent[1], ent[3:]
      elif what == "skin"   and ent[2] == skin: id, data = ent[1], ent[3:]
      if id:  mf[what][id] = (data, os.path.abspath(os.path.dirname(fn)))
    f.close()
  return mf

def main(argv=sys.argv[1:]):
  try:
    op = optparse.OptionParser(usage="xullint [options] <FileName> [-- [xmllint options]]")
    
    op.add_option("-d", "--dir",       default="")
    op.add_option("-l", "--locale",    default="en-US")
    op.add_option("-s", "--skin",      default="classic/1.0")
    op.add_option("-m", "--manifests", default=[], action="append")
    
    opts, args = op.parse_args(argv)
  
    if len(args) < 1:
      print >> sys.stderr, "No filename specified."
      return 2

    fname    = args[0]
    lintopts = args[1:]

    if not opts.manifests:
      opts.manifests = [os.path.join(os.path.abspath(opts.dir), "chrome.manifest")]
    for i in range(len(opts.manifests)):
      opts.manifests[i] = os.path.abspath(opts.manifests[i])

    f = file(fname)
    xul = f.read()
    f.close()
    
    mf = chrome_manifest(opts)
    
    def replacer(m):
      id, what, path = m.group(2), m.group(3), m.group(4)
      try:
        abs = os.path.join(mf[what][id][1], mf[what][id][0][0], path)
        return 'SYSTEM %sfile:%s%s' % (m.group(1), urllib.pathname2url(abs).replace("|",":"), m.group(5))
      except KeyError, exc:
        from pprint import pformat
        print >> sys.stderr, "Entry '%s %s' not found in %s (`%s`)" %\
                             (what, id, opts.manifests, pformat(mf))
        raise

    xul = re.sub(r'SYSTEM ("|\')chrome://(\w+)/(\w+)/(.*?\w+\.dtd)(\1\s*>)',
                 replacer, xul)
    
    tmp, tname = tempfile.mkstemp(suffix=".xul");
    try:
      os.write(tmp, xul); os.close(tmp)
      
      cmd = XMLLINT
      if isinstance(cmd, basestring): cmd = cmd.split()
      cmd += lintopts + [ tname ]

      p = sp.Popen(cmd, stderr=sp.PIPE, shell=True)
      rc = p.wait()
      errs = p.stderr.read().strip()
      if errs:
        print >> sys.stderr, errs

      if rc != 0 or errs: # xmlint return 0 on undefined entities/tags
        return rc or 1;   # we don't want that!

    finally:
      os.unlink(tname)
      pass

  except Exception, exc:
    import traceback; traceback.print_exc()
    return 42
  
  return 0

if __name__ == "__main__":
  sys.exit(main())
