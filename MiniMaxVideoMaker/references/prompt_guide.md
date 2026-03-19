# Video Prompt Writing Guide

## Prompt Structure

### Basic Formula
**Main subject + Scene/Space + Movement/Change**

Best for simple, quick descriptions without specific shot requirements.

Examples:
- "A puppy runs toward the camera in a sunny park"
- "A woman walks in the rain holding an umbrella on a city street"
- "A stream flows through a green valley with morning mist"

### Professional Formula
**Main subject + Scene + Movement + Camera motion + Aesthetic atmosphere**

For cinematic, professional-quality results.

Examples:
- "A couple sits on a park bench, warm golden hour lighting, [固定] framing, intimate and romantic atmosphere"
- "A young man in a suit eats noodles at a street stall, [拉远] revealing the busy night market, warm tones, cinematic"
- "A dancer performs contemporary dance in an empty studio, [跟随] smooth tracking, dramatic side lighting"

---

## Key Principles

1. **More precise language → more accurate video**
2. **Richer description → better generation quality**
3. **Keep prompts focused on 5-6 seconds of action** — do not describe too many events
4. **Combine shot types with mood descriptors** for professional output

---

## Camera Instructions Usage

### Simultaneous Camera Movement
Place multiple instructions in one bracket:
- `[左摇,上升]` — pan left while rising
- `[推进,下摇]` — push in while tilting down

### Sequential Camera Movement
Place instructions at different points in the prompt:
- "The camera starts with [推进] toward the face, then [拉远] to reveal the full scene"

### Temporal Precision
Add natural language to refine timing:
- "镜头先缓缓下降，之后在下降的过程中向右环绕" (camera descends gradually, then curves rightward during descent)

---

## Style-Specific Prompt Tips

### Realistic / Cinematic Style (写实/电影风格)
- Mention lighting conditions: "golden hour", "overcast sky", "dramatic side lighting"
- Reference color grading: "warm tones", "cool desaturated palette", "high contrast"
- Include texture details: "rain droplets on glass", "dust particles in sunlight"
- Use cinematic terms: "shallow depth of field", "anamorphic lens flare"

Example: "A woman in a red dress walks through a rainy Tokyo street at night, neon reflections on wet pavement, [跟随] tracking shot, cinematic color grading, shallow depth of field, moody atmospheric lighting"

### Animation Style (动画风格)
- Specify animation substyle: "2D anime", "3D Pixar-style", "watercolor animation", "stop-motion"
- Describe character design: "big expressive eyes", "chibi proportions"
- Include visual effects: "sparkle particles", "speed lines", "dramatic wind effects"

Example: "A cheerful anime girl with pink twin-tails jumps through a magical forest, colorful sparkle particles, vibrant saturated colors, Studio Ghibli style, [上升] camera revealing the vast enchanted landscape"

### Comic / Manga Panel Style (漫剧/漫画风格)
- Reference art style: "manga-style", "comic book aesthetic", "graphic novel"
- Include panel effects: "dramatic shadows", "impact lines", "halftone dots"
- Describe dramatic moments: "epic pose", "dramatic reveal", "intense stare"

Example: "A heroic figure stands atop a skyscraper at sunset, cape flowing in the wind, manga-style dramatic composition with speed lines, bold shadows, [上摇] revealing the hero against the sky"

### Product / Commercial Style (产品/商业风格)
- Focus on product details: "smooth surface", "premium materials", "elegant design"
- Use studio lighting: "soft box lighting", "rim light", "gradient background"
- Describe motion: "slow rotation", "smooth reveal", "gentle float"

Example: "A luxury watch slowly rotates on a dark reflective surface, soft warm studio lighting creating elegant highlights on the metal, [推进] smooth close-up, premium commercial aesthetic"

### Fantasy / Sci-Fi Style (奇幻/科幻风格)
- Build world elements: "floating islands", "neon cyberpunk city", "enchanted forest"
- Include VFX elements: "magic particles", "holographic displays", "energy beams"
- Set epic scale: "vast landscape", "towering structures", "infinite horizon"

Example: "A spaceship emerges from hyperspace above a ringed planet, dramatic lens flare, volumetric nebula clouds in deep purples and blues, [拉远] epic wide shot revealing the scale of the cosmos, cinematic sci-fi atmosphere"

### Nature / Documentary Style (自然/纪录片风格)
- Use nature terminology: "macro shot", "time-lapse", "wildlife behavior"
- Describe natural phenomena: "morning dew", "sunset colors", "storm clouds"
- Include scientific precision: "slow motion at 240fps", "underwater perspective"

Example: "Macro shot of a butterfly emerging from its chrysalis, morning dew droplets glistening on the shell, soft natural backlighting, [推进] extremely close-up, nature documentary quality, shallow depth of field"

---

## Image-to-Video Prompt Tips

When using image-to-video mode, the prompt should focus on **movement and change** since the image already establishes the visual:

### Basic Formula
First-frame subject + movement/change

### Professional Formula
Add camera movement and atmosphere shifts

Examples:
- Image shows a still lake → Prompt: "Gentle ripples spread across the water surface, a breeze rustles the trees, [固定] fixed camera, peaceful"
- Image shows a portrait → Prompt: "The person slowly smiles and turns their head, natural blinking, [推进] subtle push in, warm lighting"

---

## Prompt Building Checklist

When crafting a prompt, ensure these layers are covered (in order):

1. **Subject Layer** (WHO/WHAT): Describe appearance, clothing, color, expression, posture
   - Bad: "a girl" → Good: "a young woman with long black hair wearing a white sundress"
   - Bad: "a cat" → Good: "a fluffy orange tabby cat with green eyes"

2. **Action Layer** (WHAT HAPPENS): Describe temporal flow with 1-2 key actions
   - Use "first...then..." for sequential: "先低头啃食，然后抬头看向镜头"
   - Include micro-actions for realism: "blinking", "breathing", "swaying", "twitching whiskers"

3. **Scene Layer** (WHERE): Specific setting with environmental details
   - Include depth: foreground + background elements
   - Add atmosphere: weather, time of day, ambient elements

4. **Camera Layer** (HOW TO SHOOT): Use `[运镜指令]` for precise control
   - Choose movement that serves the story (push-in for intimacy, pull-back for reveal)
   - Add natural language timing: "镜头缓缓推进" (camera slowly pushes in)

5. **Aesthetic Layer** (LOOK & FEEL): Lighting, color, and cinematic quality
   - Lighting: golden hour, soft backlight, neon glow, overcast diffused
   - Color: warm tones, cool desaturated, vibrant saturated, monochromatic
   - Texture: film grain, sharp digital, dreamy soft focus
   - Cinematic: shallow depth of field, anamorphic, lens flare

---

## Common Prompt Mistakes to Avoid

1. **Too many events** — keep to 1-2 actions for 6-second videos
2. **Conflicting camera instructions** — don't combine opposing movements like `[推进,拉远]`
3. **Vague descriptions** — "a nice scene" is much worse than "a sunlit meadow with wildflowers"
4. **Ignoring temporal flow** — describe what happens over time, not a static scene
5. **Overlong prompts** — stay under 200 words for best results; quality over quantity
6. **Missing aesthetic layer** — without lighting/color/mood descriptors, results look generic
7. **Static descriptions** — video needs MOTION; describe changes, not a photograph
