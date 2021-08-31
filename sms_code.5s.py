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
#  <xbar.var>string(VAR_WEBHOOK=""): 上传短信内容到webhook</xbar.var>
#  <xbar.var>string(VAR_LATEST_ROW_ID=""): ！！！不要修改。上一次的最后一条rowid</xbar.var>


import datetime
import time
import os
import re
import sqlite3
import subprocess
import sys
import json


CHAT_DB = f"{os.environ['HOME']}/Library/Messages/chat.db"
SEARCH_PATTERN = "(验证码)"  # 验证码短信特征
CODE_PATTERN = "[0-9]{4,6}"  # 验证码特征


config_filename = f"{os.path.abspath(__file__)}.vars.json"
def read_config():
    # 读取配置文件
    data = {}
    if os.path.exists(config_filename):
        with open(config_filename) as f:
            data = json.loads(f.read())
    return data

def write_config(data):
    with open(config_filename, "w+") as f:
        f.write(json.dumps(data))


class Config:

    def __getattr__(self, attr):
        # 只有开大 plugin browser 才会重新加载 VAR_，所以每次都从文件读取
        data = read_config()
        return data.get(f'VAR_{attr}', None)

    def __setattr__(self, name, value):
        name = f"VAR_{name}"
        value = str(value)

        data = read_config()
        data[name] = value
        write_config(data)

config = Config()


def do_webhook(row):
    # TODO webhook
    _, text, is_from_me, date = row
    ts = datetime.datetime(2001, 1, 1, 0, 0, tzinfo=datetime.timezone.utc).timestamp() + date / 1000000000
    pass

def text_to_clipboard(text):
    p = subprocess.Popen("pbcopy", stdin=subprocess.PIPE)
    p.communicate(text.encode())


def get_messages():
    con = sqlite3.connect(CHAT_DB)
    cur = con.cursor()
    messages = []

    try:
        latest_row_id = int(config.LATEST_ROW_ID)
    except Exception:
        latest_row_id = 0

    if latest_row_id == 0:
        cur.execute(f"""SELECT ROWID, text, is_from_me, date
        FROM message WHERE text IS NOT NULL ORDER BY ROWID DESC LIMIT 1""")
    else:
        cur.execute(
            f"SELECT ROWID, text, is_from_me, date FROM message WHERE text IS NOT NULL AND  ROWID > ?",
            (config.LATEST_ROW_ID,)
        )

    for row in cur.fetchall():
        do_webhook(row)

        latest_row_id = row[0]
        message = row[1]
        if not message: continue

        # 是否符合验证码短信特征
        if re.search(SEARCH_PATTERN, message):

            # 提取短信验证码
            m = re.search(CODE_PATTERN, message)
            if m:
                code = message[m.start():m.end()]
                messages.append((code, message))

                # 注入剪贴板
                text_to_clipboard(code)
    config.LATEST_ROW_ID = latest_row_id
    con.close()
    return messages


if __name__ == "__main__":
    if len(sys.argv) == 1:
        messages = get_messages()
        if len(messages) > 0:
            print(f"📬({len(messages)})| color=red")
        else:
            print("🈳")
        print("---")
        for code, message in messages:
            print(f"{code} =》 {message} | shell=\"{sys.argv[0]}\" param1={code}")
    else:
        text_to_clipboard(sys.argv[1])