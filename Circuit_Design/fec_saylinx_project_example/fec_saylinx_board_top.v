module fec_saylinx_board_top
(
    input           CLK,
    input           RST_N,

    input           KEY2_N,
    input           KEY3_N,
    input           KEY4_N,

    output [3:0]    LED,

    output [7:0] SEG_DATA,
    output [7:0] SEG_SEL,

    output [16:0] GPIO_0_out_zero_value, // {R13, R12, R11, R10, R9, R8, R7, R6, R5, R4, R3, P3, M9, L9, P8, P2, N2}
    input  [16:0] GPIO_0_input_pullup, // {T14, T13, T12, T11, T10, T9, T8, T7, T6, T5, T4, T3, T2, L10, K9, R1, P1}
	 
	 output [16:0] GPIO_1_out_zero_value, // {E8, C8, E7, D6, A13, A12, A11, A10, A9, A8, A7, A6, A5, A4, A3, A2, C2(J16 mark on Saylinx board)}
    input  [16:0] GPIO_1_input_pullup // {E9, D8, F8, C6, D5, B13, B12, B11, B10, B9, B8, B7, B6, B5, B4, B3, B2}
);

    //------------------------------------------------------------------------

    wire clk;
    wire rst;

    assign clk = CLK;
    assign rst = ~ RST_N;

    // Buttons 
    wire [2:0] key;

    assign key = ~ { KEY2_N, KEY3_N, KEY4_N };

    // Seven-segment display
    wire [7:0] abcdefgh;
    wire [7:0] digit;

    assign SEG_DATA = abcdefgh;
    assign SEG_SEL = digit;

    // Zero constant value output pins
    assign GPIO_0_out_zero_value = {17{1'b0}};
    assign GPIO_1_out_zero_value = {17{1'b0}};


endmodule
