# 语阅 · 发布前测试 BUG 清单（第一至七轮，共 20 条）

测试范围：核心 Rust 测试（151 通过 / 4 按设计跳过）、iPhone 模拟器（iOS 27.2）、Mac 端（macOS 云端构建机）、Android 模拟器（Pixel 9 API 37）。
测试人：Ato（@product）。日期：2026-11-11。
状态符号：待复测 / 已确认 / 待确认 / 已修 / 环境受限。

---

## 发布前建议必修（3 项）
1. **#1【严重·iOS】搜索页没有搜索框**：底部“搜索”页只有标题，无法输入查询。
2. **#18【中·Android】点词弹窗“加入生词表”不保存**：点击“Add to Word List”后弹窗关闭，但生词页始终为空，重启后仍空。
3. **#9【中·Android】朗读声表声音名被截断**：Read Aloud 页每行声音名只显示到 `"English (United"`，无省略号，多行声音无法区分。

（注：原第 10 号“点词词典为空”已修复并实测通过。）

---

## BUG 明细（按轮次 / 编号）

### 第二轮（iPhone 界面走查，iOS 27.2）
1. 【严重·待复测】搜索页没有搜索框：底部“搜索”页只有标题，无法输入查询。怀疑自定义标签容器里 searchable 搜索框没有渲染。复现：启动 → 底部搜索标签。截图 `shots/11-search-empty.png`
2. 【中·已确认】Engine 页 `"Add Provider…"` 弹出菜单为空：没有任何服务商、设备不支持 Apple Intelligence 时，点开下拉菜单没有任何可选项（空白胶囊）。绕过：Manage Providers → Add Provider。截图 `shots/04-add-provider.png`
3. 【低·已确认】英文界面混入未翻译中文：Add Provider 表单占位文本 `"Search providers, e.g. Qwen, Kimi, magpie"`，其下 `"Add Your Own 任何 OpenAI 兼容接口"` 中英混排。截图 `shots/06-add-sheet.png`
4. 【低·未复现】一次前台使用中应用整体退出到主屏：点外观页 Tea Brown 主题色后应用消失回主屏；重启后正常，复测同一操作未再现，持续观察。
5. 【低·已确认】Apple Intelligence 文案：Engine 页 Test 行显示 `"Apple Intelligence is still downloading its model. Try again in a while"`——在不支持的设备/模拟器上永远下载不完，建议按可用性区分文案。截图 `shots/25-engine-test.png`

### 第三轮（Mac 端数据流）
6. 【中·未稳定复现】打开《红楼梦》曾出现阅读器窗口空白：只有工具条，无正文无返回按钮，超过 1 分钟不渲染；后续用精确坐标重试在 8 秒内正常渲染第一回。可能与首次解析大 EPUB 有关，发布前建议真机留意大书首开。
7. 【低·已确认】词甘误触发：英文书里 `"Chap 34"`（Chapter 缩写）中的 `Chap` 被当成单词注释为“小伙子”。
8. 【低·环境受限】选词后翻译语言下载面板的 Download 按钮置灰（云端 Mac 无法下载翻译模型），翻译功能本身未验证，需真机复测。

### 第四轮（Android 全界面，Pixel 9 模拟器 API 37）
9. 【中·已确认】朗读声表声音名被截断：Read Aloud 页每行声音名只显示到 `"English (United"`，无省略号，多行声音无法区分。复现：Me → Read Aloud。截图 `shots-a/a05-Read_Aloud.png`
10. 【已修】点词词典为空：原构建脚本拉取了 ECDICT 仓库的 mini 示例表（53 行），已改拉完整 `ecdict.csv`（66MB，打包 9 万行）并加入平台缓存。已在 Pixel 9 模拟器推英文书实测：词甘注释正常显示，点词弹窗音标、中文释义、原句上下文、朗读按钮均正常。
11. 【低·已确认】英文文案错误：划词菜单里朗读按钮显示 `"Read from"`，应为 `"Read Aloud"`。截图 `shots-a/a24-select.png`
12. 【低·已确认】Snapshots 页文案指代不通：`"Use it to move to a new phone, or to Android."` 是 iOS 文案，Android 版上应改为移去 iPhone / 新设备。截图 `shots-a/a05-Appearance.png`
13. 【低·已确认】远程书库卡片副标题 `"Calibre、NAS"` 中文顿号混在英文界面（与 iOS #3 同类混排问题）。截图 `shots-a/a01-home.png`
14. 【低·待确认】Sync 页设备名显示原始型号串 `"This sdk_gphone64_x86_64"`（模拟器的型号即为该串，真机应显示真实型号，低风险）。截图 `shots-a/a05-Sync.png`
15. 【留意】阅读器首次打开空白约 2～3 秒（仅模拟器首次打开，第二次打开即时；与 Mac #6 大书首开空白同类，真机留意）。截图 `shots-a/a12-reader.png`

