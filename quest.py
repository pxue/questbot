#!/usr/bin/env python
import re
import mechanize
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import OrderedDict
from bs4 import BeautifulSoup
import settings


def catchall(func):
    def dec(*args):
        try:
            func(*args)
        except Exception, e:
            print "Ops, something went wrong! %d: %s" % (e.code, e.msg)
            raise e
    return dec


# Get quest pages and parse the result
@catchall
def quest(br):

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
    br["SSR_DUMMY_RECV1$sels$0"] = ['0']

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

@catchall
def parse_data(data):
    if data is None: return "Empty data"

    # soup object
    soup = BeautifulSoup(data)

    # get COURSES and Send email
    courses = soup.find_all('tr', id=re.compile("trTERM_CLASSES"))

    def smtp_service(courses):

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

            html += """
                        <tr>
                            <td>%s</td>
                            <td>%s</td>
                        </tr>
            """ % (course_num, course_grade or "N/A")

        html += """
                    </table>
                <body>
            </html>
        """

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
    br = mechanize.Browser()

    # login and parse quest pages
    response = quest(br)

    print "Your daily digest has completed."


