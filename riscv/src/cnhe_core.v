// cnhe_core.v - CNBE-32 FPGA implementation
// Implements cnhe.map, cnhe.extract, cnhe.cmp

module cnhe_core (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        valid,
    input  wire [31:0] insn,
    input  wire [31:0] rs1,
    input  wire [31:0] rs2,
    output reg         ready,
    output reg  [31:0] rd
);

    reg [31:0] rom [0:20901];

    initial begin
        $readmemh("skill_table.hex", rom);
    end

    wire [6:0]  opcode = insn[6:0];
    wire [2:0]  funct3 = insn[14:12];
    wire        is_custom0 = (opcode == 7'h0B);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ready <= 1'b0;
            rd <= 32'h0;
        end else if (valid && is_custom0) begin
            case (funct3)
                3'b000: begin // cnhe.map
                    if (rs1 >= 32'h4E00 && rs1 <= 32'h9FA5)
                        rd <= rom[rs1 - 32'h4E00];
                    else
                        rd <= 32'h0;
                end
                3'b001: begin // cnhe.extract
                    case (rs2[2:0])
                        3'd0: rd <= (rs1 >> 24) & 8'hFF;
                        3'd1: rd <= (rs1 >> 19) & 5'h1F;
                        3'd2: rd <= (rs1 >> 15) & 4'h0F;
                        3'd3: rd <= (rs1 >>  4) & 12'h7FF;
                        default: rd <= 32'h0;
                    endcase
                end
                3'b010: begin // cnhe.cmp
                    rd <= $countones(rs1 ^ rs2);
                end
                default: rd <= 32'h0;
            endcase
            ready <= 1'b1;
        end else begin
            ready <= 1'b0;
        end
    end
endmodule
