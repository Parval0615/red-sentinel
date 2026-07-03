# RedSentinel 固定证据包说明

本目录保存一份最终离线运行结果的固定副本，便于评委不运行代码也能直接查看 RedSentinel 的红队攻击面覆盖、旁路监督闭环和防御回归证据。原始生成命令为：

```powershell
python run.py --comp4 --offline
```

## 文件说明

| 文件 | 对应论点 |
|---|---|
| [`convergence_curve.png`](./convergence_curve.png) | 多轮攻防后 Adaptive Defense ASR 从 44% 下降到 0%，证明防御回归可收敛 |
| [`damage_radar.png`](./damage_radar.png) | 展示 7 类威胁在加固前后的损伤变化 |
| [`convergence.json`](./convergence.json) | 收敛曲线的机器可读数据 |
| [`ablation.json`](./ablation.json) | 完整系统、去 Defense、去 Attack reflection 三组消融原始数据 |
| [`ablation_table.md`](./ablation_table.md) | 消融实验表，可直接放入答辩材料 |
| [`benchmark_datacard.md`](./benchmark_datacard.md) | AgentRiskBench-Ecommerce 红队数据卡 |
| [`evidence_pack.md`](./evidence_pack.md) | 证据包一页总览 |

## 关键数字

- Adaptive Defense 初始 ASR：44%
- Adaptive Defense 收敛后 ASR：0%
- 收敛轮数：7
- 去掉 Defense Agent：Adaptive Defense ASR 保持 44%
- 去掉 Attack reflection：攻击面覆盖停在 2/7
- 完整系统攻击面覆盖：7/7
