#!/usr/bin/python
# -*- coding: UTF-8 -*-
 
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
import traceback
 
my_sender='313548025@qq.com'    # 发件人邮箱账号
my_pass = 'ooutzpttcmkrbgce'              # 发件人邮箱密码
my_user='313548025@qq.com'      # 收件人邮箱账号，我这边发送给自己
# users = ['774137739@qq.com','14719567@qq.com','313548025@qq.com']
def mail(mfile, to_addr):
    ret=True
    try:
        # msg=MIMEText('填写邮件内容','plain','utf-8')
        msg = MIMEMultipart()
        msg['From']=formataddr(["FromRunoob",my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        # msg['To']=formataddr(["FK",my_user])              # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['To']=formataddr(["FK",to_addr])              # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject']= mfile                # 邮件的主题，也可以说是标题
         
        # 构造附件1，传送当前目录下的 test.txt 文件
        att1 = MIMEText(open(mfile, 'rb').read(), 'base64', 'utf-8')
        att1["Content-Type"] = 'application/octet-stream'
        # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
        att1["Content-Disposition"] = 'attachment; filename="%s"' % mfile
        msg.attach(att1)
        
        server=smtplib.SMTP_SSL("smtp.qq.com", 465)  # 发件人邮箱中的SMTP服务器，端口是25
        server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
        # server.sendmail(my_sender,[my_user,],msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.sendmail(my_sender,to_addr,msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
    except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
        traceback.print_exc()
        ret=False
    return ret
if __name__ == '__main__': 
    mfile = '/home/sunqi/pot/result.20190614.191059.csv'
    import sys,traceback
    try:
        mfile = sys.argv[1]
    except:
        traceback.print_exc()
        exit(1)
    ret=mail(mfile, to_addr = '313548025@qq.com')
    if ret:
        print("邮件发送成功")
    else:
        print("邮件发送失败")
