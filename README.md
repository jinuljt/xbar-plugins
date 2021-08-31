# xbar-plugins


## 读取短信验证码并注入剪贴板 sms\_code.py

- 读取iMessage中的短信验证码。并将验证码注入剪贴板，Command + V 即可使用。
- 有多条情况下，最后一条在剪贴板中。可通过xbar menu查看多条验证码
- 点击xbar menu中短信既拷贝验证码到剪贴板


需赋予**xbar** Full Disk Access 权限。见下图

![](images/macosx_full_disk_access.png)

### TODO 
- 通过webhook提交短信
