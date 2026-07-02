// cam_bank.sv — CAM Bank: 128 条目并行比较器
// 每个条目: 32-bit key + 32-bit value + valid flag

module cam_bank #(
    parameter ENTRIES    = 128,
    parameter KEY_WIDTH  = 32,
    parameter VALUE_WIDTH = 32
) (
    input  logic              clk,
    input  logic              rst_n,
    input  logic              lookup_en,
    input  logic [KEY_WIDTH-1:0]   lookup_key,
    input  logic [5:0]        bank_id,
    output logic [VALUE_WIDTH-1:0] lookup_value,
    output logic              lookup_hit,
    input  logic              cfg_wr_en,
    input  logic [6:0]        cfg_addr,
    input  logic [KEY_WIDTH-1:0]   cfg_key,
    input  logic [VALUE_WIDTH-1:0] cfg_value
);

    // CAM 存储单元
    logic [KEY_WIDTH-1:0]   key_mem   [ENTRIES];
    logic [VALUE_WIDTH-1:0] value_mem [ENTRIES];
    logic                   valid_mem [ENTRIES];

    // 配置写入
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < ENTRIES; i++) begin
                valid_mem[i] <= '0;
                key_mem[i]   <= '0;
                value_mem[i] <= '0;
            end
        end else if (cfg_wr_en) begin
            key_mem[cfg_addr]   <= cfg_key;
            value_mem[cfg_addr] <= cfg_value;
            valid_mem[cfg_addr] <= 1'b1;
        end
    end

    // 并行比较: 所有有效条目同时比较
    logic [ENTRIES-1:0] match_lines;
    genvar i;
    generate
        for (i = 0; i < ENTRIES; i++) begin : gen_rows
            cam_row #(
                .KEY_WIDTH(KEY_WIDTH),
                .VALUE_WIDTH(VALUE_WIDTH)
            ) u_row (
                .clk       (clk),
                .rst_n     (rst_n),
                .lookup_en (lookup_en),
                .lookup_key(lookup_key),
                .stored_key(key_mem[i]),
                .stored_val(value_mem[i]),
                .valid     (valid_mem[i]),
                .match     (match_lines[i])
            );
        end
    endgenerate

    // 优先级编码器 (索引优先)
    logic [$clog2(ENTRIES)-1:0] match_idx;
    priority_encoder #(
        .WIDTH(ENTRIES)
    ) u_row_enc (
        .input_bits (match_lines),
        .index      (match_idx),
        .valid      (lookup_hit)
    );

    // 输出
    always_comb begin
        if (lookup_hit)
            lookup_value = value_mem[match_idx];
        else
            lookup_value = '0;
    end

endmodule
