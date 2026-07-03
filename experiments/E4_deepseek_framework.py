import openai, os
client = openai.OpenAI(api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
test_data = [
    {"char": "\u6811", "prompt": "Split the radical from this character"},
    {"char": "\u6d77", "prompt": "Split the radical from this character"},
    {"char": "\u5df3", "prompt": "Is this character ji or si?"},
    {"char": "\u672b", "prompt": "Is this character wei or mo?"},
    {"char": "", "prompt": "Correct the idiom: \u518d\u63a5\u518d\u52b1"},
]
def run(use_cnbe):
    for d in test_data:
        p = d["prompt"] + (": " + d["char"] if d["char"] else "")
        if use_cnbe and d["char"]:
            p += " [CNBE info available]"
        try:
            r = client.chat.completions.create(model="deepseek-v4-flash", messages=[{"role":"user","content":p}], temperature=0.3)
            print(" " + r.choices[0].message.content[:80])
        except Exception as e:
            print(" Error: " + str(e))
print("Baseline:"); run(False)
print("CNBE-enhanced:"); run(True)
