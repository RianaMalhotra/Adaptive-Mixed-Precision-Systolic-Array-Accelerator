# Matrix-level packed INT4 regression

The integration regression now exercises the full matrix job datapath in both signed INT8 and packed signed INT4 modes. INT4 operands contain two signed four-bit lanes per byte; the expected product is the sum of lane-wise products. The 5x33 by 33x5 test covers all four output tiles, the final one-element reduction block, signed edge values, and output accumulation. Both tests compare all 25 output elements with Python reference values. Operand staging remains host-assisted.
