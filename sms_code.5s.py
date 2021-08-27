#!/usr/bin/env python3
#  <xbar.title>短信验证码</xbar.title>
#  <xbar.version>v0.1</xbar.version>
#  <xbar.author>juntao</xbar.author>
#  <xbar.author.github>jinuljt</xbar.author.github>
#  <xbar.desc>从iMessage中读取短信验证码，注入剪贴板。如有多条验证码，默认最后一条，可手动从菜单中选择。</xbar.desc>
#  <xbar.dependencies>python</xbar.dependencies>
#  <xbar.abouturl>https://github.com/jinuljt/xbar-plugins</xbar.abouturl>
# Variables become preferences in the app:
#
#  <xbar.var>string(VAR_INTERVAL="6"): 获取最后x秒的短信，建议 refresh时间 + 1s</xbar.var>
# 1 sqlite 读取 imessage 短信内容。获取连续的数字， 4位 or 6位
# 2 注入剪贴板
# 3 通过notification提示

import datetime
import time
import os
import re
import sqlite3
import subprocess

CHAT_DB = f"{os.environ['HOME']}/Library/Messages/chat.db"
SEARCH_PATTERN = "(验证码)"  # 验证码短信特征
CODE_PATTERN = "[0-9]{4,6}"  # 验证码特征


def get_messages():
    # 计算gap 时间
    ts = time.time()
    base_dt = datetime.datetime(2001, 1, 1, 0, 0)
    date = (ts - base_dt.timestamp() - int(os.environ['VAR_INTERVAL']))* 1000000000

    con = sqlite3.connect(CHAT_DB)
    cur = con.cursor()
    messages = []
    for row in cur.execute(f"SELECT text FROM message WHERE date >= {date}"):
        message = row[0]
        # 是否符合验证码短信特征
        if re.search(SEARCH_PATTERN, message):

            # 提取短信验证码
            m = re.search(CODE_PATTERN, message)
            if m:
                code = message[m.start():m.end()]
                messages.append(f"【{code}】 =》 {message}")

                # 注入剪贴板
                p = subprocess.Popen("pbcopy", stdin=subprocess.PIPE)
                p.communicate(code.encode())
    con.close()

    return messages


if __name__ == "__main__":
    messages = get_messages()
    if len(messages) > 0:
        print(f"📬({len(messages)})| color=red")
    else:
        print("🈳")
    print("---")

    for message in messages:
        print(f"{message} | shell=")
    
