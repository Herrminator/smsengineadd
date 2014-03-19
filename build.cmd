@echo off
@rem $Id: build.cmd 85 2012-03-05 16:52:14Z hhofer69@gmail.com $
if not defined JAR     set JAR=%~d0\jdk1.6.0_18\bin\jar.exe
if not defined SHA1SUM set SHA1SUM=%~d0\Develop\cygwin\bin\sha1sum.exe
if not defined XULLINT set XULLINT=python %~dp0xullint.py

rem echo.>%~dp0build.log
rem set "LOG=2>&1 | tee -a %~dp0build.log"

rem make jar output more compact ;-)
set JAVA_TOOL_OPTIONS=-Duser.language=en -Duser.country=US

call python26 "%~dp0mkinst.py" -p smsengineadd -o "%~dp0\versions" -i "%~dp0." --AMO --latest %LOG%