### 第五轮（Mac 数据页快照闭环）
16. 【低·已确认】生成快照后右侧“上次快照”栏不刷新：仍显示“还没生成过”，但列表中其实已生成。真机大概率也会出现。
17. 【低·已确认】导入快照弹窗里 Import 按钮置灰样式下仍可点击执行，视觉样式与实际可点状态不一致。

### 第六轮（Android 词典与笔记闭环）
18. 【中·已确认】点词弹窗“加入生词表”（Add to Word List）按钮点击不生效：弹窗正常关闭，但生词页始终为空，重启应用后再查仍为空。界面检查确认点击命中按钮本体，连试两次均无效，日志无报错。
19. 【低·已确认】搜索结果卡片里书名重复显示两遍（如 `"The Catch of the Day · The Catch of the Day"`）。

### 第七轮（Mac 书架走查）
20. 【已排除】新建合集输入名字回车关闭后，合集列表仍是空的：第八至十轮复测确认这是自动化输入未进弹窗输入框造成的（名字真正输入后回车，合集立即创建并显示）。应用本身无问题。
- 另记：右键书卡的上下文菜单两次模拟点击均未弹出（可能是自动化点击工具限制，真机人工验证）。

---

## 各轮已验证通过项汇总
- **核心 Rust 测试**：151 通过，4 按设计跳过，0 失败。
- **iPhone 界面**：启动与空态、Me 页全子页（Sync / Library Sources / Wi-Fi Transfer / Appearance / Focus Reading / E-ink / Languages / Read Aloud / Engine / Storage / Snapshots / Note Export / About）、四套新主题色即时切换与深色模式、AI 服务商列表与空 Key 校验均正常。
- **Mac 数据流与快照**：中文 EPUB（《红楼梦》）、GBK 中文 TXT（《背影》）、英文 EPUB（《傲慢与偏见》）正确入库；双页排版、翻页、目录、书内查找、全局搜索 ⌘K、中文选词菜单、GBK 解码、词甘注释正常；生成快照（5 个开关）、导入快照全闭环（预览弹窗、Merge/Replace 动态计数、Replace 前自动备份）、Goodreads/StoryGraph 历史导出 CSV 正常；书架排序（4 项）、状态筛选正常。
- **Android 界面与闭环**：四个底部页签（书架/笔记/我的/搜索）、搜索框、中文 EPUB 与 GBK TXT 导入、阅读器翻页/进度/排版面板、划线四色高亮与笔记保存、选词加想法与笔记保存、英中文全文搜索高亮、词甘与点词查词弹窗、深色模式均正常。

## 需真机复测清单（模拟器/云端环境受限）
1. Wi-Fi 传书实际传输（模拟器为内网 NAT）
2. 朗读实际发音、翻译语言包下载与翻译结果
3. 有声书播放与音文对齐界面（无音频夹具）
4. iPhone 真机从文件导入（iOS 模拟器无法直接放入测试书）
5. Mac/Android 大书首次打开加载表现（#6 / #15）及 Mac 书卡右键菜单

---

## 第八至十轮夜间复测（2026-11-13，代码未变，HEAD ae23508）

### 必修项结果
- **#18 Android 加入生词表：已修，实测通过。** 点词弹窗加入后生词表立即显示（含词性、音标、释义、原句上下文、出现次数），重启应用后仍在。
- **#1 iOS 搜索页无搜索框：仍在。** 搜索页只有标题，无任何输入框。
- **#9 Android 朗读声音名截断：仍在。** 30 个英文声音每行都只显示到 "English (United"。

