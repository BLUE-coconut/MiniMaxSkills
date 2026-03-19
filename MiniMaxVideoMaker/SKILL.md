---
name: minimax-video-maker
description: Create videos with MiniMax video models (Hailuo-2.3, Hailuo-02, S2V-01). Use when generating videos from text prompts, images, start-end frames, or subject references via MiniMax Video Generation API. Supports multiple video styles including realistic, anime, comic, commercial, fantasy, and documentary. Supports adding background music (BGM) via MiniMax Music API or local audio files. **NEW: Supports long video generation (30s+) via automatic scene chaining with last-frame extraction and parallel instrumental BGM generation.** Guides users through an interactive workflow to produce professional-quality videos.
---

# MiniMax Video Maker

Generate videos using MiniMax Video Generation API. Default model: **MiniMax-Hailuo-2.3** (recommended).

## Environment Setup

```bash
export MINIMAX_API_KEY="your_api_key"
```

To verify the environment:
```bash
python check_environment.py
```

---

## Generation Modes

| Mode | Code | Description | Key Parameters |
|------|------|-------------|----------------|
| Text-to-Video | `t2v` | Generate from text prompt only | `--prompt` |
| Image-to-Video | `i2v` | First-frame image + prompt | `--first-frame`, `--prompt` |
| Start-End Frame | `sef` | First + last frame images + prompt | `--first-frame`, `--last-frame`, `--prompt` |
| Subject Reference | `ref` | Face photo + prompt (face consistency) | `--subject-image`, `--prompt` |

---

## Agent Workflow (MUST FOLLOW)

When a user requests video creation, **always** follow this interactive workflow. Do NOT skip steps or jump directly to generation.

### Step 1: Understand Basic Requirements

Analyze the user's request and determine:

1. **Generation Mode** — Which of the 4 modes to use:
   - Text-only description → `t2v`
   - User has a starting image → `i2v`
   - User has both start and end images → `sef`
   - User wants face consistency from a photo → `ref`

2. **Core Subject** — Extract what/who the main subject is from the user's description.

If the user provides an image, confirm whether it should be used as:
- A first frame (i2v mode)
- Part of a start-end frame pair (sef mode)
- A face reference for subject consistency (ref mode)

### Step 2: Guided Requirement Refinement (Interactive)

Based on the user's basic request, **proactively offer options** to refine each dimension. Present each question with lettered choices (A/B/C/...) so the user can quickly select. Do NOT dump all questions at once — ask in 2-3 focused rounds.

#### Round 1: Style & Scene (ask together)

**Q1 — Video Style:** Which visual style?
- A) Realistic/Cinematic (写实/电影) — photorealistic, cinematic lighting, film-quality
- B) Anime/Animation (动画) — 2D anime, 3D Pixar-style, Ghibli-style
- C) Comic/Manga (漫剧/漫画) — manga-style, graphic novel, bold shadows
- D) Commercial/Product (产品/商业) — studio lighting, premium feel
- E) Fantasy/Sci-Fi (奇幻/科幻) — magical worlds, futuristic cityscapes
- F) Nature/Documentary (自然/纪录片) — wildlife, macro, natural phenomena

**Q2 — Scene/Setting:** Where does the action take place? Offer 3-4 options derived from the subject context, plus "Other".
> Example for "cute bunny eating carrot":
> - A) Warm home kitchen with wooden table (温馨厨房)
> - B) Sunny garden / grass lawn (阳光花园)
> - C) Studio with clean background (摄影棚)
> - D) Other — describe your own

#### Round 2: Action, Camera & Mood (ask together)

**Q3 — Action/Movement:** What key action happens? Offer 2-3 options based on the subject, keeping to 1-2 actions (6s limit). Include a "custom" option.
> Example for "bunny eating carrot":
> - A) Bunny nibbles carrot, then looks up at camera with cute expression
> - B) Bunny hops toward carrot, sniffs it, then starts eating
> - C) Close-up of bunny chewing, showing details of whiskers twitching

