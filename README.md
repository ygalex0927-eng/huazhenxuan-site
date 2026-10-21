# 华甄选 · 只读选品站

GitHub Pages 静态站：完整 Maison React 前端（动画保留），数据来自本机 `catalog.db` 导出。

- 站点：https://huazhenxuan.com/ （亦可用 https://ygalex0927-eng.github.io/huazhenxuan-site/）
- 只读：无登录录入、无供货价/集采价
- 刷新货盘：

```bash
cd ~/claude-workdir/huazhenxuan-site
python3 scripts/export-catalog-api.py
# then rebuild SPA from huazhen-catalog/web with VITE_STATIC=1 and rsync dist (see scripts/deploy-static.sh)
```