### 仍在的老问题（复测确认）
- #2 iOS Add Provider 弹出菜单仍为空；#3 iOS 加服务商表单中英混排仍在（"Add Your Own 任何 OpenAI 兼容接口"）。
- #5 iOS Apple Intelligence 永远"还在下载"文案仍在。
- #7 Android 词甘仍把 "Chap 34" 的 Chap 注释为“小伙子”。
- #11 Android 划词菜单仍显示 "Read from"。
- #12 Android Snapshots 页仍写 "move to a new phone, or to Android"（另见 Sync 页 "Choose the same way on your iPhone and Mac"）。
- #13 Android 远程书库副标题 "Calibre、NAS" 中英混排仍在。
- #14 设备名原始串仍在：Android 显示 "This sdk_gphone64_x86_64"（iPhone 正常显示名字）。
- #16 Mac 上次快照栏不刷新：已二次确认。生成快照后 Earlier snapshots 列表立即出现（11/13 18:32 · 347 bytes），右侧“上次快照”仍显示“还没生成过”。
- #19 Android 搜索结果卡：未见书名重复两遍，本次显示为书名 · 章节，待定。
- #20 Mac 新建合集：已排除。先点入输入框再输入 "Night Test" 回车，合集立即创建（0 books · Today），侧栏计数变 1。第七轮的失败是自动化输入没进输入框，非应用问题。

### 新发现
21. 【低·iOS·已确认】点主题色偶发退出到主屏：点外观页 Tea Brown 后应用退出到主屏（本轮又出现一次；第二次复测正常），#4 同源，仍不稳定。
22. 【低·iOS·已确认】同步页英文界面混入中文条目“有声书录音”；同页 "Not Uploaded To Icloud" 拼写错误（应为 iCloud）。
23. 【低·Android·已确认】朗读弹窗的睡前定时器标签截断：两处只显示 "End of"。
24. 【低·Mac·待确认】快照时间显示与系统时间制式不一致（Earlier snapshots 显示 "11/13 18:32"，系统时间 4:32 PM），可能只是 24 小时制格式，真机留意。

### 新验证通过项
- Android 快照创建后 Earlier snapshots 列表立即刷新（Mac #16 的问题 Android 上不存在）。
- Android 新主题色四套名字生效；iOS Appearance 页新主题名（Pine Green / Tea Brown / Moss Green / Dusk Violet）生效，新增 Liquid Glass 开关。
- Android 生词表页今天分组、来源书、复习卡结构正常。
- iPhone/Android About 页版本号 0.1.0(1)、反馈入口（Email the developer）正常。

### 环境限制（本轮仍无法测）
- iPhone Wi-Fi 传书：模拟器地址 192.168.2.2:8080 从沙盒不可达，网关不转发应用端口，留真机。

## 第十一轮（2026-11-14 凌晨，重装后全页走查，HEAD 2a111d1，代码未变）

模拟器被平台回收后重出包（iOS c9c0f82a / Android 7d2ab562），全新安装重测。

### iOS 空库与新页验证通过
- 首启动空书架引导页正常（Import from Files / Wi-Fi Transfer / Remote Libraries 三入口）。
- Wi-Fi Transfer 页：地址显示、Copy 按钮、浏览器示意均正常（实传仍留真机）。
- Library Sources 列表 + Add Library 表单（OPDS/WebDAV 分段、占位符、未填时 Connect and Save 置灰）正常。
- Storage 页：用量、Recently deleted 区、Clear Now 置灰正常。
- Snapshots 页：Create/Import Snapshot、导出阅读历史入口正常。
- Note Export 页：Obsidian/Notion/flomo 三组表单与说明正常。
- Engine 页：Companion Provider 下拉、Manage Providers、System voices / System Translation 选中态、Saved Answers 清除置灰正常；Apple Intelligence 提示文案正确。
- Read Aloud 设置页：速度滑杆、中文 2 声音 / 英文 16 声音分组正常。
- Notes 空态（All/Thoughts/Words + By time/By book 筛选）正常。

### 新发现（小问题）
- #25 iOS Snapshots 页 "Export Reading History" 行文字截断（"Export Reading Hi…" / "Goodreads、Story…"），且英文文案里出现全角顿号"、"（Goodreads、StoryGraph），与其他页面的英文逗号不一致。截断与 #9/#23 同类。
- #26 iOS Engine 页 Companion 状态提示 "Apple Intelligence is still downloading its model." 也被截断（"downloa…"），同 #25 一类。

### 待测（书导入后）
- iOS 有书后的搜索页（空库时搜索页只有标题，无输入框也无空态提示，待有书后确认是否恢复输入框）；Android 导入 → 阅读器内划词/翻译/朗读/睡前定时器回归。

## 第十二轮（2026-11-14 凌晨，Android 全链路带书回归，build 7d2ab562，HEAD 2a111d1）

