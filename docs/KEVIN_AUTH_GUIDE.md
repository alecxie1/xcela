# 开启登录功能 - 给 Kevin 的操作指南（feature 021）

> Paste-able message for Kevin's team (their CTO runs the commands on their server).
> Context: Kevin asked for a login page, whitelisted users, per-user isolation of brands
> and runs, and a super user who sees everything. Auth ships OFF: nothing changes until
> the commands below are run. Written 2026-07-14.

---

登录功能已经上线，但默认是**关闭**的：不做任何操作，系统和现在完全一样。
想开启登录，请在服务器上执行以下步骤（每位队友一个账号，外加一个管理员账号）：

## 1. 更新代码并创建账号

```bash
cd /opt/xcela/handyprint-design-tool     # 你们的部署目录
sudo -u xcela git pull

# 创建管理员（super，能看到并管理所有人的品牌和任务）——只建一个：
sudo -u xcela .venv/bin/python frontend/auth.py add kevin --super

# 为每位设计师创建普通账号（会提示输入两次密码）：
sudo -u xcela .venv/bin/python frontend/auth.py add xiaowang
sudo -u xcela .venv/bin/python frontend/auth.py add xiaoli

# 重启服务，登录才会生效：
sudo systemctl restart xcela
```

## 2. 日常账号管理（都是这一个命令）

```bash
.venv/bin/python frontend/auth.py list            # 查看所有账号
.venv/bin/python frontend/auth.py add <名字>       # 新增账号；对已有名字执行 = 重设密码
.venv/bin/python frontend/auth.py remove <名字>    # 删除账号（其登录立即失效）
```

- 忘记密码：没有自助找回，管理员重新 `add` 一次同名账号即可（就是重设密码）。
- 删除**最后一个**账号时，登录功能自动关闭（回到开放模式），不会把所有人锁在外面。
- 想彻底关闭登录：删掉服务器上的 `users.json` 文件，重启服务即可。

## 3. 权限模型（开启后的行为）

- 每个人登录后，只能看到**自己录入的品牌**和**自己发起的任务**，
  以及所有**未认领的共享内容**。
- **开启登录之前**的历史品牌和任务没有所有者，属于共享内容：全团队照常可见、可用，
  什么都不会丢。
- 管理员（super）能看到并管理全部内容，还可以在「品牌管理」页给品牌指定所有者
  （把某个共享品牌划给某位设计师）。
- 会话有效期 30 天；服务器重启不会把大家登出。

有问题随时找我们。
