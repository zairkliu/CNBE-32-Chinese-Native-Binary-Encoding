// priority_encoder.sv — 优先编码器 (最低索引优先)
// 用于 CAM 匹配线的优先级编码

module priority_encoder #(
    parameter WIDTH = 128
) (
    input  logic [WIDTH-1:0]       input_bits,
    output logic [$clog2(WIDTH)-1:0] index,
    output logic                   valid
);

    logic [$clog2(WIDTH)-1:0] idx;
    logic v;

    always_comb begin
        idx = '0;
        v   = 1'b0;
        for (int i = 0; i < WIDTH; i++) begin
            if (input_bits[i] && !v) begin
                idx = i[$clog2(WIDTH)-1:0];
                v   = 1'b1;
            end
        end
    end

    assign index = idx;
    assign valid = v;

endmodule
