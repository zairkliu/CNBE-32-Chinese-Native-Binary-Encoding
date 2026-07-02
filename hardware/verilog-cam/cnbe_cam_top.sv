//======================================================================
// cnbe_cam_top.sv — CNBE-32 CAM 顶层模块
// 功能: 内容可寻址存储器, 32-bit Unicode → 32-bit CNBE 编码
// 容量: 8105 条目
// 延迟: 单周期 (组合逻辑查找 + 优先级编码)
//
// 架构: 64个 Bank, 每个 Bank 128 个条目
//   Bank 选择: key[6:0] (0-127, 但Banks 64-127 实际未用)
//   每个 Bank: 128 × 32-bit 比较器并行
//======================================================================

module cnbe_cam_top (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        lookup_en,
    input  logic [31:0] lookup_key,       // Unicode 输入
    output logic [31:0] lookup_value,      // CNBE 编码输出
    output logic        lookup_hit,        // 查找命中
    // 配置接口 (初始化阶段写入 CAM 条目)
    input  logic        cfg_wr_en,
    input  logic [12:0] cfg_addr,         // 0-8104
    input  logic [31:0] cfg_key,          // Unicode 码点
    input  logic [31:0] cfg_value         // CNBE 编码
);

    //==================================================================
    // 参数
    //==================================================================
    localparam ENTRIES = 8105;
    localparam BANKS   = 64;    // 64 banks × 128 entries = 8192 (> 8105)
    localparam ENTRIES_PER_BANK = 128;

    //==================================================================
    // 内部信号
    //==================================================================
    logic [BANKS-1:0]      bank_match;          // 每个Bank的匹配信号
    logic [31:0]           bank_value [BANKS];  // 每个Bank输出的值
    logic [BANKS-1:0]      bank_hit;
    logic [12:0]           bank_entry_addr;     // Bank内地址
    logic [5:0]            bank_id;             // Bank编号 (0-63)

    //==================================================================
    // Bank 实例化 (每个Bank 128 个条目)
    //==================================================================
    genvar b;
    generate
        for (b = 0; b < BANKS; b++) begin : gen_banks
            cam_bank #(
                .ENTRIES(ENTRIES_PER_BANK),
                .KEY_WIDTH(32),
                .VALUE_WIDTH(32)
            ) u_bank (
                .clk           (clk),
                .rst_n         (rst_n),
                .lookup_en     (lookup_en),
                .lookup_key    (lookup_key),
                .bank_id       (b[5:0]),
                .lookup_value  (bank_value[b]),
                .lookup_hit    (bank_hit[b]),
                .cfg_wr_en     (cfg_wr_en && (cfg_addr[12:7] == b[5:0])),
                .cfg_addr      (cfg_addr[6:0]),
                .cfg_key       (cfg_key),
                .cfg_value     (cfg_value)
            );
        end
    endgenerate

    //==================================================================
    // 优先级编码器: 从匹配的 Bank 中选第一个
    //==================================================================
    priority_encoder #(
        .WIDTH(BANKS)
    ) u_pri_enc (
        .input_bits (bank_hit),
        .index      (bank_id),
        .valid      (lookup_hit)
    );

    // 输出选择
    always_comb begin
        if (lookup_hit && lookup_en)
            lookup_value = bank_value[bank_id];
        else
            lookup_value = '0;
    end

endmodule
