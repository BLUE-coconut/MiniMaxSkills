# MiniMaxSkills

MiniMaxSkills 是 MiniMax 官方提供的 AI Agent 技能库，基于 MiniMax 多模态模型，为 Agent 拓展语音合成、音乐生成等能力。

## 技能列表

### 语音 & 语音合成

| 技能 | 简介 | 核心功能 |
|------|------|----------|
| [MiniMaxTTS](./MiniMaxTTS/) | 基于 MiniMax Voice API 和 FFmpeg 的语音合成技能。 | 支持多角色语音合成，可制作有声书、播客等。还提供了声音克隆（10秒–5分钟音频）、声音设计（文字描述生成）、音频后处理（合并、转换、归一化、裁剪）能力。快速文本转语音、简单易用、使 Agent 具备「说话」的能力。 |

### 音乐

| 技能 | 简介 | 核心功能 |
|------|------|----------|
| [MiniMaxMusicMaker](./MiniMaxMusicMaker/) | 基于 MiniMax Music API 的音乐生成技能。 | 支持带歌词的完整歌曲生成、纯音乐/器乐生成、旋律哼唱/吟唱生成。交互式引导工作流，支持对音乐各维度的精细控制。 |

## 快速开始

每个技能目录下都有 `SKILL.md`（详细使用说明）和 `reference/`（参考文档）。开始使用：

1. 进入你需要使用的技能目录
2. 阅读 `SKILL.md` 了解完整工作流程
3. 设置所需的 API Key（`MINIMAX_VOICE_API_KEY` 或 `MINIMAX_MUSIC_API_KEY`），即 MiniMax 按量计费 API Key
4. 按照步骤指引操作

## 环境要求

- Python 3.8+
- MiniMax 按量计费 API Key（[中国用户前往获取](https://platform.minimaxi.com/user-center/basic-information/interface-key), [海外用户前往获取](https://platform.minimax.io/user-center/basic-information/interface-key)）
- FFmpeg（MiniMaxTTS 的音频处理功能需要）

## 其他说明
在 openclaw 接入飞书中使用时，若需将音频文件转换为飞书语音消息，则可使用以下提示词：
```
OpenClaw 用飞书 message 工具发音频时是以"文件"发送（可能是没区分 audio 类型），请按照以下 Feishu 原生 API 要求进行优化，实现将音频直接转换为飞书语音消息进行发送。
# 1. 先上传文件到飞书
POST https://open.feishu.cn/open-apis/im/v1/files
file_type: "opus"  # 关键！
# 2. 再发送语音消息，指定 msg_type: "audio"
POST https://open.feishu.cn/open-apis/im/v1/messages
{
  msg_type: "audio",  # 关键！
"content": {
   "file_key": "xxx",
   "duration": 3000 # 注意：必须标注语音的实际时长
  }
}
```