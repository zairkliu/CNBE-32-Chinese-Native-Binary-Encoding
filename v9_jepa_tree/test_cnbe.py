import sys
sys.path.insert(0, r"C:\Users\zairk\Documents\Codex\2026-07-02\codex-dangerously-bypass-approvals-and-sandbox\v9_jepa_tree\src")
from cnbe_tree_encoder import CNBETreeEncoder
enc = CNBETreeEncoder()
import numpy as np
# Test the encoder
state = np.random.rand(10, 8).astype(np.float32)
encoded = enc.encode_state(state)
print("Shape:", encoded.shape)
print("Min:", encoded.min(), "Max:", encoded.max(), "Mean:", encoded.mean())
