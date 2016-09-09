import coloredlogs
import os
import smtplib
import logging

from logging.handlers import SMTPHandler
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

import common


class SSLSMTPHandler(SMTPHandler):
    def _format_addr(self, s):
        name, addr = parseaddr(s)
        return formataddr((
            Header(name, 'utf-8').encode(),
            addr.encode('utf-8') if isinstance(addr, unicode) else addr))

    def emit(self, record):
        '''
        Emit a record.
        '''
        try:
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP_SSL(self.mailhost, port, timeout=self._timeout)
            msg = self.format(record)
            msg = MIMEText(msg, 'plain', 'utf-8')
            msg['From'] = self._format_addr(u'PSTest Robot <%s>'
                                            % self.fromaddr)
            msg['To'] = self._format_addr(",".join(self.toaddrs))
            msg['Subject'] = Header(u'%s' %
                                    self.getSubject(record), 'utf-8').encode()

            if self.username:
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg.as_string())
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


os.environ['COLOREDLOGS_LOG_FORMAT'] = \
        '[%(hostname)s] %(asctime)s - %(name)s[%(process)d] - ' \
        '%(filename)s[line:%(lineno)d] - %(levelname)-8s: %(message)s'
coloredlogs.install(level='DEBUG')
logger = logging.getLogger()

mailuser = os.environ.get('PST_MAIL_USER', None)
mailpasswd = os.environ.get('PST_MAIL_PASSWD', None)
smtpserver = os.environ.get('PST_MAIL_SMTP', None)
smtpport = os.environ.get('PST_MAIL_PORT', 465)
toaddrs = os.environ.get('PST_MAIL_TOADDRS', None)
subject = os.environ.get('PST_MAIL_SUBJECT', u"[PST][log]")

if mailuser and mailpasswd and smtpserver:
    hostname = common.get_hostname()
    rootfs = common.get_rootfs()
    commit = common.get_commit()
    if common.is_in_vm():
        tbox_type = 'vm'
    elif common.is_in_docker():
        tbox_type = 'docker'
    else:
        tbox_type = 'pm'
    subject_suffix = ' %s  %s  %s  %s' % (hostname, tbox_type, rootfs, commit)
    mail_handler = SSLSMTPHandler(mailhost=(smtpserver, int(smtpport)),
                                  fromaddr=mailuser,
                                  toaddrs=toaddrs,
                                  subject=subject+subject_suffix,
                                  credentials=(mailuser, mailpasswd))

    mail_handler.setLevel(logging.ERROR)
    logger.addHandler(mail_handler)
