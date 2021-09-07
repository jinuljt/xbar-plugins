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
#  <xbar.var>string(VAR_SEARCH_PATTERN="验证码,动态码"): 关键词，用于判断是否为短信。</xbar.var>
#  <xbar.var>number(VAR_LATEST_ROW_ID=""): ！！！不要修改。新消息ROW ID</xbar.var>


import datetime
import os
import re
import sqlite3
import subprocess
import sys
import json
import urllib
import urllib.request


CHAT_DB = f"{os.environ['HOME']}/Library/Messages/chat.db"
CODE_PATTERN = "[0-9]{4,6}"
RETAIN_COUNT = 10  # 保留显示最后n条短信
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
        # 只有打开 plugin browser 才会重新加载 VAR_，所以每次都从文件读取
        data = read_config()

        attr = f'VAR_{attr}'
        return data.get(attr, os.environ.get(attr, None))

    def __setattr__(self, name, value):
        name = f"VAR_{name}"
        value = value

        data = read_config()
        data[name] = value
        write_config(data)

config = Config()


def do_webhook(row):
    if not config.WEBHOOK:
        return ""

    data = {
        "message": row[1],
        "category": 'Send' if row[2] == '1' else 'Received',
        "timestamp": datetime.datetime(2001, 1, 1, 0, 0, tzinfo=datetime.timezone.utc).timestamp() + \
            int(row[3]) / 1000000000,
        "phone": row[4]
    }

    req = urllib.request.Request(
        url=config.WEBHOOK,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return ""
    except Exception as e:
        return f"post to {config.WEBHOOK} {data} fail due to {e}"


def text_to_clipboard(text):
    p = subprocess.Popen("pbcopy", stdin=subprocess.PIPE)
    p.communicate(text.encode())


def fetch_rows(latest_row_id):
    con = sqlite3.connect(CHAT_DB)
    cur = con.cursor()

    if latest_row_id == 0:
        cur.execute(f"""SELECT m.ROWID, m.text, m.is_from_me, m.date, c.chat_identifier
        FROM message  as m, chat_message_join as cmj, chat as c
        WHERE m.ROWID = cmj.message_id AND c.ROWID = cmj.chat_id AND m.text IS NOT NULL
        ORDER BY m.ROWID DESC LIMIT 1""")
        rows = cur.fetchall()
    else:
        cur.execute(
            f"""SELECT m.ROWID, m.text, m.is_from_me, m.date, c.chat_identifier
            FROM message  as m, chat_message_join as cmj, chat as c
            WHERE m.ROWID = cmj.message_id AND c.ROWID = cmj.chat_id AND m.text IS NOT NULL AND m.ROWID > ?""",
            (latest_row_id,)
        )
        rows = cur.fetchall()
    con.close()
    return rows

def get_messages():
    code_messages = []
    common_messages = []

    latest_row_id = max((config.LATEST_ROW_ID or 0) - RETAIN_COUNT, 0)
    rows = fetch_rows(latest_row_id)

    for idx, row in enumerate(rows, 1):
        if idx > RETAIN_COUNT:
            error = do_webhook(row)
            if error: common_messages.append(("error", error))

        config.LATEST_ROW_ID = row[0]
        # 是否符合验证码短信特征
        text = row[1]
        if re.search(f"({'|'.join(config.SEARCH_PATTERN.split(','))})", text):
            # 提取短信验证码
            m = re.search(CODE_PATTERN, text)
            if m:
                code = text[m.start():m.end()]
                code_messages.append((code, text))

                # 注入剪贴板
                if idx > RETAIN_COUNT:
                    text_to_clipboard(code)

                continue
        common_messages.append(("", text))
    return code_messages, common_messages


if __name__ == "__main__":
    if len(sys.argv) == 1:
        code_messages, common_messages = get_messages()
        if len(code_messages):
            print(f"📬({len(code_messages)})| color=red")
        else:
            print("🈳")
        print("---")
        for code, message in code_messages + common_messages:
            print(f"{code} =》 {message} | shell=\"{sys.argv[0]}\" param1={code}")
    else:
        text_to_clipboard(sys.argv[1])
