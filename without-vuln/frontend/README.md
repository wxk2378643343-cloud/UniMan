# UniMan 修订版前端

在 `without-vuln/frontend/` 安装依赖并运行开发服务。

```sh
npm ci
npm run dev
```

浏览器打开 Vite 输出的地址。启动前先确认后端在本机 8000 端口运行。开发服务依据 [vite.config.js](vite.config.js) 代理 API 请求。运行 `npm run build` 可生成 `dist/` 静态构建产物。
