# 华甄选 · 只读选品目录（GitHub Pages）

静态只读货盘浏览站。对照 Motomotos 的免费 GitHub Pages 用法：无后端、无 SQLite、无录入。

- 公司：深圳市华甄选礼品有限公司
- 展示：零售参考价、品牌、分类、预算档（价格档）
- **不展示**：供货价 / 集采价；无管理后台、无录入

## 本地预览

```bash
cd ~/claude-workdir/huazhenxuan-site
python3 -m http.server 8822
# 打开 http://127.0.0.1:8822/
```

## 从本机库刷新（录入后更新站点）

默认读同级目录 `../huazhen-catalog/data/catalog.db`：

```bash
cd ~/claude-workdir/huazhenxuan-site
python3 scripts/export-from-db.py
git add data images
git commit -m "refresh catalog export"
git push
```

指定库：

```bash
python3 scripts/export-from-db.py --db /path/to/catalog.db
```

推送后 GitHub Pages 大约一分钟内更新。

## 部署

Public repo → Settings → Pages → Deploy from branch `main` / root（或 `gh api` 已启用）。
