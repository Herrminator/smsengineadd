// $Id: logutils.jsm 58 2012-06-02 11:41:32Z hhofer69@gmail.com $

"use strict";

Components.utils.import("resource://gre/modules/Services.jsm");
Components.utils.import("resource://gre/modules/FileUtils.jsm");

var EXPORTED_SYMBOLS = [ "Logging" ];

//*****************************************************************************
//* Logging
//*****************************************************************************
function CallerInfo() {
}

CallerInfo.prototype = {
  filename: null, fileName: null, sourceLine: null, lineNumber: null, columnNumber: null
}

var Logging = {
  PFX:          "synclog: ",
  CATEGORY:     "synclog",
  LOGFILE_PREF: "invalid",
  logfile:      null,
  DEBUG:        false,
  
  callerInfo: function callerInfo(level) { // should
    if (!level) level = 0;
    // see https://github.com/eriwen/javascript-stacktrace/blob/master/stacktrace.js
    var info = new CallerInfo();
    var exc  = new Error();
    info.stack = exc.stack;
    var stack = exc.stack.replace(/(?:\n@:0)?\s+$/m, '').replace(/^\(/gm, '{anonymous}(').split('\n');
    // "{anonymous}([object Object],\"refreshEngine\",[object Proxy])@chrome://gprivacy/content/gprivacy.js:134"
    if (stack.length > level+1) {
      var sinfo = stack[level+1].split('@');
      if (sinfo.length == 2) {
        info.sourceLine = sinfo[0];
        var c = sinfo[1].lastIndexOf(":");
        if (c != -1) { 
          info.filename   = info.fileName = sinfo[1].slice(0, c);
          info.lineNumber = parseInt(sinfo[1].slice(c+1));
        } else {
          info.filename   = info.fileName = sinfo[1]
          info.lineNumber = 1;
        }
      }
      else
        info.sourcLine = stack[level+1];
    }
    return info;
  },
    
  _writeFile: function(msg) {
    if (this.logname !== undefined && this.logfile == null) return; // failed before
    if (this.logfile == null) {
      try         { this.logname = Services.prefs.getCharPref(this.LOGFILE_PREF); }
      catch (exc) { this.logname = null; }
      if (!this.logname) return;
      this.logfile = new FileUtils.File(this.logname);
      if (!this.logfile) return;
    }
    try {
      let ostream = FileUtils.openFileOutputStream(this.logfile, 0x1A)
      let sstream = Components.classes["@mozilla.org/intl/converter-output-stream;1"]
                               .createInstance(Components.interfaces.nsIConverterOutputStream);
      sstream.init(ostream, "UTF-8", 0, 0);
      let logmsg = "["+new Date().toISOString()+"] "+
                   msg.toString().replace(this.PFX,"");
      sstream.writeString(logmsg+"\n"); ostream.flush();
      sstream.close();
    } catch (exc) { this.logname = null; this._logException(exc, null, false); }
  },
  
  log: function(txt) {
    Services.console.logStringMessage(this.PFX + txt);
    this._writeFile(txt);
  },
  
  _logException: function(exc, txt, toFileIfOpen) {
    txt = txt ? txt + ": " : ""
    var excLog = Components.classes["@mozilla.org/scripterror;1"]
                           .createInstance(Components.interfaces.nsIScriptError);
    excLog.init(this.PFX + txt + (exc.message || exc.toString()),
                exc.filename || exc.fileName, exc.location ? exc.location.sourceLine : null,
                exc.lineNumber || 0, exc.columnNumber || 0,
                excLog.errorFlag || 0, this.CATEGORY);
    Services.console.logMessage(excLog);
    if (toFileIfOpen) this._writeFile(excLog);
  },
  
  logException: function(exc, txt) {
    this._logException(exc, txt, true);
  },
  
  info: function(txt) { this.log(txt); },

  debug: function(txt) { if (this.DEBUG) this.log("DEBUG: "+txt); },

  warn: function(txt, showSrcInfo, stackLevel) {
    var warn = Components.classes["@mozilla.org/scripterror;1"]
                         .createInstance(Components.interfaces.nsIScriptError);
    if (stackLevel  === undefined) stackLevel  = 0;
    var info = showSrcInfo ? this.callerInfo(stackLevel+1) : new CallerInfo();
    warn.init(this.PFX + txt, info.filename, info.sourceLine, info.lineNumber, info.columnNumber,
              warn.warningFlag, this.CATEGORY);
    Services.console.logMessage(warn);
    this._writeFile(warn);
  },
  
  error: function(txt, showSrcInfo, stackLevel) {
    var err = Components.classes["@mozilla.org/scripterror;1"]
                        .createInstance(Components.interfaces.nsIScriptError);
    if (showSrcInfo === undefined) showSrcInfo = true;
    if (stackLevel  === undefined) stackLevel  = 0;
    var info = showSrcInfo ? this.callerInfo(stackLevel+1) : new CallerInfo();
    err.init(this.PFX + txt, info.filename, info.sourceLine, info.lineNumber, info.columnNumber,
             err.errorFlag, this.CATEGORY);
    Services.console.logMessage(err);
    this._writeFile(err);
  },
  
};
