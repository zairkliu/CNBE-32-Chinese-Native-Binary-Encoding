`include "cnbe_table_params.svh"

module cnbe_exec (
    input  wire [31:0] insn,
    input  wire [31:0] rs1_data,
    input  wire [31:0] rs2_data,
    output reg  [31:0] rd_data,
    output reg         valid
);

    reg [31:0] unicode_mem [0:CNBE_TABLE_SIZE-1];
    reg [31:0] cnbe_mem    [0:CNBE_TABLE_SIZE-1];
    integer j, lo, hi, mid;
    reg found;

    wire [2:0] funct3 = insn[14:12];
    wire [4:0] rs1    = insn[19:15];
    wire [4:0] rs2    = insn[24:20];
    wire [4:0] rd     = insn[11:7];

    initial begin
        $readmemh("generated/unicode_table.hex", unicode_mem);
        $readmemh("generated/cnbe_table.hex", cnbe_mem);
    end

    function [31:0] lookup;
        input [31:0] ucp;
        integer j;
        begin
            for (j = 0; j < CNBE_TABLE_SIZE; j = j + 1) begin
                if (unicode_mem[j] == ucp) begin
                    return cnbe_mem[j];
                end
            end
            return 0;
        end
    endfunction

    function [31:0] reverse_lookup;
        input [31:0] code;
        integer j;
        begin
            for (j = 0; j < CNBE_TABLE_SIZE; j = j + 1) begin
                if (cnbe_mem[j] == code) begin
                    return unicode_mem[j];
                end
            end
            return 0;
        end
    endfunction

    function [31:0] extract_field;
        input [31:0] code;
        input [31:0] selector;
        begin
            case (selector)
                0: extract_field = (code >> 24) & 32'hFF;
                1: extract_field = (code >> 19) & 32'h1F;
                2: extract_field = (code >> 15) & 32'h0F;
                3: extract_field = (code >> 4)  & 32'h7FF;
                4: extract_field = code & 32'hF;
                default: extract_field = 0;
            endcase
        end
    endfunction

    function [31:0] field_distance;
        input [31:0] a;
        input [31:0] b;
        reg [7:0] ra, rb, sa, sb, ta, tb;
        reg [31:0] dr, ds, dt;
        begin
            ra = (a >> 24) & 8'hFF; rb = (b >> 24) & 8'hFF;
            sa = (a >> 19) & 8'h1F; sb = (b >> 19) & 8'h1F;
            ta = (a >> 15) & 8'h0F; tb = (b >> 15) & 8'h0F;
            dr = ra > rb ? ra - rb : rb - ra;
            ds = sa > sb ? sa - sb : sb - sa;
            dt = ta > tb ? ta - tb : tb - ta;
            field_distance = dr * 8 + ds * 5 + dt * 4;
        end
    endfunction

    always @(insn or rs1_data or rs2_data) begin
        rd_data = 0;
        valid = 0;
        if (insn[6:0] == 7'h0B) begin
            valid = 1;
            case (funct3)
                3'h0: begin
                    lo = 0;
                    hi = CNBE_TABLE_SIZE - 1;
                    found = 0;
                    rd_data = 0;
                    while (!found && lo <= hi) begin
                        mid = (lo + hi) / 2;
                        if (unicode_mem[mid] == rs1_data) begin
                            rd_data = cnbe_mem[mid];
                            found = 1;
                        end else if (unicode_mem[mid] < rs1_data) begin
                            lo = mid + 1;
                        end else begin
                            hi = mid - 1;
                        end
                    end
                end
                3'h1: rd_data = extract_field(rs1_data, rs2_data);
                3'h2: rd_data = field_distance(rs1_data, rs2_data);
                3'h3: begin
                    rd_data = 0;
                    found = 0;
                    for (j = 0; j < CNBE_TABLE_SIZE; j = j + 1) begin
                        if (!found && cnbe_mem[j] == rs1_data) begin
                            rd_data = unicode_mem[j];
                            found = 1;
                        end
                    end
                end
                default: begin
                    rd_data = 0;
                    valid = 0;
                end
            endcase
        end
    end

endmodule
