import json, os, sys, re, time, gc, torch, math, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","..","src"))
from cnbe32.db import lookup

BASE_PATH = r"C:\Users\zairk\.cache\huggingface\hub\models--Qwen--Qwen3.5-0.8B\snapshots\2fc06364715b967f1860aea9cf38778875588b17"
ENCODERS = ["unicode","cnbe_full","random_bitfield"]
RESULTS_DIR = os.path.join(os.path.dirname(__file__),"results")
BATCH_SIZE = 16
rng_enc = random.Random(42)

# =========== GENERATE 1000 TEST CASES ===========
print("Generating 1000 test cases...")

# Entity pool: name, category, property, wrong1, wrong2
POOL = [
    # Geography
    ("北京","首都","中国","上海","广州"),("上海","最大城市","中国","北京","深圳"),
    ("长江","最长河流","中国","黄河","珠江"),("黄河","第二长河流","中国","长江","淮河"),
    ("太平洋","最大海洋","世界","大西洋","印度洋"),("撒哈拉沙漠","最大沙漠","世界","戈壁","阿拉伯"),
    ("南极洲","最冷大陆","世界","非洲","欧洲"),("赤道","最热地区","地球","北极","南极"),
    ("埃及","金字塔所在","非洲国家","印度","中国"),("日本","富士山所在","亚洲国家","韩国","中国"),
    ("俄罗斯","面积最大","国家","加拿大","中国"),("法国","埃菲尔铁塔所在","欧洲国家","德国","意大利"),
    ("尼罗河","最长河流","非洲","亚马逊河","长江"),("青藏高原","最高高原","中国","云贵高原","内蒙古"),
    ("海南岛","第二大岛","中国","台湾岛","崇明岛"),("洞庭湖","第二大淡水湖","中国","鄱阳湖","太湖"),
    ("珠穆朗玛峰","最高峰","世界","乔戈里峰","干城章嘉"),("亚马逊河","流量最大","河流","尼罗河","长江"),
    # Science  
    ("水","零度结冰","物质","一百度","五十度"),("氧气","光合作用产生","气体","二氧化碳","氮气"),
    ("地球","第三行星","太阳系","第二行星","第四行星"),("月球","地球卫星","天体","行星","恒星"),
    ("火星","红色星球","太阳系","蓝色星球","绿色星球"),("光","速度最快","物理量","声音","热量"),
    ("金刚石","硬度最大","天然矿物","最软","密度最大"),("石油","不可再生","能源","可再生","无限"),
    ("维生素C","水果蔬菜含","营养素","肉类","谷物"),("鲸鱼","哺乳动物","动物","鱼类","爬行动物"),
    ("蝙蝠","唯一会飞","哺乳动物","会游泳","会爬树"),("企鹅","生活在南极","鸟类","北极","赤道"),
    ("银杏","活化石","植物","蕨类","藻类"),("铁","具有磁性","金属","没有","半磁"),
    ("臭氧层","吸收紫外线","大气层","反射可见光","吸收红外线"),("DNA","双螺旋结构","遗传物质","单螺旋","三螺旋"),
    ("一年","365天","时间","3650天","36天"),("三角形","三个角","几何图形","四个角","五个角"),
    ("正方形","四条边相等","四边形","不相等","部分相等"),("圆","没有角","几何图形","有四个角","有三个角"),
    # Daily
    ("苹果","水果","食物","蔬菜","谷物"),("熊猫","国宝","中国","国鸟","国花"),
    ("米饭","主食","中国","面包","面条"),("蜂蜜","蜜蜂酿造","食品","蝴蝶","蚂蚁"),
    ("咖啡","含咖啡因","饮料","茶碱","可可碱"),("自行车","两个轮子","交通工具","四个轮子","三个轮子"),
    ("手机","通话功能","设备","飞行","煮饭"),("火车","铁轨行驶","交通工具","公路","天空"),
    ("鱼","用鳃呼吸","动物","肺","皮肤"),("北极熊","生活在北极","动物","南极","赤道"),
    ("指南针","四大发明之一","中国古代","四大名著","四大古都"),("饺子","中国传统食物","食品","饮料","工具"),
    ("春节","最重要传统节日","中国","节气","节气"),("筷子","中国传统餐具","工具","武器","文具"),
    # Culture
    ("孔子","古代思想家","中国","军事家","医学家"),("北斗星","指示方向","星座","北极星","牛郎星"),
    ("汉语","官方语言之一","联合国","非官方语言","区域语言"),("长城","世界文化遗产","中国","世界自然遗产","世界地质"),
    ("丝绸","古代贸易商品","中国","农产品","工业品"),("中秋节","团圆节日","中国","丰收节日","祭祀节日"),
    ("端午节","纪念屈原","节日","李白","杜甫"),("故宫","位于北京","中国古建筑","西安","南京"),
    ("兵马俑","位于西安","秦代文物","北京","洛阳"),("西湖","位于杭州","中国名湖","苏州","扬州"),
    ("京剧","国粹","中国","国花","国树"),("茶","传统饮料","中国","传统食物","传统服装"),
    ("瓷器","CHINA同名","中国","日本","韩国"),
]

