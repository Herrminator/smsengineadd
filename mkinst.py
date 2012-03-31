#!/bin/env python

# $Id: mkinst.py 85 2012-03-05 16:52:14Z hhofer69@gmail.com $

import sys, os, re, shutil, zipfile, glob, optparse, time

DEFPROJ    = os.path.basename(os.path.dirname(__file__))

ROOT_FILES = "chrome modules defaults chrome.manifest install.rdf bootstrap.js changelog.txt"
OUTDIR     = "versions"

JAR       = os.environ.get("JAR",       "jar")
SHA1SUM   = os.environ.get("SHA1SUM",   "sha1sum")
SVN       = os.environ.get("SVN",       "svn")
JSCHK     = os.environ.get("JSCHK",     'jsshell -s -C -e options(\'werror\')')
XULLINT   = os.environ.get("XULLINT",   "xullint.py")
AMOEXIT   = os.environ.get("AMOEXIT",   "amoexit.py")
BUILDEXIT = os.environ.get("BUILDEXIT", "buildexit.py")

XMLLINT_OPTS = "--nodefdtd --noout"
LOCALES      = [ "en-US", "de-DE", "fr-FR" ]

VERPATT      = r'([\d.]+)((?:pre\d+)?)(-dev)?'

def main(argv=sys.argv[1:]):
  op = optparse.OptionParser()
  op.add_option("-p", "--project",   default=DEFPROJ)
  op.add_option("-d", "--directory", default=None)
  op.add_option("-i", "--inpdir",    default=".")
  op.add_option("-o", "--outdir",    default=OUTDIR)
  op.add_option("-b", "--builddir",  default="build", help="only for SVN")
  op.add_option("-m", "--manifests", default=[], action="append")
  op.add_option("-a", "--AMO",       default=False,   help="build AMO version", action="store_true")
  op.add_option("-l", "--latest",    default=False,   help="create *-latest-dev.xpi", action="store_true")
  
  opts, args = op.parse_args(argv);

  outdir  = os.path.abspath(opts.outdir)
  inpdir  = os.path.abspath(opts.inpdir)
  svnbdir = os.path.abspath(os.path.join(opts.outdir, opts.builddir))
  
  cwd = os.getcwd()

  rc = 0

  if os.path.isdir(os.path.join(inpdir, ".svn")):
    print "Exporting SVN..."
    rc = os.system(SVN + ' export "%s" "%s"' % (inpdir, svnbdir))
    assert rc == 0, "SVN export failed"
  else:
    print "Copying to '%s'" % svnbdir
    shutil.copytree(inpdir, svnbdir, ignore=shutil.ignore_patterns(os.path.basename(svnbdir), ".git"));

  inpdir = svnbdir
  
  try:
    if os.path.isfile(BUILDEXIT):
      glbl = globals(); glbl.update(locals())
      execfile(BUILDEXIT, glbl, {})
    
    f = file(os.path.join(inpdir, "install.rdf")); inst = f.read(); f.close()
    m = re.search(r'em:version="'+VERPATT+'"', inst)
    if m is None:
      m = re.search(r'<em:version>'+VERPATT+'</em:version>', inst)
    assert m != None, "Version not found in install.rdf"
    ver = m.group(1) + m.group(2) + "-sm+fx"

    checks = [
      ("JavaScript", JSCHK,   [ ".js", ".jsm" ], "%s"),
    ]
    # for syntax checks only
    manifests = "-m " + os.path.join(inpdir, "chrome.manifest ") 
    if opts.manifests: manifests += "-m " + "-m ".join(opts.manifests)
    for loc in LOCALES:
      if os.path.isdir(os.path.join(inpdir, "chrome", "locale", loc)):
        checks += [ ("%s XUL" % loc,  XULLINT, [ ".xul" ], "-d %s -l %s %s %%s -- %s" % (inpdir, loc, manifests, XMLLINT_OPTS)) ]
      else:
        print "Warning: locale '%s' not found." % loc
    
    for what, cmd, exts, par in checks:
      if not what or not cmd:
        print "Syntax check omitted!"; continue

      print "checking %s Syntax" % what,
      files = []
      for ext in exts:
        for dirpat in [ "*", "chrome/*",  "chrome/*/*",  "chrome/*/*/*",
                             "modules/*", "modules/*/*", "modules/*/*/*" ]:
          files += glob.glob(os.path.join(inpdir, dirpat+ext))
      for fn in files:
        print ".", ; sys.stdout.flush()

        rc = os.system(cmd + " " + (par % fn));

        assert rc == 0, "%s Syntax check failed for '%s'!" % (what, fn)

      print; sys.stdout.flush()

    fname = os.path.join(outdir, "%s-%s-dev.xpi" % (opts.project, ver))
    if os.path.exists(fname): os.remove(fname)
    rf = " ".join([r for r in ROOT_FILES.split() if os.path.exists(os.path.join(inpdir, r))])
    # jar -C is only valid for one (the next) name
    os.chdir(inpdir)
    
    rc = os.system(JAR+' cvMf "%s" %s' % (fname, rf))
    assert rc == 0, "jar RC = %s" % rc

    print "sha1:", 
    os.system(SHA1SUM+" "+fname)
    print "Please update update.rdf and run McCoy"

    global xpidata
    
    if opts.AMO:
      print "Building for AMO..."
      famo = os.path.join(outdir, "%s-%s-amo.xpi" % (opts.project, ver))
      p = re.compile(r'\s*<em:updateURL>.*?</em:updateURL>\n', re.S)
      inst = p.sub('\n', inst)
      p = re.compile(r'\s*<em:updateKey>.*?</em:updateKey>\n', re.S)
      inst = p.sub('\n', inst)
      p = re.compile(r'<!--\s*REMOVEME:.*?-->\n', re.S)
      inst = p.sub('\n', inst)
      p = re.compile(r'(<em:version>)'+VERPATT+'(</em:version>)')
      inst = p.sub(r'\1\2\3\5', inst)
      xpi = zipfile.ZipFile(fname, "r")
      amo = zipfile.ZipFile(famo, "w")
      for item in xpi.infolist():
        xpidata = xpi.read(item.filename)
        print item.filename, item.file_size, item.external_attr
        if item.filename == "install.rdf": xpidata = inst
        if os.path.isfile(AMOEXIT): execfile(AMOEXIT, globals(), locals())
        if xpidata is not None:
          amo.writestr(item, xpidata)
      amo.close(); xpi.close()

    if opts.latest:
      shutil.copy(fname, os.path.join(outdir, "%s-latest-dev.xpi" % opts.project))

  finally:
    os.chdir(cwd)
    print "Done."
    if os.path.isdir(svnbdir):
      shutil.rmtree(svnbdir)

  return rc

if __name__ == "__main__":
  sys.exit(main())