**Q4 — Camera Movement:** How should the camera move? Offer options with Chinese 运镜指令:
- A) Push in close-up `[推进]` — gradually zoom into the subject
- B) Fixed framing `[固定]` — stable, no camera movement
- C) Follow/tracking `[跟随]` — camera follows the subject's movement
- D) Pull back reveal `[拉远]` — start close, reveal the full scene
- E) Rise up `[上升]` — camera rises to show wider view
- F) Orbit/pan `[左摇]` or `[右摇]` — camera rotates around subject
- G) Combined (specify) — e.g., `[推进,下摇]` push in while tilting down

**Q5 — Mood/Atmosphere:** What feeling should the video convey?
- A) Warm and cozy (温馨治愈)
- B) Cinematic and dramatic (电影感)
- C) Playful and fun (活泼有趣)
- D) Elegant and premium (优雅高级)
- E) Mysterious and moody (神秘氛围)
- F) Other

#### Round 3: Technical & BGM (ask together)

**Q6 — Duration & Resolution:**
- A) 6 seconds, 1080P (default, recommended)
- B) 6 seconds, 768P
- C) 10 seconds, 768P (longer duration)

**Q7 — Background Music (BGM):**
- A) No BGM — video only
- B) Auto-generate BGM — describe the music style or let the agent match it to the video mood
- C) Use existing audio file — provide a local audio file path
- D) Decide later — add BGM after seeing the video result

> If user selects B, ask for music style preference and whether they want **pure instrumental** or **short vocal track**:
> - **Instrumental vs Vocals:** Pure instrumental (`--instrumental`) takes longer to generate (~4min) but has no singing. Default mode generates a short vocal version (~40s) which is trimmed to video length.
> - **Style options** (tailored to video mood): bamboo flute + harp, soft piano + strings, kalimba + ambient pads, acoustic guitar + percussion, auto-match
>
> Always tailor style options to the video's specific mood and style. A cinematic video should offer orchestral/strings/brass options; a playful video should offer ukulele/xylophone/bouncy options.

#### Refinement Principles

- **Always provide concrete options** derived from the user's context — never ask open-ended "what do you want?" without suggestions
- **Default to the best option** — mark recommended choices with "(Recommended)" so users can quickly accept
- **Skip dimensions already specified** — if the user already said "anime style", don't ask about style again
- **Adapt options to context** — a product video needs different scene/camera options than a pet video
- **Keep each round to 2-3 questions max** — avoid overwhelming the user

### Step 3: Craft the Prompt & Present Plan

Based on all gathered requirements, craft a professional prompt following the **Prompt Architecture**:

**Prompt Formula:** `[Main subject + detailed appearance] + [Action/movement over time] + [Scene/setting + details] + [Camera movement with 运镜指令] + [Aesthetic/mood/lighting/color]`

**Key prompt-crafting techniques** (from MiniMax official prompt guide):

1. **Subject precision**: Describe appearance details — clothing, color, expression, posture
2. **Temporal flow**: Describe what happens over time, not a static scene. Use "first...then..." for sequential actions
3. **Camera instructions**: Use `[运镜指令]` syntax for precise control. Combine max 3 in one bracket for simultaneous movement. Place at different positions for sequential movement
4. **Aesthetic layer**: Add lighting (golden hour, neon, soft backlight), color grading (warm tones, desaturated, vibrant), texture (rain droplets, dust particles), and cinematic terms (shallow depth of field, anamorphic)
5. **Keep it focused**: 1-2 key actions for 6s video. Under 200 words. Quality over quantity

**Style-specific techniques** — Read `references/prompt_guide.md` for detailed per-style prompt patterns.

Present the complete plan to user in a clear table:

| Item | Detail |
|------|--------|
| Mode | t2v / i2v / sef / ref |
| Model | MiniMax-Hailuo-2.3 |
| Prompt | (full crafted prompt text) |
| Image inputs | (if any) |
| Duration | 6s |
| Resolution | 1080P |
| Style | Realistic / Anime / etc. |
| BGM | None / Auto-generate: "gentle piano" / File: path |

**Wait for user confirmation before proceeding.**

### Step 3: Generate Video (and BGM in Parallel)

After user approval, execute the generation command.

**Performance optimization:** If BGM was requested, launch video generation and BGM generation **in parallel** (two separate shell commands running concurrently) to minimize total wait time. The total time becomes `max(video_time, bgm_time)` instead of `video_time + bgm_time`.

