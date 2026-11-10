# 反馈

用户在语阅里写下的反馈，加密后发到公共的 [ntfy.sh](https://ntfy.sh)，由 GitHub Actions 收进私有仓库的 Issue，Mac 开机后再导入本机的 Kaneo。不自建服务器，不花钱。Mac 关机也不影响反馈先被收下：ntfy 和 GitHub 都在云上，Kaneo 只在电脑开着的时候补上。

## 为什么是这条路

- 用户在大陆。ntfy.sh 的 HTTPS 在几家主要运营商上能通，免费档大约每个 IP 每天 250 条，消息大约留 12 小时。
- 没有邮箱、没有 Gitee、没有 Kaneo Cloud、没有 Cloudflare 或国内云。
- 语阅仓库是公开的（GPL-3.0）。谁知道话题地址，谁都能订阅，所以反馈不能明文发。
- App 用接收方的公钥做 libsodium sealed box（`crypto_box_seal`，X25519）。私钥只放在 GitHub Actions 的 secret 里。订阅话题的人只能看到密文。
- 加密写在 Rust core（`core/yuyue-core/src/feedback.rs` 的 `seal_feedback`）。界面还没进 App：样子在 [`docs/dev/feedback-prototype/index.html`](feedback-prototype/index.html)，你点头之后再接到 SwiftUI 和 Compose。各端的发送和「没网先留在本机」也等界面定了再接，不跟界面稿混在一起。

## 进 Kaneo 的做法

用本机脚本读 GitHub Issue，再调用 Kaneo 的「创建任务」。

不用 Kaneo 文档里的「Import GitHub issues」。那条接口本身是幂等的（已有任务会更新），但要用它，得先给自建 Kaneo 配一个 GitHub App。App 的实时同步要求一个公网 Webhook（`https://…/api/github-integration/webhook`）。这台 Mac 没有公网地址。

脚本每次跑都会看 Kaneo 里已有任务的描述。第一行是 `yuyue-feedback-issue:<编号>` 的，跳过。所以重复运行不会造出两张一样的任务。删掉某张任务之后，下次会再导入那一条。

## 隐私

不点「发送」，什么都不会离开这台设备。发出去的只有这段话、可选的联系方式、应用版本、平台和系统版本。不带书、笔记，也没有能认出这台设备的信息。

客户端限制：正文最多 800 字，联系方式最多 80 字，24 小时最多 5 条。超长或解不开的消息，中转脚本直接跳过。

没网时，这条已经加密的内容留在本机，下次打开语阅会再试。在发出去之前不用再点一次。

## 你要做的事

下面假设私有仓库叫 `wtino/yuyue-feedback`，Kaneo 开在本机。路径按你的机器改。

### 1. 私有仓库

在 GitHub 新建一个 **Private** 仓库，例如 `wtino/yuyue-feedback`。把本仓库的 `feedback/relay/` 原样放进去，路径保持 `feedback/relay/`。把 `feedback/relay/relay.yml` 复制成私有仓库的 `.github/workflows/relay.yml`。

不要把这份工作流放进公开的语阅仓库。

到仓库的 Settings → Actions → General，允许 GitHub Actions。

### 2. 生成密钥和话题

在能装 Python 包的机器上：

```sh
python3 -m pip install --user -r feedback/relay/requirements.txt
python3 feedback/relay/keygen.py
```

会打出三行：

- `NTFY_TOPIC`：难猜的话题名
- `FEEDBACK_PRIVATE_KEY`：私钥
- `YUYUE_FEEDBACK_PUBLIC_KEY`：公钥

私钥只放进 GitHub。话题不要提交到公开仓库：知道话题的人虽然读不到内容，但可以往里面灌垃圾，占掉每天大约 250 条的额度。公钥可以放进构建配置，它本来就是公开的。

### 3. GitHub secrets

私有仓库 → Settings → Secrets and variables → Actions → New repository secret：

| 名字 | 值 |
| --- | --- |
| `NTFY_TOPIC` | 上面的话题 |
| `FEEDBACK_PRIVATE_KEY` | 上面的私钥 |

工作流用自带的 `GITHUB_TOKEN` 开 Issue，不用再做一个 token 给 Actions。它只有 `issues: write`。

到 Actions 页，选「转发反馈」，Run workflow，手动跑一次。没有新反馈时，日志里应是「新开 0」。失败多半是 secret 名字拼错，或 Actions 没打开。

定时是每小时第 17 分（`17 * * * *`）。一次设了 3 分钟上限，平常不到一分钟，一个月远低于私有仓库 2000 分钟的免费额度。ntfy 只留大约 12 小时，间隔不要改得比这更稀。想再省分钟，把 cron 改成 `17 */3 * * *`。

### 4. 配进 App

Apple，在 `apple/Config/` 把 `Feedback.local.xcconfig.example` 复制成 `Feedback.local.xcconfig`（这个文件被 git 忽略）：

```
YUYUE_FEEDBACK_TOPIC = 上面的话题
YUYUE_FEEDBACK_PUBLIC_KEY = 上面的公钥
```

然后在 `apple/` 里重新 `xcodegen`，让这两项进 Info.plist。

Android，在 `android/` 把 `feedback.properties.example` 复制成 `feedback.properties`（同样被忽略）：

```
topic=上面的话题
publicKey=上面的公钥
```

没配的构建里，反馈页会写「这个版本还没接上反馈」，发送按钮不可用。

### 5. 编译

加密在 core 里，两端都要先重新编 core，再编 App：

```sh
apple/build-core.sh
cd apple && xcodegen

android/build-core.sh
cd android && ./gradlew assembleDebug
```

### 6. Kaneo

1. 在 Kaneo 里建一个项目，用来收反馈。打开项目，从地址栏抄下项目 ID，填到 `KANEO_PROJECT_ID`。
2. Kaneo → 设置 → 账户 → API Keys，新建一把钥匙。它要能读这个项目、创建任务。钥匙只显示一次。
3. `KANEO_BASE` 是你在浏览器里打开的地址，后面加 `/api`。例如 Kaneo 开在 `http://127.0.0.1:8000`，就写 `http://127.0.0.1:8000/api`。
4. 不填 `KANEO_STATUS` 时，任务放进第一列还没完成的列。想指定的话，填那一列的 slug。

GitHub 上再做一只 **fine-grained token**，只给 `wtino/yuyue-feedback`，权限只要 Issues 的 Read。这只 token 留在 Mac 上，不放进 Actions。

### 7. Mac 上的导入

```sh
mkdir -p ~/.config/yuyue
chmod 700 ~/.config/yuyue
cat > ~/.config/yuyue/feedback.env << 'EOF'
GITHUB_TOKEN=上面的细粒度 token
GITHUB_REPO=wtino/yuyue-feedback
KANEO_BASE=http://127.0.0.1:8000/api
KANEO_API_KEY=Kaneo 的钥匙
KANEO_PROJECT_ID=项目 ID
EOF
chmod 600 ~/.config/yuyue/feedback.env
```

先试跑，不写入：

```sh
python3 /path/to/yuyue-feedback/feedback/relay/kaneo_import.py --dry-run
```

确认会导入哪些条，再去掉 `--dry-run`。

登录后每小时跑一次：把 `feedback/relay/com.yuyue.feedback-kaneo.plist.example` 复制到 `~/Library/LaunchAgents/app.yuyue.feedback-kaneo.plist`，改掉里面的 Python 和脚本路径（`which python3`）。macOS 不一定有 `/usr/bin/python3`。

```sh
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/app.yuyue.feedback-kaneo.plist
```

日志在 `/tmp/yuyue-feedback-kaneo.log`。电脑关机的那段时间，Issue 先留在 GitHub，下次开机再进 Kaneo。

### 8. 对一下

App 里还没有发送按钮。要先打通中转，可以用 `keygen.py` 的公钥在本机封一条 `v1.` 开头的 sealed box，POST 到 `https://ntfy.sh/<话题>`，再手动跑一次工作流。私有仓库里应出现一个 Issue，正文第一行是 `<!-- ntfy-id: … -->`。再跑导入脚本，Kaneo 里出现一张任务，描述以 `yuyue-feedback-issue:` 开头。再跑一次，不应该多出一张。

界面进 App 之后，用真机发一条，走同一条路。

## 提议的入口（原型，还没进 App）

早期希望反馈在主界面上就看得见，不藏在设置深处。稿在 [`docs/dev/feedback-prototype/index.html`](feedback-prototype/index.html)。定稿后再写进 SwiftUI / Compose，并用一个开关以后收起来。

稿里的摆法：

- iPhone / iPad：每个主标签底部、标签栏上方有一颗「反馈」。阅读是盖在上面的全屏页，这颗按钮不压在书页上。阅读页只在顶栏出现时放一个气泡。
- Android：标签栏上方同样有一颗「反馈」。阅读顶栏里放按钮，顶栏收起时按钮一起收起。
- Mac 书架：标题旁边一颗，侧栏底部一颗。读书窗口的工具栏里一颗，不浮在书页上。菜单栏「帮助」里有「给语阅反馈…」。
- 第一次打开书架，标题下面有一张不挡操作的卡片。可以去反馈，也可以点「知道了」。只出现一次。
- 「我的」和 Mac「设置」里始终有「反馈」，开关关掉之后也还在，和帮助菜单一样。

## 限制

- ntfy.sh 大约每 IP 每天 250 条，消息大约留 12 小时。工作流停太久，中间的反馈会丢。
- 正文上限是为了塞进 ntfy 的大约 4096 字节。中文按 800 字留了余量。
- 公开构建如果没配话题和公钥，反馈页在，但发不出去。
