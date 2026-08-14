# M5 Person B：Repair Generator 与闭环控制 v0.1

状态：Person B 范围的书面契约、生成 Prompt、确定性控制器、正反测试和 Gold 回放已完成；M5 整体仍等待全量 pilot 的 Person A 人工复核。

本发布使用独立 M5 v0.1 输入、`PatchProposal` 和运行清单，不修改 M1–M4 冻结 Schema。`harness/m5_repair.py` 实现 `insert_before`、`replace`、`delete`、`mark_irreparable`，严格绑定 ErrorCertificate 的目标版本、允许操作、依赖引用和修改预算。Controller 直接调用 Person A 的 fail-closed 数学复核门并绑定上下文、证书与补丁摘要；三字段“同意”不能应用补丁。补丁只有经非 Generator 的完整独立 review 接受后才能事务式应用；异常时当前图、版本历史、失效集、重验队列和事件全部回滚。

替换或插入会将旧目标移入不可变版本历史，仅在当前图保留新版本；删除会留下删除历史。三类图修改都会计算依赖旧版本的完整后代闭包，将其移出当前图并登记为 stale，同时清除对应缓存并产生按拓扑顺序排列的重验/阻塞队列。规范化补丁指纹忽略 patch ID 和解释文本但包含全部结构及证据依赖；同一结构补丁再次出现立即以 `equivalent_patch` 终止。每次提交只能复核一次，拒绝后才可重试；达到最大轮数以 `max_rounds` 终止，不可局部修复以 `mark_irreparable` 终止。

M4 v1.1 接受证书及仓库真实的 `m4-integrated-v1.1` 联合验收对象在构造时复制、摘要绑定并只读暴露；任何快照都复核其摘要，不会回写冻结证书。运行清单按尝试顺序保存输入、M4 证据、补丁指纹、review 摘要、事件和最终状态摘要。

`data/fixtures/m5/person_b_gold_repair.json` 是偶数平方修复的端到端 Gold：冻结错误证书，提交替换补丁，由 Person A 独立接受，生成节点 v2，并使依赖 v1 的结论 stale。已知限制：模型适配器是注入式 callable，正式模型版本、成本与全量 pilot 结果须在联合验收中冻结；Person B 的机制测试不替代 Person A 数学判断。
