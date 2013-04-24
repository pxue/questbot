#!/usr/bin/env python
import re
import sqlite3
import mechanize
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import OrderedDict
from bs4 import BeautifulSoup
import settings

conn = None
br = None

# Get quest pages and parse the result
#@catchall
def quest():

    # try to log into quest
    br.open(settings.LOGIN_URL)

    # select the login form and try to login
    br.select_form(name="login")
    br["userid"] = settings.QUEST['username']
    br["pwd"] = settings.QUEST['password']
    response = br.submit()

    # select the grades page
    br.open(settings.GRADE_URL)

    # on grades page, select the latest term
    br.select_form(name="win0")
    br.set_all_readonly(False)

    # select the latest term, you can change the number here
    # from 1 to i for which ever term you want
    br["SSR_DUMMY_RECV1$sels$0"] = ['2']

    # do not modify any thing below here
    br["DERIVED_SSTSNAV_SSTS_MAIN_GOTO$22$"] = ['9999']
    br["DERIVED_SSTSNAV_SSTS_MAIN_GOTO$70$"] = ['9999']
    br['ICAction'] = 'DERIVED_SSS_SCT_SSR_PB_GO';
    br['ICChanged'] = '-1';
    br['ICElementNum'] = '0';
    br['ICFocus'] = '';
    br['ICResubmit'] = '0';
    br['ICSaveWarningFilter'] = '0';
    br['ICType'] = 'Panel';
    br['ICXPos'] = '0';
    br['ICYPos'] = '0';
    # don't modify anything above

    # submit and get data in html format
    response = br.submit()

    parse_data(response.read())

    return True


def check_changes(course_num, course_grade):
    
    c = conn.cursor()
    # check if grades table exist, create if do not
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='grades'")
    if not c.fetchone():
        c.execute("CREATE TABLE grades (course text, grade real)")
        conn.commit()

    # table exists, check if grade changed
    print "checking", course_num
    c.execute("SELECT grade FROM grades WHERE course=?", [course_num])
    grade = c.fetchone()
    if not grade:
        # grade changed: insert into table and return true
        c.execute("INSERT INTO grades VALUES (?, ?)", [course_num, course_grade])
        conn.commit()
        return True
    elif str(grade[0]) != str(course_grade):

        # grades already in there, but changed
        c.execute("UPDATE grades SET grade=? WHERE course=?", [course_grade, course_num])
        conn.commit()
        return True

    return False


#@catchall
def parse_data(data):
    if data is None: return "Empty data"

    # soup object
    soup = BeautifulSoup(data)

    # get COURSES and Send email
    courses = soup.find_all('tr', id=re.compile("trTERM_CLASSES"))

    def smtp_service(courses, has_changes=False):

        # build html message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = settings.MESSAGE["subject"]
        msg['From'] = settings.MESSAGE["from"]
        msg['To'] = settings.MESSAGE["to"]

        html = """
            <html>
                <head></head>
                <body>
                    <table>
                        <tr>
                            <th>Course</th>
                            <th>Grade</th>
                        </tr>
        """

        # iterate through course table
        # extract course names and grades
        for course in courses:
            course_num = course.find_all('td')[0].find('a').string.strip()
            course_grade = course.find('span',
                    id=re.compile("CRSE_GRADE_OFF")).string.strip()


            course_change = False
            if course_grade != "":
                course_change = check_changes(course_num, float(course_grade))

            has_changes = course_change or has_changes

            # bold and plus size if changed
            # assign different color depending on grades:
            #  < 50 is RED
            #  50 <= x <= 70 is ORANGE 
            #  70 > is GREEN
            color = ""
            if course_grade != "":
                color = "orange"
                if float(course_grade) < 50:
                    color = "red"
                elif float(course_grade) > 70:
                    color = "green"

            if course_change:
                html += "<tr style='font-weight: bold; font-size: 18px; color: %s;'>" % color
            else:
                html += "<tr style='color: %s'>" % color

            html += """
                            <td>%s</td>
                            <td>%s</td>
                        </tr>
            """ % (course_num, course_grade or "N/A")

        html += """
                    </table>
                <body>
            </html>
        """

        if has_changes:
            msg.attach(MIMEText(html, 'html'))

            s = smtplib.SMTP(settings.SMTP["server"], settings.SMTP["port"])
            s.ehlo()
            s.starttls()
            s.login(settings.SMTP["username"], settings.SMTP["password"])

            s.sendmail(settings.ME, settings.YOU, msg.as_string())
            s.quit()

    smtp_service(courses)

    return True


if __name__ == "__main__":
    # initialize mechanize browser
    br = mechanize.Browser()

    # initialize sqlite storage
    conn = sqlite3.connect("grades.db")

    # login and parse quest pages
    response = quest()

    conn.close()
    print "Your daily digest has completed."


