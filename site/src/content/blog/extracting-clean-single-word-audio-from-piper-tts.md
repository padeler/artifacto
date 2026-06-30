---
title: "Extracting Clean Single-Word Audio from Piper TTS"
summary: "Piper TTS struggles with isolated words—feed it context and slice the output to get perfect single-word audio."
pubDate: "2026-06-30"
tags: ["audio", "python", "piper", "greek", "tts", "voice"]
draft: false
---

Piper TTS falls apart on isolated letters and numbers or single words in Greek. The VITS architecture needs surrounding context to generate smooth phonetic transitions; feed it a single word and the neural network panics—you get robotic glitching, harsh clipping, or silence.

The workaround: feed Piper a longer sentence (so it has context), then extract just the word you need with timestamps.

## The Solution

Feed Piper a padded string like `"Το γράμμα βήτα"` and extract the audio segment for `"βήτα"` using word-level timestamps.

**Step 1: Get timestamps from Piper**

```bash
echo "Το γράμμα βήτα" | piper --model el_GR-rapunzelina-low.onnx --output_json
```

Piper outputs JSON with precise start/end times for each word in milliseconds.

**Step 2: Slice the audio**

Use pydub to extract just the target word:

```python
import json
import subprocess
from pydub import AudioSegment

text = "Το γράμμα βήτα"
model_path = "el_GR-rapunzelina-low.onnx"
output_wav = "full_sentence.wav"
target_word = "βήτα"

command = f'echo "{text}" | piper --model {model_path} --output_file {output_wav} --output_json'
process = subprocess.run(command, shell=True, capture_output=True, text=True)

response_data = json.loads(process.stdout)

for w in response_data["words"]:
    if w["word"] == target_word:
        start_ms = int(w["start_time"] * 1000)
        end_ms = int(w["end_time"] * 1000)
        
        full_audio = AudioSegment.from_wav(output_wav)
        isolated = full_audio[start_ms:end_ms]
        isolated.export("isolated_beta.wav", format="wav")
        print(f"Extracted '{target_word}' cleanly")
        break
```

Piper gets the structural context it needs. You get pristine single-word audio. Everyone wins.
