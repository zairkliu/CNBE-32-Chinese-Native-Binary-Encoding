#!/usr/bin/env python3
"""Generate CNBE-32 binary mapping table + SQLite DB + JSON mapping"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import numpy as np, os, json, sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from cnbe32.constants import RADIX_SHIFT, STROKE_SHIFT, STRUCT_SHIFT, INDEX_SHIFT, INDEX_MASK, STRUCT_NAMES, CJK_UNICODE_COUNT

OUT = os.path.join(os.path.dirname(__file__), "..", "data")
TABLE_SIZE = CJK_UNICODE_COUNT

RADIX_NAMES = {
    1:"一",2:"丨",3:"丶",4:"丿",5:"乙",6:"亅",7:"二",8:"亠",9:"人",10:"儿",
    11:"入",12:"八",13:"冂",14:"冖",15:"冫",16:"几",17:"凵",18:"刀",19:"力",20:"勹",
    21:"匕",22:"匚",23:"匸",24:"十",25:"卜",26:"卩",27:"厂",28:"厶",29:"又",30:"口",
    31:"囗",32:"土",33:"士",34:"夂",35:"夊",36:"夕",37:"大",38:"女",39:"子",40:"宀",
    41:"寸",42:"小",43:"尢",44:"尸",45:"屮",46:"山",47:"巛",48:"工",49:"己",50:"巾",
    51:"干",52:"幺",53:"广",54:"廴",55:"廾",56:"弋",57:"弓",58:"彐",59:"彡",60:"彳",
    61:"心",62:"戈",63:"戶",64:"手",65:"支",66:"攴",67:"文",68:"斗",69:"斤",70:"方",
    71:"无",72:"日",73:"曰",74:"月",75:"木",76:"欠",77:"止",78:"歹",79:"殳",80:"母",
    81:"比",82:"毛",83:"氏",84:"气",85:"水",86:"火",87:"爪",88:"父",89:"爻",90:"爿",
    91:"片",92:"牙",93:"牛",94:"犬",95:"王",96:"玄",97:"瓜",98:"瓦",99:"甘",100:"生",
    101:"用",102:"田",103:"疋",104:"疒",105:"癶",106:"白",107:"皮",108:"皿",109:"目",110:"矛",
    111:"矢",112:"石",113:"示",114:"禸",115:"禾",116:"穴",117:"立",118:"竹",119:"米",120:"糸",
    121:"缶",122:"网",123:"羊",124:"羽",125:"老",126:"而",127:"耒",128:"耳",129:"聿",130:"肉",
    131:"臣",132:"自",133:"至",134:"臼",135:"舌",136:"舛",137:"舟",138:"艮",139:"色",140:"艸",
    141:"虍",142:"虫",143:"血",144:"行",145:"衣",146:"西",147:"見",148:"角",149:"言",150:"谷",
    151:"豆",152:"豕",153:"豸",154:"貝",155:"赤",156:"走",157:"足",158:"身",159:"車",160:"辛",
    161:"辰",162:"辵",163:"邑",164:"酉",165:"釆",166:"里",167:"金",168:"長",169:"門",170:"阜",
    171:"隶",172:"隹",173:"雨",174:"青",175:"非",176:"面",177:"革",178:"韋",179:"韭",180:"音",
    181:"頁",182:"風",183:"飛",184:"食",185:"首",186:"香",187:"馬",188:"骨",189:"高",190:"髟",
    191:"鬥",192:"鬯",193:"鬲",194:"鬼",195:"魚",196:"鳥",197:"鹵",198:"鹿",199:"麥",200:"麻",
    201:"黃",202:"黍",203:"黑",204:"黹",205:"黽",206:"鼎",207:"鼓",208:"鼠",209:"鼻",210:"齊",
    211:"齒",212:"龍",213:"龜",214:"龠",
}

def build_table():
    """Generate encoding table with all fields"""
    table = []
    for i in range(TABLE_SIZE):
        unicode_cp = 0x4E00 + i
        radix = (i % 214) + 1
        stroke = (i % 31) + 1
        struct = i % 13
        index_val = i & INDEX_MASK
        code = (radix << RADIX_SHIFT) | (stroke << STROKE_SHIFT) | (struct << STRUCT_SHIFT) | (index_val << INDEX_SHIFT)
        table.append({
            "unicode": unicode_cp,
            "char": chr(unicode_cp),
            "cnbe": code,
            "radix": radix,
            "radix_name": RADIX_NAMES.get(radix, f"radix_{radix}"),
            "strokes": stroke,
            "struct_type": struct,
            "struct_name": STRUCT_NAMES.get(struct, "unknown"),
            "index": index_val,
        })
    return table

def build_db(table):
    """Build SQLite database from encoding table"""
    db_path = os.path.join(OUT, "cnbe32.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE cnbe32 (
            unicode INTEGER PRIMARY KEY,
            char TEXT,
            cnbe INTEGER,
            radix INTEGER,
            radix_name TEXT,
            strokes INTEGER,
            struct_type INTEGER,
            struct_name TEXT,
            idx INTEGER
        )
    """)
    c.execute("CREATE INDEX idx_cnbe ON cnbe32(cnbe)")
    c.execute("CREATE INDEX idx_radix ON cnbe32(radix)")
    c.execute("CREATE INDEX idx_strokes ON cnbe32(strokes)")
    for row in table:
        c.execute("INSERT INTO cnbe32 VALUES (?,?,?,?,?,?,?,?,?)",
                  (row["unicode"], row["char"], row["cnbe"], row["radix"],
                   row["radix_name"], row["strokes"], row["struct_type"],
                   row["struct_name"], row["index"]))
    conn.commit()
    conn.close()
    print(f"SQLite DB: {db_path} ({len(table)} entries)")

def build_json(table):
    """Build JSON mapping file from encoding table"""
    json_path = os.path.join(OUT, "cnbe32.json")
    metadata = {
        "version": "0.3.1",
        "total": len(table),
        "generated": "2026-07-09",
        "index_shift": INDEX_SHIFT,
        "index_bits": 11,
        "index_mask": INDEX_MASK,
    }
    data = {"metadata": metadata, "characters": table}
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"JSON: {json_path} ({len(table)} entries)")

def build_bin(table):
    """Build binary skill table (.bin + .npy)"""
    arr = np.array([r["cnbe"] for r in table], dtype=np.uint32)
    np.save(os.path.join(OUT, "skill_table.npy"), arr)
    arr.tofile(os.path.join(OUT, "skill_table.bin"))
    print(f"Binary: skill_table.bin + skill_table.npy ({len(arr)} entries)")

def main():
    os.makedirs(os.path.dirname(OUT) if os.path.dirname(OUT) else ".", exist_ok=True)
    print(f"Generating CNBE-32 encoding table ({TABLE_SIZE} characters)...")
    table = build_table()
    build_db(table)
    build_json(table)
    build_bin(table)
    print("Done!")

if __name__ == "__main__":
    main()
