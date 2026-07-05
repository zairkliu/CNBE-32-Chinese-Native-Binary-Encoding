`timescale 1ns/1ps
module tb_cnhe();
    reg clk, rst_n, valid;
    reg [31:0] insn, rs1, rs2;
    wire ready;
    wire [31:0] rd;
    integer pass=0, fail=0, i;

    cnhe_core uut(.*);

    always #5 clk = ~clk;

    reg [31:0] expected [0:11];
    reg [31:0] testvals [0:11];

    initial begin
        clk=0; rst_n=0; valid=0; insn=0; rs1=0; rs2=0;
        #12 rst_n=1; #10;

        // Test 1-4: cnhe.map known codes
        testvals[0]=32'h5B66; expected[0]=32'h274C6010; // 学
        testvals[1]=32'h7535; expected[1]=32'h66040220; // 电
        testvals[2]=32'h4E2D; expected[2]=32'h04400110; // 中
        testvals[3]=32'h6C34; expected[3]=32'h55040000; // 水

        // Test 5-8: cnhe.map more chars
        testvals[4]=32'h6C22; // 氢
        testvals[5]=32'h9502; // 锂
        testvals[6]=32'h78B3; // 碳
        testvals[7]=32'h6C27; // 氧

        // Test 9-10: cnhe.extract (field=0 radical, field=1 stroke)
        testvals[8]=32'h274C6010; // CNBE code for 学
        testvals[9]=32'h274C6010;

        // Test 11-12: cnhe.cmp
        testvals[10]=32'hFFFFFFFF;
        testvals[11]=0;

        for (i=0; i<8; i=i+1) begin
            @(posedge clk);
            valid <= 1; insn <= 32'h0000000B; rs1 <= testvals[i]; #10;
            valid <= 0;
            @(posedge clk);
            if (rd !== expected[i]) begin
                $display("FAIL[%0d] cnhe.map 0x%X: got 0x%X exp 0x%X", i, testvals[i], rd, expected[i]);
                fail = fail + 1;
            end else begin
                $display("PASS[%0d] cnhe.map 0x%X = 0x%X", i, testvals[i], rd);
                pass = pass + 1;
            end
        end

        // cnhe.extract radical
        @(posedge clk);
        valid <= 1; insn <= 32'h0000100B; rs1 <= testvals[8]; rs2 <= 0; #10;
        valid <= 0;
        @(posedge clk);
        if (rd !== 39) begin
            $display("FAIL[8] extract radical: got %0d exp 39", rd); fail=fail+1;
        end else begin
            $display("PASS[8] extract radical = %0d", rd); pass=pass+1;
        end

        // cnhe.extract stroke
        @(posedge clk);
        valid <= 1; insn <= 32'h0000100B; rs1 <= testvals[9]; rs2 <= 1; #10;
        valid <= 0;
        @(posedge clk);
        if (rd !== 8) begin
            $display("FAIL[9] extract stroke: got %0d exp 8", rd); fail=fail+1;
        end else begin
            $display("PASS[9] extract stroke = %0d", rd); pass=pass+1;
        end

        // cnhe.cmp (same)
        @(posedge clk);
        valid <= 1; insn <= 32'h0000200B; rs1 <= testvals[10]; rs2 <= testvals[10]; #10;
        valid <= 0;
        @(posedge clk);
        if (rd !== 0) begin
            $display("FAIL[10] cmp same: got %0d exp 0", rd); fail=fail+1;
        end else begin
            $display("PASS[10] cmp same = %0d", rd); pass=pass+1;
        end

        // cnhe.cmp (different)
        @(posedge clk);
        valid <= 1; insn <= 32'h0000200B; rs1 <= testvals[10]; rs2 <= testvals[11]; #10;
        valid <= 0;
        @(posedge clk);
        if (rd !== 32) begin
            $display("FAIL[11] cmp diff: got %0d exp 32", rd); fail=fail+1;
        end else begin
            $display("PASS[11] cmp diff = %0d", rd); pass=pass+1;
        end

        $display("---");
        $display("Results: %0d passed, %0d failed, %0d total", pass, fail, pass+fail);
        $display("---Perf: 50k cycles---");
        for (i=0; i<50000; i=i+1) begin
            @(posedge clk);
            valid <= 1; insn <= 32'h0000000B; rs1 <= 32'h4E00 + (i % 100); #2;
            valid <= 0;
        end
        $display("Done: 50000 lookups");
        $finish;
    end
endmodule
