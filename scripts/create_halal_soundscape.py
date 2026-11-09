import os
import subprocess

sfx_base = r"C:\Users\shami\.gemini\config\skills\brag\assets\sfx"
keyboard_dir = os.path.join(sfx_base, "keyboard")
ui_dir = os.path.join(sfx_base, "ui")

keypress_1 = os.path.join(keyboard_dir, "keypress-001.wav")
keypress_2 = os.path.join(keyboard_dir, "keypress-002.wav")
keypress_3 = os.path.join(keyboard_dir, "keypress-003.wav")
switch_1 = os.path.join(ui_dir, "switch1.ogg")
click_1 = os.path.join(ui_dir, "click1.ogg")
click_3 = os.path.join(ui_dir, "click3.ogg")
mouse_1 = os.path.join(ui_dir, "mouseclick1.ogg")

project_root = r"C:\Users\shami\OneDrive\Desktop\stock-analyzer"
output_audio = os.path.join(project_root, r"brag-output\composition\assets\music\bgm.mp3")
os.makedirs(os.path.dirname(output_audio), exist_ok=True)

# Mechanical trading terminal cues: mechanical keys, toggles, low airflow
# Zero musical instruments, zero melodies, zero drums

cues = [
    (0.2, keypress_1),
    (0.5, keypress_2),
    (0.8, keypress_3),
    (1.4, switch_1),
    (3.0, click_1),
    (4.5, click_3),
    (6.5, switch_1),
    (7.0, keypress_1),
    (7.3, keypress_2),
    (7.8, mouse_1),
    (8.2, keypress_3),
    (8.7, keypress_1),
    (9.2, mouse_1),
    (9.8, keypress_2),
    (10.2, keypress_3),
    (11.0, mouse_1),
    (11.7, keypress_1),
    (12.4, switch_1),
    (13.0, click_1),
    (13.7, click_3),
    (14.5, click_1),
    (15.2, switch_1),
    (15.8, click_3),
]

inputs = ['-f', 'lavfi', '-i', 'anoisesrc=d=18:c=pink:r=48000:a=0.0015,lowpass=f=300,volume=0.4']
filter_parts = []
filter_parts.append('[0:a]volume=0.4[ambience]')

mix_inputs = ['[ambience]']

for idx, (timestamp, filepath) in enumerate(cues, start=1):
    inputs.extend(['-i', filepath])
    delay_ms = int(timestamp * 1000)
    filter_parts.append(f'[{idx}:a]adelay={delay_ms}|{delay_ms},volume=0.85[sfx{idx}]')
    mix_inputs.append(f'[sfx{idx}]')

num_streams = len(mix_inputs)
filter_parts.append(f'{"".join(mix_inputs)}amix=inputs={num_streams}:duration=first:dropout_transition=2[out]')

filter_complex_str = ';'.join(filter_parts)

cmd = [
    'ffmpeg', '-y',
    *inputs,
    '-filter_complex', filter_complex_str,
    '-map', '[out]',
    '-c:a', 'libmp3lame',
    '-b:a', '192k',
    output_audio
]

print("Assembling AlphaPulse halal soundscape...")
res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode == 0:
    print(f"SUCCESS: Halal soundscape generated at {output_audio}")
else:
    print("Error generating soundscape:")
    print(res.stderr)