templates = [
    "{s}是{w1}的{w2}", "{s}位于{w1}", "{s}最著名的特点是{w2}",
    "在{w1}中，{s}是{w2}", "{s}以{w2}闻名",
]

def gen_cases(pool):
    cases = []
    for subj, prop1, prop2, w1, w2 in pool:
        for i, tmpl in enumerate(templates):
            if "{w1}" in tmpl and "{w2}" in tmpl:
                s = tmpl.format(s=subj, w1=prop1, w2=prop2)
            elif "{w1}" in tmpl:
                s = tmpl.format(s=subj, w1=prop1)
            else:
                s = tmpl.format(s=subj, w1=prop1, w2=prop2)
            q = f"关于{subj}，以下说法正确的是？"
            if i % 3 == 0:
                opts = [w1, subj, w2]
            elif i % 3 == 1:
                opts = [w2, subj, w1]
            else:
                opts = [w1, subj, prop2]
            cases.append((s, q, opts, 1))
    return cases

cases = gen_cases(POOL)
rng_src = random.Random(42)
rng_src.shuffle(cases)
cases = cases[:1000]
print(f"Generated {len(cases)} cases")

# =========== ENCODING ===========
def encode(text, mode):
    out = []
    for ch in text:
        r = lookup(ch)
        if mode == "unicode": out.append(ch)
        elif mode == "cnbe_full": out.append(f"0x{r['cnbe']:08X}" if r else ch)
        elif mode == "random_bitfield":
            v = r["cnbe"] ^ rng_enc.randint(0,0xFFFFFFFF) if r else rng_enc.randint(0,0xFFFFFFFF)
            out.append(f"0x{v&0xFFFFFFFF:08X}")
    return " ".join(out)

print("Pre-encoding...", flush=True)
t0 = time.time()
encoded = {enc: [encode(c[0], enc) for c in cases] for enc in ENCODERS}
print(f"Encoded in {time.time()-t0:.0f}s")

# =========== BATCH INFERENCE ===========
print("Loading model...", flush=True)
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained(BASE_PATH, device_map="auto", torch_dtype=torch.float16)
tokenizer = AutoTokenizer.from_pretrained(BASE_PATH)
tokenizer.padding_side = "left"
tokenizer.pad_token = tokenizer.eos_token

def make_prompt(enc_name, idx):
    tc = cases[idx]
    return f"编码文本: {encoded[enc_name][idx]}\n问题: {tc[1]}\n选项: {' '.join(f'{i}.{o}' for i,o in enumerate(tc[2]))}\n只输出选项编号:"

results = {}
t_start = time.time()
total_queries = 0
n = len(cases)

for enc in ENCODERS:
    print(f"\n{enc}:", flush=True)
    results[enc] = {"ok": 0, "n": n}
    correct = 0
    report_every = max(1, n // 10)
    
    for batch_start in range(0, n, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, n)
        batch_idx = list(range(batch_start, batch_end))
        prompts = [make_prompt(enc, i) for i in batch_idx]
        texts = [tokenizer.apply_chat_template([{"role":"user","content":p}], tokenize=False, add_generation_prompt=True) for p in prompts]
        inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=512).to(model.device)
        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=5, do_sample=False)
        responses = tokenizer.batch_decode(outputs[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        for bi, resp in zip(batch_idx, responses):
            m = re.search(r"\d+", resp.strip())
            parsed = int(m.group()) if m else None
            if parsed == cases[bi][3]: correct += 1
            total_queries += 1
        results[enc]["ok"] = correct
        
        if (batch_start // BATCH_SIZE + 1) % report_every == 0:
            print(f"  [{time.time()-t_start:3.0f}s] {batch_end}/{n}: {correct}/{batch_end} = {correct/batch_end*100:.1f}%", flush=True)
    
    print(f"  Done: {correct}/{n} = {correct/n*100:.1f}%", flush=True)

total_t = time.time() - t_start
print(f"\n{'='*50}")
print(f"1000-CASE BATCH EXPERIMENT")
print(f"{'='*50}")
print(f"Time: {total_t:.0f}s for {total_queries} queries ({total_queries/total_t:.1f} qps)")
for enc in ENCODERS:
    r = results[enc]; pct = r["ok"]/r["n"]*100
    bar = "█" * int(pct/5)
    print(f"  {enc:25s} {r['ok']:4d}/{r['n']} = {pct:5.1f}% {bar}")

# Save
outfile = os.path.join(RESULTS_DIR, "batch_1000_results.json")
json.dump({"n_cases":n,"encoders":ENCODERS,"total_queries":total_queries,"time_s":total_t,"results":results},
    open(outfile,"w"), indent=2)
print(f"\nSaved to {outfile}")
