## 1. 令牌

- [x] 1.1 	okens.css：--color-lime-94 #fffef5 → #f3efe2，--color-white #ffffff → #f7f3e8。验证：lint:styles 批 2 通过。**验证结果**：通过。
- [x] 1.2 字面量收敛：ackground: #fff 4 个文件 13 处改为 ar(--color-white)。验证：全仓 ackground: #fff 计数为 0。**验证结果**：0 处。

## 2. 门禁与目视

- [x] 2.1 ue-tsc / uild:check / 	ests/shared / lint:styles / lint:lines。验证：全绿。**验证结果**：tsc 0；build 1m10s；shared 测试通过；批 2 通过；虚线 0 处。
- [x] 2.2 真实页面截图（CDP 登录后）核对仪表盘与测试报告。验证：	emps/dashboard-live.png、	emps/report-live.png。**验证结果**：暖米色生效。
