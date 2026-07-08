# Fix CNBE encoder normalization
path = r"C:\Users\zairk\Documents\Codex\2026-07-02\codex-dangerously-bypass-approvals-and-sandbox\v9_jepa_tree\src\cnbe_tree_encoder.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find encode_state method for CNBETreeEncoder class and add normalization
in_class = False
in_encode_state = False
fixed = False
new_lines = []
for i, line in enumerate(lines):
    if "class CNBETreeEncoder" in line:
        in_class = True
    if in_class and "def encode_state" in line:
        in_encode_state = True
    if in_encode_state and "return codes.astype(np.float32)" in line:
        line = line.replace("return codes.astype(np.float32)", "return codes.astype(np.float32) / 4294967295.0")
        fixed = True
    if in_encode_state and line.strip().startswith("def ") and "encode_state" not in line:
        in_encode_state = False
    new_lines.append(line)

if fixed:
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("CNBE encoder normalization FIXED")
else:
    print("Pattern not found!")
    # Show the relevant lines
    for i, line in enumerate(lines):
        if "encode_state" in line or "return codes" in line:
            print(f"  Line {i+1}: {line.rstrip()}")
