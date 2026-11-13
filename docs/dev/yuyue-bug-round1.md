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
20. 【中·待确认】新建合集输入名字回车关闭后，合集列表仍是空的：要么创建静默失败，要么与 #16“上次快照不刷新”属同类不刷新问题，需复测。
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
