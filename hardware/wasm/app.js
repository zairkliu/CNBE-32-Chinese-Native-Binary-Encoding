// CNBE-32 WASM glue code
let Module = null;
const structNames = ["独体","左右","左中右","上下","上中下","左上包围","右上包围","左下包围","上包围","下包围","左包围","全包围","三角形"];

async function initWasm() {
    const status = document.getElementById("status");
    try {
        // Try to fetch the WASM module
        const response = await fetch("cnbe_wasm.wasm");
        const bytes = await response.arrayBuffer();
        const wasm = await WebAssembly.instantiate(bytes, {
            env: { memory: new WebAssembly.Memory({ initial: 1 }), abort: () => {} }
        });
        Module = wasm.instance.exports;
        status.textContent = "WASM 模块已加载，编码器就绪";
        document.getElementById("encodeBtn").disabled = false;
    } catch(e) {
        // Fallback: pure JS implementation
        console.log("WASM not available, using JS fallback");
        status.textContent = "JS 回退模式（WASM 不可用）";
        Module = createJsFallback();
        document.getElementById("encodeBtn").disabled = false;
    }
}

function createJsFallback() {
    const RADIX_SHIFT = 24, STROKE_SHIFT = 19, STRUCT_SHIFT = 15, INDEX_SHIFT = 4;
    return {
        cnbe_encode: (r,s,t,i,e) => ((r&0xFF)<<RADIX_SHIFT)|((s&0x1F)<<STROKE_SHIFT)|((t&0xF)<<STRUCT_SHIFT)|((i&0x7FF)<<INDEX_SHIFT)|(e&0xF),
        cnbe_radix: (c) => (c>>>RADIX_SHIFT)&0xFF,
        cnbe_stroke: (c) => (c>>>STROKE_SHIFT)&0x1F,
        cnbe_struct_type: (c) => (c>>>STRUCT_SHIFT)&0xF,
        cnbe_index: (c) => (c>>>INDEX_SHIFT)&0x7FF,
        cnbe_extension: (c) => c&0xF,
        cnbe_distance: (a,b) => {
            const ra=(a>>>RADIX_SHIFT)&0xFF,rb=(b>>>RADIX_SHIFT)&0xFF;
            const sa=(a>>>STROKE_SHIFT)&0x1F,sb=(b>>>STROKE_SHIFT)&0x1F;
            const ta=(a>>>STRUCT_SHIFT)&0xF,tb=(b>>>STRUCT_SHIFT)&0xF;
            const ia=(a>>>INDEX_SHIFT)&0x7FF,ib=(b>>>INDEX_SHIFT)&0x7FF;
            return Math.abs(ra-rb)*8+Math.abs(sa-sb)*5+Math.abs(ta-tb)*4+Math.abs(ia-ib);
        }
    };
}

function encode() {
    const charInput = document.getElementById("charInput").value.trim();
    const radix = parseInt(document.getElementById("radixInput").value) || 72;
    const stroke = parseInt(document.getElementById("strokeInput").value) || 8;
    const struct = parseInt(document.getElementById("structInput").value) || 1;
    const index = parseInt(document.getElementById("indexInput").value) || 0;

    const code = Module.cnbe_encode(radix, stroke, struct, index, 0);
    displayResult(code, radix, stroke, struct, index);
}

function displayResult(code, radix, stroke, struct, index) {
    const r = Module.cnbe_radix(code);
    const s = Module.cnbe_stroke(code);
    const t = Module.cnbe_struct_type(code);
    const i = Module.cnbe_index(code);
    const e = Module.cnbe_extension(code);

    document.getElementById("hexValue").textContent = "0x" + (code >>> 0).toString(16).padStart(8, "0");
    document.getElementById("binaryValue").textContent = (code >>> 0).toString(2).padStart(32, "0").replace(/(.{4})/g,"$1 ");
    document.getElementById("fieldRadix").textContent = r + " (0x" + r.toString(16) + ")";
    document.getElementById("fieldStroke").textContent = s;
    document.getElementById("fieldStruct").textContent = t + " (" + (structNames[t] || "未知") + ")";
    document.getElementById("fieldIndex").textContent = i;
    document.getElementById("fieldExt").textContent = e;

    document.getElementById("resultPlaceholder").style.display = "none";
    document.getElementById("resultArea").style.display = "block";
}

document.addEventListener("DOMContentLoaded", () => {
    initWasm();
    document.getElementById("encodeBtn").addEventListener("click", encode);
    document.getElementById("manualEncodeBtn").addEventListener("click", encode);
    document.getElementById("charInput").addEventListener("keydown", (e) => {
        if (e.key === "Enter") encode();
    });
});
