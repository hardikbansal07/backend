import json

transcript_path = r"C:\Users\acer\.gemini\antigravity\brain\99445a72-de58-42bd-9af3-54fa1c365114\.system_generated\logs\transcript.jsonl"

print("--- SEARCHING TRANSCRIPT FOR SPECIFIC MEDIA IMAGES ---")
with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            step = json.loads(line)
            content = str(step.get('content', ''))
            if '1779956055684' in content or '1779956064821' in content:
                print(f"Step {step.get('step_index')} (Source: {step.get('source')}, Type: {step.get('type')}):")
                print(content[:1500])
                print("=" * 60)
        except Exception as e:
            pass
