Make sure you go through settings file and setup your email and quest stuff.
Currently by default I use gmail smtp, but you can change it to anything.

I included mechanize package because there's a bug with it that I had to patch.
The fix is in the file called "urllib2_fork" and the class "HTTPSConnectionV3"

for requirements, just pip -r install requirements.txt
and make sure you have sqlite3

HOW TO RUN:

1. make a shell script file (make sure the chmod +x it)
2. open up crontab (crontab -e)
3. add your shell script file
4. ???
5. profit!

if you need a refresher on how crons work, this is a [good link](http://kvz.io/blog/2007/07/29/schedule-tasks-on-linux-using-crontab/)

Have fun!