**Script location:** `scripts/generate_video.py` (relative to this skill's directory)

#### Text-to-Video
```bash
python scripts/generate_video.py \
  --mode t2v \
  --prompt "Your crafted prompt here" \
  --duration 6 \
  --resolution 1080P \
  --output <cwd>/video/output.mp4
```

#### Image-to-Video
```bash
python scripts/generate_video.py \
  --mode i2v \
  --first-frame "path/to/image.jpg" \
  --prompt "Description of movement/changes" \
  --duration 6 \
  --resolution 1080P \
  --output <cwd>/video/output.mp4
```

#### Start-End Frame
```bash
python scripts/generate_video.py \
  --mode sef \
  --first-frame "path/to/start.jpg" \
  --last-frame "path/to/end.jpg" \
  --prompt "Description of transition" \
  --model MiniMax-Hailuo-02 \
  --output <cwd>/video/output.mp4
```

#### Subject Reference
```bash
python scripts/generate_video.py \
  --mode ref \
  --subject-image "path/to/face.jpg" \
  --prompt "Description of scene and action" \
  --model S2V-01 \
  --output <cwd>/video/output.mp4
```

#### Additional Options
- `--prompt-optimizer false` — Disable auto prompt optimization for precise control
- `--fast-pretreatment` — Speed up prompt optimization (Hailuo-2.3/02 only)
- `--model <name>` — Override default model selection
- `--aigc-watermark` — Add watermark to output

#### Template-Based Generation (Video Agent)
For stylized template videos, use `scripts/generate_template_video.py`:
```bash
python scripts/generate_template_video.py \
  --template-id <template_id> \
  --media "https://example.com/image.jpg" \
  --text "Optional text" \
  --output <cwd>/video/template_output.mp4
```

Available template IDs — read `references/api_documentation.md` section "Video Template Agent" for the full template list.

### Step 4: Add Background Music (if requested)

If the user chose BGM in Step 2 Round 3, add background music after video generation.

**Script location:** `scripts/add_bgm.py` (relative to this skill's directory)
**Requires:** FFmpeg installed on the system.

#### Option A: Auto-Generate BGM via MiniMax Music API
Generate background music matching the video mood, then merge:
```bash
python scripts/add_bgm.py \
  --video <cwd>/video/output.mp4 \
  --generate-bgm \
  --music-prompt "A warm healing ambient at 72 BPM, featuring soft piano arpeggios layered with gentle acoustic guitar fingerpicking and light strings, creating an intimate cozy atmosphere" \
  --bgm-volume 0.3 \
  --fade-in 0.5 --fade-out 1.0 \
  --output <cwd>/video/output_with_bgm.mp4
```

**--instrumental flag:** Use `--instrumental` to generate pure instrumental music without vocals/lyrics. Without this flag, the API generates a short vocal track (~40s) which is trimmed to video length.

**CRITICAL: Music Prompt Crafting Rules**

The MiniMax Music API generates **music (instruments + melody)**, NOT sound effects. Never use prompts like "bird chirping, wind blowing, rustling leaves" — these are sound effects, not music, and produce poor results.

**BGM Prompt Formula:**
```
[Genre/Style] + [BPM] + [Core instruments] + [Mood/atmosphere] + [Dynamic description]
```

**Step-by-step approach to derive BGM prompt from video context:**
1. **Match the video mood** → choose a musical genre and tempo that evokes the same feeling
2. **Pick 2-3 core instruments** → select instruments whose timbre matches the visual atmosphere
3. **Describe musical dynamics** → how the music evolves (e.g., starts sparse, builds gently)
4. **Add production style** → spatial qualities (intimate/wide, dry/reverberant)

**Video Mood → BGM Prompt Mapping:**

| Video Mood | BGM Prompt Example |
|------------|-------------------|
| Warm/cozy (温馨治愈) | "A warm healing instrumental at 72 BPM, featuring soft piano arpeggios with gentle acoustic guitar fingerpicking and light pad strings, intimate and cozy production, lo-fi warmth" |
| Cinematic/dramatic (电影感) | "A cinematic orchestral instrumental at 90 BPM, building from solo cello to layered strings with French horn, sweeping emotional arc, wide reverberant soundscape" |
| Playful/fun (活泼有趣) | "An upbeat playful instrumental at 120 BPM, featuring bouncy pizzicato strings with ukulele strumming and light xylophone, cheerful and whimsical, bright mix" |
| Elegant/premium (优雅高级) | "An elegant jazz instrumental at 80 BPM, smooth piano with brushed drums and upright bass, sophisticated and minimal, warm analog tone" |
| Mysterious/moody (神秘氛围) | "A dark ambient instrumental at 65 BPM, ethereal synth pads with distant reverb piano and sub bass, suspenseful cinematic texture, spacious and haunting" |
| Nature/documentary (自然纪录片) | "A peaceful pastoral instrumental at 68 BPM, featuring solo bamboo flute melody with soft harp arpeggios and delicate strings, organic and serene, gentle dynamic swell, airy open production" |
| Sci-Fi/futuristic (科幻) | "A futuristic electronic instrumental at 100 BPM, pulsing synth arpeggios with deep bass and shimmering pads, cinematic sci-fi atmosphere, wide stereo field" |
| Anime/cartoon (动画) | "A bright J-pop style instrumental at 130 BPM, energetic synth leads with electric guitar and driving drums, kawaii and uplifting, polished pop production" |
| Peaceful/calm (平静舒适) | "A serene ambient instrumental at 60 BPM, featuring gentle kalimba with soft reverb piano and warm pad layers, meditative and tranquil, spacious airy mix" |
| Epic/grand (史诗恢弘) | "An epic cinematic instrumental at 110 BPM, powerful brass fanfare with timpani and full orchestra, heroic and triumphant, massive arena soundscape" |

**Common mistakes to AVOID in music prompts:**
- "nature sounds, bird singing, wind" → Music model cannot generate sound effects
- "background music" → Too vague, no musical guidance
- "happy music" → No instruments, no BPM, no genre — results are generic
- "piano" → Single word is too sparse; describe how the piano is played and what mood it evokes

#### Option B: Use Existing Audio File
Merge a local audio file as background music:
```bash
python scripts/add_bgm.py \
  --video <cwd>/video/output.mp4 \
  --audio /path/to/bgm.mp3 \
  --bgm-volume 0.3 \
  --fade-in 0.5 --fade-out 1.0 \
  --output <cwd>/video/output_with_bgm.mp4
```

#### BGM Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--bgm-volume` | 0.3 | BGM volume relative to original (0.0-1.0). Lower = subtler background music |
| `--fade-in` | 0.5 | Fade-in duration in seconds at start |
| `--fade-out` | 1.0 | Fade-out duration in seconds at end |
| `--replace-audio` | false | Replace original audio entirely instead of mixing |
| `--instrumental` | false | Generate pure instrumental music (no vocals/lyrics) |

**Note:** Generated BGM is saved to `<cwd>/video/tmp/generated_bgm.mp3` for reuse. The music is automatically trimmed to match video duration.

### Step 5: Post-Generation Review

After the video (and optional BGM) is generated:
1. Inform the user of the output file path and size
2. Ask if the result meets expectations
3. If adjustments are needed, offer specific options:
   - **Prompt refinement**: more precise subject description, different camera work, adjusted lighting/color
   - **Model change**: Hailuo-2.3-Fast for speed, Hailuo-02 for different feel
   - **Duration/resolution**: switch to 10s@768P for longer video
   - **Precise control**: use `--prompt-optimizer false` to prevent auto-rewriting
   - **BGM adjustment**: change music style, adjust volume, add/remove BGM
4. Re-generate with updated parameters as needed
5. If user wants BGM added to a video that was generated without it, run add_bgm.py on the existing video

---

## Long Video Generation (30s+)

For videos longer than 10 seconds, use the long video generation script which:
1. Generates sequential clips (6-10s each) with **automatic scene chaining** via last-frame extraction
2. Uses i2v mode for smooth transitions between scenes
3. **Generates BGM in parallel** using music-2.5+ instrumental mode
4. Concatenates all clips and merges with BGM automatically

### When to Use Long Video Mode
- User wants a video longer than 10 seconds
- User describes multiple scenes or a sequence of actions
- User wants background music automatically

### Workflow

**Step 1: Plan the Scenes**
Break down the story into distinct scenes (each 6-10s):

| Scene # | Description | Duration |
|---------|-------------|----------|
| 1 | Opening scene - establishing shot | 6s |
| 2 | Main action begins | 6s |
| 3 | Climax moment | 10s |
| 4 | Resolution/ending | 6s |

**Step 2: Craft Prompts for Each Scene**
Each scene prompt should:
- Be self-contained (describe what's happening in that clip)
- Include camera movement instructions
- Reference the previous scene's ending for continuity

**Step 3: Generate Long Video**

```bash
python scripts/generate_long_video.py \
  --scenes \
    "Scene 1 description with camera movement" \
    "Scene 2 description continuing the story" \
    "Scene 3 description climax moment" \
    "Scene 4 description ending" \
  --music-prompt "Epic orchestral instrumental at 90 BPM, dramatic cinematic atmosphere" \
  --segment-duration 6 \
  --resolution 768P \
  --bgm-volume 0.4 \
  --fade-in 1.0 --fade-out 1.5 \
  --output video/final_long_video.mp4
```

### Long Video Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--scenes` | **required** | List of scene descriptions (one per segment) |
| `--segment-duration` | 6 | Duration per segment (max 10s) |
| `--resolution` | 768P | Resolution (768P recommended for longer videos) |
| `--music-prompt` | None | BGM prompt for instrumental music generation |
| `--bgm-volume` | 0.4 | BGM volume relative to original |
| `--fade-in` | 1.0 | Fade-in duration at start |
| `--fade-out` | 1.5 | Fade-out duration at end |
| `--output` | **required** | Output file path |

### Technical Details

- **Scene Chaining**: Each segment's last frame is extracted and used as the first frame for the next segment (i2v mode)
- **BGM Generation**: Uses music-2.5+ in instrumental mode (no vocals) for ~4 min generation
- **Parallel Processing**: BGM generates while video segments are being prepared
- **FFmpeg Concatenation**: All clips are joined with stream-copy for efficiency

### Example: Skiing Action Sequence

```bash
python scripts/generate_long_video.py \
  --scenes \
    "A skier stands at the top of a steep snow mountain, looking down at the dramatic slope, [上升] camera rises slowly revealing the vast white landscape, epic winter scenery" \
    "The skier pushes off and races down the steep slope, body leaning forward, snow spraying dramatically behind, [跟随] camera follows closely keeping the skier centered, intense speed and momentum" \
    "The skier launches off a big jump into the air, time slows to super slow motion, mid-air pose with arms extended, [固定] camera captures the frozen moment, epic aerial moment" \
    "The skier lands smoothly on the snow, continues down the slope with confident smile, [拉远] camera pulls back showing the scenic mountain backdrop, triumphant finish" \
  --music-prompt "An energetic electronic sports anthem at 140 BPM, pulsing synth with driving drums, extreme sports action atmosphere, heroic and adrenaline-fueled" \
  --segment-duration 6 \
  --resolution 768P \
  --output video/skiing_complete.mp4
```

### Tips for Long Video Prompts

1. **First Scene**: Establish the setting and introduce the subject
2. **Middle Scenes**: Build the action with clear continuity from previous scene
3. **Last Scene**: Provide a satisfying conclusion
4. **Camera Movement**: Vary camera directions between scenes for visual interest
5. **Transitions**: Describe how one action leads to the next (e.g., "launches off", "lands then continues")

---

## Model Selection Guide

| Use Case | Recommended Model | Why |
|----------|------------------|-----|
| General high-quality | MiniMax-Hailuo-2.3 | Best quality, latest model |
| Quick drafts/iteration | MiniMax-Hailuo-2.3-Fast | Faster generation |
| Start-end frame transitions | MiniMax-Hailuo-02 | Only model supporting sef |
| Face-consistent characters | S2V-01 | Subject reference support |
| Director-level camera control | T2V-01-Director / I2V-01-Director | Enhanced camera control |
| Live photo effects | I2V-01-live | Subtle animation from photo |

---

## Important Constraints

- **Prompt max length:** 2000 characters
- **Video duration:** 6s (default) or 10s (768P only, select models)
- **Image requirements:** JPG/JPEG/PNG/WebP, < 20MB, short side > 300px, aspect ratio 2:5 to 5:2
- **Generation is async:** Typical wait time is 1-5 minutes
- **Poll interval:** 10 seconds (do not poll more frequently)
- Both local image paths and public URLs are accepted for image inputs
- Output directory (`<cwd>/video/`) is created automatically if it doesn't exist
