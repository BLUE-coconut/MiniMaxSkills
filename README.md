# MiniMaxSkills

MiniMaxSkills is a collection of AI agent skills powered by MiniMax multimodal models. These skills extend agent capabilities with voice synthesis, music generation, and more.

<p align="left">
  <a href="README-CN.md"><img src="https://img.shields.io/badge/中文-README--CN-blue" alt="中文"></a>
</p>

## Skills List

### Voice & Speech

| Skill | Description | Key Features |
|-------|-------------|--------------|
| [MiniMaxTTS](./MiniMaxTTS/) | Text-to-speech skill powered by MiniMax Voice API and FFmpeg. | Support multi-voice synthesis, can create audiobooks, podcasts, etc. Also provides voice cloning (10s–5min audio), voice design (text prompt), audio post-processing (merge, convert, normalize, trim) capabilities. Quick text-to-speech conversion, simple and easy to use, enables Agent to "speak". |

### Music

| Skill | Description | Key Features |
|-------|-------------|--------------|
| [MiniMaxMusicMaker](./MiniMaxMusicMaker/) | Music generation skill powered by MiniMax Music API. | Support standard songs with lyrics, pure instrumental music, melodic chanting/humming, structured prompt crafting, multiple output formats (hex/url). Interactive guided workflow for fine-grained control over every aspect of the music. |

## Getting Started

Each skill has its own `SKILL.md` with detailed usage instructions and `reference/` docs. To get started:

1. Navigate to the skill directory you want to use
2. Read the `SKILL.md` for the complete workflow
3. Set the required API key (`MINIMAX_VOICE_API_KEY` or `MINIMAX_MUSIC_API_KEY`), i.e. MiniMax Pay-as-you-go API Key
4. Follow the step-by-step guide

## Requirements

- Python 3.8+
- MiniMax Pay-as-you-go API Key ([Get one here (overseas users)](https://platform.minimax.io/user-center/basic-information/interface-key), [Get one here (Chinese users)](https://platform.minimaxi.com/user-center/basic-information/interface-key))
- FFmpeg (required for audio processing in MiniMaxTTS)

## Additional Notes

When using OpenClaw integrated with Feishu, if you need to convert audio files into Feishu voice messages, use the following prompt:

```
When OpenClaw sends audio via the Feishu message tool, it sends as a "file" (likely not distinguishing the audio type). Please follow the native Feishu API requirements below to convert and send the audio directly as a Feishu voice message.
# 1. Upload the file to Feishu first
POST https://open.feishu.cn/open-apis/im/v1/files
file_type: "opus"  # Critical!
# 2. Then send a voice message with msg_type: "audio"
POST https://open.feishu.cn/open-apis/im/v1/messages
{
  msg_type: "audio",  # Critical!
  "content": {
    "file_key": "xxx",
    "duration": 3000  # Note: must specify the actual duration of the audio
  }
}
```