### 验证通过
- 系统文件选择器导入《Pride and Prejudice》成功，书架即时显示、状态标签正常。
- 阅读器：深色纸即时切换、词条音注（悬求/药剂师）、四色高亮含词纹、选中菜单（想法/朗读起点/问/翻译/拷贝/分享）、朗读卡拉OK下划线逐句推进、切页签后底部迷你播放条继续播、Notes 页高亮即时入库 + Today's Review 卡。深色模式下 Me/Sync/阅读统计/Library Sources/E-ink/排版面板均正常，Android Sync 页干净（iOS #22 混入问题 Android 没有）。
- 空库引导页、导入页、搜索/笔记空态正常。

### 仍问题
- #9 复确认：Android 朗读声音行整行只显示 "English (United"，声音名完全没显示（本次为全新安装重装后）。
- 新发现 #27【中】阅读器选中文本点"翻译"：只弹出词头读音条（黄字词 + 播放/暂停），无任何翻译内容，读音结束自动收起。离线翻译引擎显示可用。复现：长按词 → Translate。需确认词典/翻译面板数据流。
- 新发现 #28【低】空库引导页 Remote 卡文案 "Calibre、 NAS"（全角顿号+多余空格）；Wi-Fi Transfer 卡副标题 "Send from a computer's" 被裁（无省略号）。
- 新发现 #29【低】排版面板纸质主题 chip 截断："Paper ·"、"Lette"（无省略号），行距 "Medium line spacing" chip 文字贴边裁切。
- #25 同源：iOS Snapshots "Export Reading History" 行截断 + "Goodreads、StoryGraph" 全角顿号；Engine 页 Apple Intelligence 提示截断。
- 观察项：空库时搜索页只有标题无输入框（待有书确认）；预览示例句拼接生硬（"acknowledged,Heaven always leaves a way out!"），双语混排无空格。

## 第十三轮（2026-11-14，iPhone Duo 三态加测，iOS build 1a3eb247 / Android 26975d5c，HEAD 8969ba0）
- 无新代码提交（HEAD 8969ba0 全是测试文档），双平台重新打包并装机启动正常。
- iPhone Duo：展开全屏、半折、合盖外屏三态自适应正常；半折时内容横排 + 右侧页签栏可用；合盖外屏布局正常。
- 新发现（#28 同类，低）：Duo 半折态下卡片副标题同样省略号截断。
- 测试注：折叠姿态截图默认旋转，用 screenshot --upright 输出正立图（点按坐标仍按普通截图计）。

## 第十四轮（2026-11-14 下午，Android 带书回归 + 设置页走查，build 7ba2257b，HEAD 8969ba0 无新提交）
### 验证通过
- 模拟器被回收后 APK 重装、书重新推送（base64 分块 561102 字节校验一致）、系统选择器再次导入成功，书架即时显示（Continue + Listening 角标、进度 4%）。
- 目录面板：Contents / Bookmarks / Notes 页签、每章阅读/听书时长估算正常；点 Chapter I 跳转成功，返回原位置的浮层正常。
- 排版面板字号滑杆增大后正文即时重排，页码/进度同步。
- 朗读：播放/暂停、卡拉OK下划线逐句推进、点进度条跳句正常。
- Me 各子页全走查：Languages（MDict 导入、CET-6 词条预览正常）、Read Aloud（速度滑杆、17 个英文声音 + Premium 标签、Cloud Voices 三组 Key 输入）、Storage（4.2 MB 用量/8 GB 可用分布正常）、Snapshots（新建快照成功，1.1 kB，分享/导出/删除按钮在）、Note Export（Obsidian/Notion/flomo 三组表单与说明完整）、Engine（Companion Add Provider / System voices / 系统翻译三区正常）、Focus Reading（六个开关分组与免打扰提示正常）。

### 仍问题 / 新发现
- #9 复确认：Read Aloud 声音行仍整行只显示 "English (United"（10 行英文声音全部如此，声音名与地区完全不可见）。
- #29 复确认：排版面板 "Paper ·"、"Lette" 截断仍在。
- 新发现 #30【低】导入成功的 snackbar 右侧出现红色数字角标"2"（第二次导入时出现），含义不明，疑似未读计数错挂在 snackbar 上。
- 观察：Me 页从子页返回时滚动位置行为不一致（四次中两次回到顶部、两次保留），自动化点按需每次重截图定位；真机上手动使用影响小。
- 睡前定时器（#23）本轮未复测：定时器入口在有声书播放器内，Android 模拟器无音频书 fixture，留真机。
