`timescale 1ns / 1ps

module tb_cnbe_exec;

    reg  [31:0] insn;
    reg  [31:0] rs1_data;
    reg  [31:0] rs2_data;
    wire [31:0] rd_data;
    wire        valid;

    cnbe_exec dut (
        .insn(insn),
        .rs1_data(rs1_data),
        .rs2_data(rs2_data),
        .rd_data(rd_data),
        .valid(valid)
    );

    integer f, status, pass, fail, have_prev;
    reg [511:0] name;
    integer uni, code, rad, stk, str, gidx, ext, revu, distv;
    integer prev_c;
    integer sel;

    initial begin
        pass = 0;
        fail = 0;
        have_prev = 0;
        prev_c = 0;
        f = $fopen("golden/qemu_expected.txt", "r");
        if (f == 0) begin
            $display("FAIL: cannot open golden/qemu_expected.txt");
            $finish(1);
        end

        while (!$feof(f)) begin
            status = $fscanf(f, "%s %h %h %d %d %d %d %d %h %d",
                             name, uni, code, rad, stk, str, gidx, ext, revu, distv);
            if (status != 10) begin
                // EOF or malformed line; loop ends on $feof.
            end else begin
                // cnbe.map rd=11, rs1=10
                insn = (10 << 15) | (11 << 7) | 8'h0B;
                rs1_data = uni;
                #1;
                if (rd_data != code) begin
                    $display("FAIL map U+%04X got %08X expected %08X", uni, rd_data, code);
                    fail = fail + 1;
                end else begin
                    pass = pass + 1;
                end

                // cnbe.extract rd=12, rs1=10, rs2=11
                for (sel = 0; sel < 5; sel = sel + 1) begin
                    insn = (sel << 20) | (10 << 15) | (3'b001 << 12) | (12 << 7) | 8'h0B;
                    rs1_data = code;
                    rs2_data = sel;
                    #1;
                    if (sel == 0) begin
                        if (rd_data != rad) begin
                            $display("FAIL extract radix U+%04X", uni);
                            fail = fail + 1;
                        end else pass = pass + 1;
                    end
                    if (sel == 1) begin
                        if (rd_data != stk) begin
                            $display("FAIL extract stroke U+%04X", uni);
                            fail = fail + 1;
                        end else pass = pass + 1;
                    end
                    if (sel == 2) begin
                        if (rd_data != str) begin
                            $display("FAIL extract struct U+%04X", uni);
                            fail = fail + 1;
                        end else pass = pass + 1;
                    end
                    if (sel == 3) begin
                        if (rd_data != gidx) begin
                            $display("FAIL extract idx U+%04X", uni);
                            fail = fail + 1;
                        end else pass = pass + 1;
                    end
                    if (sel == 4) begin
                        if (rd_data != ext) begin
                            $display("FAIL extract ext U+%04X", uni);
                            fail = fail + 1;
                        end else pass = pass + 1;
                    end
                end

                // cnbe.cmp rd=12, rs1=10, rs2=11
                if (have_prev) begin
                    insn = (11 << 20) | (10 << 15) | (3'b010 << 12) | (12 << 7) | 8'h0B;
                    rs1_data = prev_c;
                    rs2_data = code;
                    #1;
                    if (rd_data != distv) begin
                        $display("FAIL cmp got %0d expected %0d", rd_data, distv);
                        fail = fail + 1;
                    end else begin
                        pass = pass + 1;
                    end
                end

                // cnbe.skill rd=13, rs1=10
                insn = (10 << 15) | (3'b011 << 12) | (13 << 7) | 8'h0B;
                rs1_data = code;
                #1;
                if (rd_data != revu) begin
                    $display("FAIL skill got %04X expected %04X", rd_data, revu);
                    fail = fail + 1;
                end else begin
                    pass = pass + 1;
                end

                prev_c = code;
                have_prev = 1;
            end
        end

        $fclose(f);
        $display("CNBE-32 v8 Verilog test: %0d passed, %0d failed", pass, fail);
        if (fail == 0) begin
            $finish(0);
        end else begin
            $finish(1);
        end
    end

endmodule
