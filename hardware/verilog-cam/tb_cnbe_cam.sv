// tb_cnbe_cam.sv — CNBE CAM 测试台
// 从 cnbe_table.h 和 unicode_table.h 加载数据验证 CAM 功能

module tb_cnbe_cam;

    logic        clk, rst_n;
    logic        lookup_en;
    logic [31:0] lookup_key;
    logic [31:0] lookup_value;
    logic        lookup_hit;
    logic        cfg_wr_en;
    logic [12:0] cfg_addr;
    logic [31:0] cfg_key, cfg_value;

    // 测试用数据 (实际验证时从文件加载)
    logic [31:0] test_keys   [0:9] = '{32'h4E00, 32'h4E59, 32'h4E8C, 32'h5341, 32'h4E01,
                                       32'h5382, 32'h4E03, 32'h516B, 32'h4EBA, 32'h5165};
    logic [31:0] test_values [0:9] = '{32'h01098000, 32'h05080000, 32'h07118000, 32'h18118000, 32'h01118000,
                                       32'h1B118000, 32'h01118010, 32'h00120008, 32'h09120009, 32'h0012000A};

    cnbe_cam_top u_dut (
        .clk, .rst_n, .lookup_en, .lookup_key, .lookup_value, .lookup_hit,
        .cfg_wr_en, .cfg_addr, .cfg_key, .cfg_value
    );

    // 时钟
    always #5 clk = ~clk;

    initial begin
        int pass = 0, fail = 0;

        $display("========================================");
        $display("CNBE-32 CAM Module Testbench");
        $display("========================================\n");

        clk = 0; rst_n = 0; lookup_en = 0;
        cfg_wr_en = 0; lookup_key = 0;
        #20 rst_n = 1;

        // Phase 1: 写入 10 条测试数据
        $display("[Phase 1] Writing %0d test entries...", 10);
        for (int i = 0; i < 10; i++) begin
            @(posedge clk);
            cfg_wr_en = 1;
            cfg_addr  = i;
            cfg_key   = test_keys[i];
            cfg_value = test_values[i];
        end
        @(posedge clk); cfg_wr_en = 0;

        // Phase 2: 验证每条数据
        $display("\n[Phase 2] Verifying %0d lookups...", 10);
        for (int i = 0; i < 10; i++) begin
            @(posedge clk);
            lookup_en  = 1;
            lookup_key = test_keys[i];
            @(negedge clk);
            if (lookup_hit && lookup_value == test_values[i]) begin
                $display("  [%0d] PASS: U+%h -> 0x%h", i, lookup_key, lookup_value);
                pass++;
            end else begin
                $display("  [%0d] FAIL: U+%h expected 0x%h got 0x%h (hit=%b)",
                         i, lookup_key, test_values[i], lookup_value, lookup_hit);
                fail++;
            end
        end
        @(posedge clk); lookup_en = 0;

        // Phase 3: 测试未命中
        @(posedge clk);
        lookup_en  = 1;
        lookup_key = 32'hFFFFFFFF;  // 不存在
        @(negedge clk);
        if (!lookup_hit) begin
            $display("\n[Phase 3] PASS: Non-existent key correctly missed");
            pass++;
        end else begin
            $display("\n[Phase 3] FAIL: Non-existent key incorrectly hit");
            fail++;
        end
        @(posedge clk); lookup_en = 0;

        $display("\n========================================");
        $display("Results: %0d PASS, %0d FAIL", pass, fail);
        $display("========================================");
        $finish;
    end

endmodule
