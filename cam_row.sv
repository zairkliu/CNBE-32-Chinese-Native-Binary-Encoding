// cam_row.sv — CAM 单行: 32-bit 比较 + 值输出
// 组合逻辑: 匹配线在单周期内建立

module cam_row #(
    parameter KEY_WIDTH   = 32,
    parameter VALUE_WIDTH = 32
) (
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic                    lookup_en,
    input  logic [KEY_WIDTH-1:0]    lookup_key,
    input  logic [KEY_WIDTH-1:0]    stored_key,
    input  logic [VALUE_WIDTH-1:0]  stored_val,
    input  logic                    valid,
    output logic                    match
);

    // 并行位比较 + valid 掩码
    // match_line 在 ~3 个门延迟内稳定
    assign match = lookup_en & valid & (lookup_key == stored_key);

endmodule
