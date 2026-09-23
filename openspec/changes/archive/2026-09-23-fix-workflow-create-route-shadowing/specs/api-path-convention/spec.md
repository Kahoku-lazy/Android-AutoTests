## ADDED Requirements

### Requirement: 调用面的方法必须被命中视图接受

调用面守护 SHALL 在记录每个 HTTP 调用点的路径之外，同时记录其 HTTP 方法，并断言：该路径拼上 baseURL 解析后，若命中 DRF router 生成的视图，则该方法 MUST 落在该路由的动作白名单内。仅解析成功、却把请求交给不接受该方法的视图（最终表现为 405），SHALL 判定为违规。

非 router 的视图（普通函数视图、非 router 的 APIView）不在本断言范围内。

违规断言失败时，错误信息 SHALL 列出文件、方法、路径与该路由允许的动作，便于定位。

#### Scenario: router 详情路由不接受 write 方法即失败

- **WHEN** 前端以 `POST` 调用一条解析后命中 router 详情路由（动作白名单为 get/put/patch/delete）的路径
- **THEN** 守护失败并列出该方法、路径与白名单

#### Scenario: 方法被接受时通过

- **WHEN** 调用方法与命中视图的动作白名单一致（如 `PATCH` 打详情路由、`DELETE` 打详情路由、`POST` 打集合路由）
- **THEN** 守护通过

#### Scenario: 函数视图不被误判

- **WHEN** 路径解析命中的是普通函数视图（无 router 动作白名单）
- **THEN** 该方法断言跳过，不影响结论
