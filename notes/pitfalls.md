# 坑日志

每个坑记四件事：症状（原始报错或现象）、原因、怎么定位到的、怎么修的。最后一行写一句以后遇到类似问题先查什么。

| 编号 | 日期 | 阶段 | 一句话 |
| --- | --- | --- | --- |
| 001 | 2026-11-13 | 第 3 周 · 服务 | `ros2 service list` 为空：没有节点在运行 |
| 002 | 2026-11-13 | 第 3 周 · 服务 | `set_pen` 的字段 `off` 被 YAML 当成布尔值 false |

---

## 001 · `ros2 service list` 什么都没有

- **日期 / 阶段**：2026-11-13，第 3 周第 6 天，服务入门，用命令行观察 turtlesim 的服务
- **症状**：执行 `ros2 service list`，没有任何输出，也没有报错
- **原因**：`turtlesim_node` 没有在运行。服务是挂在节点上的，就像 Qt 的槽挂在某个 QObject 上；`ros2 service list` 列出的是当前活着的节点提供的服务，不是系统里装了哪些服务。没有节点，就没有服务
- **怎么定位**：
  - `ros2 node list` 也为空，说明不是服务的问题，是根本没有节点
  - `ps aux | grep turtlesim` 看不到进程
  - 环境变量正常（`ROS_DISTRO=humble`，`ROS_DOMAIN_ID` 未设置，默认是 0），排除了没有 source 或不在同一个 domain 的可能
- **怎么修**：另开一个终端执行 `ros2 run turtlesim turtlesim_node`，再执行 `ros2 service list`。如果节点已经在跑，列表仍然为空，先执行 `ros2 daemon stop` 清掉命令行工具缓存的旧信息再查
- **以后先查什么**：话题、服务、参数列表为空或缺东西时，先看 `ros2 node list`，确认提供它的节点真的活着；再查 `ROS_DOMAIN_ID` 两边是否一致

## 002 · 命令行调用 `set_pen` 报 `attribute name must be string`

- **日期 / 阶段**：2026-11-13，第 3 周第 6 天，命令行手动调用 turtlesim 的服务
- **症状**：
  ```bash
  ros2 service call /turtle1/set_pen turtlesim/srv/SetPen "{r: 255, g: 0, b: 0, width: 3, off: 0}"
  ```
  报错 `Failed to populate field: getattr(): attribute name must be string`
- **原因**：`ros2 service call` 和 `ros2 topic pub` 后面的参数是按 YAML 解析的。在 YAML 1.1 里，`off`、`on`、`yes`、`no` 这些不加引号的词会被当成布尔值，所以字段名 `off` 被解析成了布尔值 `False`。ROS 拿这个 `False` 去找消息里的字段，字段名必须是字符串，于是报错
- **怎么定位**：报错说“属性名必须是字符串”，说明有某个字段名被解析成了别的类型。逐个排查字段名，只有 `off` 是 YAML 的保留词。用 Python 验证：`yaml.safe_load("{off: 0}")` 得到的是 `{False: 0}`
- **怎么修**：给字段名加引号：
  ```bash
  ros2 service call /turtle1/set_pen turtlesim/srv/SetPen "{r: 255, g: 0, b: 0, width: 3, 'off': 0}"
  ```
- **以后先查什么**：命令行发消息时出现奇怪的字段报错，先怀疑 YAML 解析：字段名或字符串值是不是 `on/off/yes/no/null` 这类词，冒号后面有没有空格。以后写 yaml 参数文件（第 4 周）也是同一个坑
