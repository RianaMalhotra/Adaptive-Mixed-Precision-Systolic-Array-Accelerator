# Registered SRAM packed INT4 verification

The synchronous-memory matrix integration regression now covers signed packed INT4 as well as signed INT8. Each byte carries two signed 4-bit lanes, both independently multiplied and accumulated. The 5x33 by 33x5 case exercises four output tiles, two K reduction blocks per tile, partial M/P edges, and a final K block of one element. Python independently computes all 25 output cells; the test checks tile and accepted-write counts. CI verification pending.
