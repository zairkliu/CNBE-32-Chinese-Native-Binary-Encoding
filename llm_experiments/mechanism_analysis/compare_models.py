import json, os, sys, re, time, gc, torch
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","src"))
from cnbe32.db import lookup
import random
rng = random.Random(42)

BASE_PATH = r"C:\Users\zairk\.cache\huggingface\hub\models--Qwen--Qwen3.5-0.8B\snapshots\2fc06364715b967f1860aea9cf38778875588b17"
MERGE_PATH = r"C:\Users\zairk\cnbe-training1\outputs\cnbe-merged"
ENCODERS = ["unicode","cnbe_full","random_bitfield"]
RESULTS_DIR = os.path.join(os.path.dirname(__file__),"results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# 40 test cases
CASES = [
    ("北京是中国的首都","中国的首都是哪里？",["上海","北京","广州"],1),
    ("三角形有三个角","三角形有几个角？",["两个","三个","四个"],1),
    ("熊猫喜欢吃竹子","熊猫喜欢吃什么？",["竹子","肉类","水果"],0),
    ("苹果是一种水果","苹果是什么？",["水果","动物","工具"],0),
    ("太阳从东方升起","太阳从哪里升起？",["西方","东方","南方"],1),
    ("水在零度时会结冰","水在什么温度结冰？",["零度","一百度","五十度"],0),
    ("地球绕太阳公转一周需要一年","地球公转一周需要多久？",["一天","一月","一年"],2),
    ("孔子是中国古代伟大的思想家","孔子是哪国人？",["中国","日本","韩国"],0),
    ("长江是中国最长的河流","中国最长的河流是什么？",["长江","黄河","珠江"],0),
    ("鲸鱼是哺乳动物","鲸鱼属于哪一类？",["鱼类","哺乳动物","爬行动物"],1),
    ("氧气是植物光合作用的产物","光合作用产生什么？",["二氧化碳","氧气","氮气"],1),
    ("铝合金比纯铝更坚硬","铝合金和纯铝哪个更坚硬？",["铝合金","纯铝","一样"],0),
    ("火星被称为红色星球","火星被称为什么？",["蓝色星球","红色星球","绿色星球"],1),
    ("赤道是地球上最热的地方","地球上最热的地方是哪里？",["南极","北极","赤道"],2),
    ("指南针是中国古代四大发明之一","指南针是哪个国家的发明？",["中国","印度","阿拉伯"],0),
    ("维生素C存在于水果和蔬菜中","维生素C主要存在于什么中？",["肉类","水果蔬菜","谷物"],1),
    ("石油是一种不可再生能源","石油是不是可再生能源？",["是","不是","不确定"],1),
    ("金字塔位于埃及","金字塔在哪个国家？",["中国","印度","埃及"],2),
    ("南极洲是地球上最冷的大洲","最冷的大洲是哪里？",["南极洲","非洲","欧洲"],0),
    ("他每天洗澡","他每天做什么？",["洗澡","洗操","洗澡"],0),
    ("我在图书馆借了一本书","我借了什么？",["一本书","一本树","一本书"],0),
    ("天气预报说明天会下雨","明天天气怎么样？",["下雨","下雪","晴天"],0),
    ("妈妈做的菜很好吃","菜的味道怎么样？",["好吃","难吃","很咸"],0),
    ("院子里有一棵大树","院子里有什么？",["一棵树","一棵木","一棵林"],0),
    ("她用毛笔写字","她用笔还是用键盘？",["毛笔","键盘","两者都用"],0),
    ("他每天早晨跑步","他什么时候跑步？",["早晨","晚上","中午"],0),
    ("春天之后是夏天","春天之后是什么季节？",["冬天","夏天","秋天"],1),
    ("飞机的速度比汽车快","飞机和汽车哪个快？",["飞机","汽车","一样"],0),
    ("蜂蜜是蜜蜂酿造的","蜂蜜是谁酿造的？",["蜜蜂","蝴蝶","蚂蚁"],0),
    ("月球是地球的卫星","月球是地球的什么？",["恒星","行星","卫星"],2),
    ("鲁迅是中国现代文学的奠基人","鲁迅是哪方面的奠基人？",["现代医学","现代文学","现代建筑"],1),
    ("针灸是中医学的重要组成部分","针灸属于什么？",["中医学","西医学","兽医学"],0),
    ("巧克力主要原料是可可豆","巧克力的主要原料是什么？",["可可豆","咖啡豆","大豆"],0),
    ("火车在铁轨上行驶","火车在哪里行驶？",["公路上","铁轨上","天空中"],1),
    ("银河系是一个星系","银河系是什么？",["星系","行星","恒星"],0),
    ("咖啡含有咖啡因","咖啡含有哪种物质？",["咖啡因","茶碱","可可碱"],0),
    ("企鹅生活在南极","企鹅生活在哪里？",["北极","南极","赤道"],1),
    ("手机可以用来通话","手机的主要功能是什么？",["通话","飞行","煮饭"],0),
    ("鱼用鳃呼吸","鱼用什么呼吸？",["肺","鳃","皮肤"],1),
    ("自行车有两个轮子","自行车有几个轮子？",["两个","四个","一个"],0),
]

def encode(text, mode):
    out = []
    for ch in text:
        r = lookup(ch)
        if mode == "unicode": out.append(ch)
        elif mode == "cnbe_full": out.append(f"0x{r['cnbe']:08X}" if r else ch)
        elif mode == "random_bitfield":
            v = r["cnbe"] ^ rng.randint(0,0xFFFFFFFF) if r else rng.randint(0,0xFFFFFFFF)
            out.append(f"0x{v&0xFFFFFFFF:08X}")
    return " ".join(out)

def run_model(model_path, model_name):
    print(f"\n{'='*50}")
    print(f"Loading {model_name}...")
    from transformers import AutoModelForCausalLM, AutoTokenizer
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto", torch_dtype=torch.float16)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    print(f"Loaded in {time.time()-t0:.0f}s")

    results = {}
    t_start = time.time()
    for enc in ENCODERS:
        results[enc] = {"ok": 0, "n": 0}
        for idx, tc in enumerate(CASES):
            prompt = f"编码文本: {encoded[enc][idx]}\n问题: {tc[1]}\n选项: {' '.join(f'{i}.{o}' for i,o in enumerate(tc[2]))}\n只输出选项编号:"
            text = tokenizer.apply_chat_template([{"role":"user","content":prompt}], tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(text, return_tensors="pt").to(model.device)
            with torch.no_grad():
                outputs = model.generate(**inputs, max_new_tokens=5, do_sample=False)
            resp = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
            m = re.search(r"\d+", resp)
            parsed = int(m.group()) if m else None
            ok = (parsed == tc[3])
            results[enc]["ok"] += 1 if ok else 0
            results[enc]["n"] += 1
            if (idx+1) % 10 == 0:
                print(f"  [{model_name[:6]}] [{time.time()-t_start:3.0f}s] {enc:20s} {idx+1}/{len(CASES)}: {results[enc]['ok']}/{results[enc]['n']} = {results[enc]['ok']/results[enc]['n']*100:.0f}%")
    
    total_t = time.time() - t_start
    print(f"  [{model_name[:6]}] Done: {total_t:.0f}s")
    
    del model; del tokenizer; gc.collect(); torch.cuda.empty_cache()
    return results

# Pre-encode
print("Pre-encoding 40 cases...")
encoded = {enc: [encode(tc[0], enc) for tc in CASES] for enc in ENCODERS}
print("Done")

# Run base model
base_results = run_model(BASE_PATH, "Base Qwen 0.8B")

# Run trained model
trained_results = run_model(MERGE_PATH, "Trained LoRA")

# Compare
print(f"\n{'='*55}")
print(f"COMPARISON — {len(CASES)} cases, {len(ENCODERS)} encoders")
print(f"{'='*55}")
print(f"{'Encoder':20s} {'Base':>15s} {'Trained':>15s} {'Diff':>10s}")
print("-"*55)
for enc in ENCODERS:
    b = base_results[enc]; t = trained_results[enc]
    bp = b["ok"]/b["n"]*100; tp = t["ok"]/t["n"]*100
    diff = tp - bp
    sign = "+" if diff > 0 else ""
    print(f"{enc:20s} {bp:5.1f}%({b['ok']:2d}/{b['n']}) {tp:5.1f}%({t['ok']:2d}/{t['n']}) {sign}{diff:+.1f}pp")

# Save
json.dump({
    "n_cases": len(CASES), "encoders": ENCODERS,
    "base_model": {"path": BASE_PATH, "results": base_results},
    "trained_model": {"path": MERGE_PATH, "results": trained_results}
}, open(os.path.join(RESULTS_DIR,"model_comparison.json"),"w"), indent=2)
print(f"\nSaved to {RESULTS_DIR}/model_comparison.json")
