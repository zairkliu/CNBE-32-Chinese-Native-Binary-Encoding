import json, os, sys, time, urllib.request, urllib.error, concurrent.futures
sys.path.insert(0, os.path.dirname(__file__))
from encoder import get_all_encoders

OLLAMA_URL = "http://localhost:11434/api/chat"
TIMEOUT = 60
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Minimal test cases
QUICK_CASES = [
    {"sentence": "苹果是一种水果", "question": "苹果是什么？", "options": ["水果", "动物", "工具"], "answer": 0},
    {"sentence": "太阳从东方升起", "question": "太阳从哪里升起？", "options": ["西方", "东方", "南方"], "answer": 1},
    {"sentence": "北京是中国的首都", "question": "中国的首都是哪里？", "options": ["上海", "北京", "广州"], "answer": 1},
    {"sentence": "三角形有三个角", "question": "三角形有几个角？", "options": ["两个", "三个", "四个"], "answer": 1},
    {"sentence": "水在零度时会结冰", "question": "水在什么温度结冰？", "options": ["零度", "一百度", "五十度"], "answer": 0},
    {"sentence": "熊猫喜欢吃竹子", "question": "熊猫喜欢吃什么？", "options": ["竹子", "肉类", "水果"], "answer": 0},
    {"sentence": "孔子是中国古代伟大的思想家", "question": "孔子是哪国人？", "options": ["中国", "日本", "韩国"], "answer": 0},
    {"sentence": "地球绕太阳公转一周需要一年", "question": "地球公转一周需要多久？", "options": ["一天", "一月", "一年"], "answer": 2},
    {"sentence": "他用毛笔写字", "question": "他用什么写字？", "options": ["铅笔", "毛笔", "钢笔"], "answer": 1},
    {"sentence": "妈妈做的菜很好吃", "question": "菜的味道怎么样？", "options": ["好吃", "难吃", "很咸"], "answer": 0},
]

def query_ollama(model, prompt):
    data = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
        "stream": False, "options": {"temperature": 0}}).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))["message"]["content"].strip()
    except Exception as e:
        return f"[ERR]"

def build_prompt(encoded, question, options):
    opts_str = " ".join(f"{i}.{o}" for i, o in enumerate(options))
    return f"编码文本: {encoded}\n问题: {question}\n选项: {opts_str}\n只输出选项编号(单个数字):"

def run_single(model, enc_name, test_cases):
    from encoder import get_all_encoders
    enc = {e.name: e for e in get_all_encoders()}[enc_name]
    correct = 0
    for tc in test_cases:
        encoded = enc.encode(tc["sentence"])
        prompt = build_prompt(encoded, tc["question"], tc["options"])
        resp = query_ollama(model, prompt)
        for ch in resp:
            if ch.isdigit() and 0 <= int(ch) < len(tc["options"]):
                if int(ch) == tc["answer"]: correct += 1
                break
    return enc_name, correct, len(test_cases)

if __name__ == "__main__":
    cases = QUICK_CASES[:5]
    encoders = ["unicode", "cnbe_full", "random_bitfield", "radical_only"]
    models = ["qwen3.5:0.8b"]

    print(f"Experiment: {len(cases)} cases, {len(encoders)} encoders, {len(models)} model\n")

    for model in models:
        print(f"Model: {model}")
        print("-" * 40)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(run_single, model, enc, cases) for enc in encoders]
            for f in concurrent.futures.as_completed(futures):
                name, c, t = f.result()
                acc = c / t * 100
                bar = "█" * int(acc / 5)
                print(f"  {name:20s} {c:2d}/{t} = {acc:5.1f}% {bar}")
        print()

    summary = {enc: {"correct": c, "total": cases} for enc in encoders}
    for model in models:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(run_single, model, enc, QUICK_CASES): enc for enc in encoders}
            for f in concurrent.futures.as_completed(futures):
                name, c, t = f.result()
                results[name] = {"correct": c, "total": t, "accuracy": c/t}

    result_file = os.path.join(RESULTS_DIR, "mechanism_results.json")
    with open(result_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {result_file}")
