      ******************************************************************
      * INTCALC.CBL — Deposit interest calculation module (practice).
      * This is the GOLDEN implementation. Read it as the SME does: it
      * is authoritative but not fully documented (see PARA-CAP-CHECK).
      ******************************************************************
       IDENTIFICATION DIVISION.
       PROGRAM-ID. INTCALC.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-PRINCIPAL        PIC S9(9)V99 COMP-3.
       01  WS-RATE-BP          PIC 9(4).
       01  WS-TIER             PIC 9(1).
       01  WS-YEAR-2D          PIC 9(2).
       01  WS-BAL-OVERPUNCH    PIC S9(7) SIGN TRAILING SEPARATE.
       01  WS-INTEREST         PIC S9(9)V99 COMP-3.
       01  WS-CAPPED-INTEREST  PIC S9(9)V99 COMP-3.
       01  WS-RATE-DEC         PIC 9V9999.
       01  WS-TEMP             PIC S9(9)V999.

       PROCEDURE DIVISION.

       PARA-MAIN.
      *    R-001..R-003: tiered annual rate by WS-TIER
           MOVE 0 TO WS-RATE-BP
           IF WS-TIER = 1
               MOVE 0150 TO WS-RATE-BP
           ELSE IF WS-TIER = 2
               MOVE 0275 TO WS-RATE-BP
           ELSE IF WS-TIER = 3
               MOVE 0400 TO WS-RATE-BP
           END-IF.

      *    R-004: tier boundary is strictly GREATER-THAN 100000, not >=.
      *    A balance of exactly 100000 stays in the lower tier. The
      *    business rule text says "balances over 100000 receive the
      *    next tier" — genuinely ambiguous whether "over" means >= or >.
      *    This code says >.
           IF WS-PRINCIPAL > 100000.00 AND WS-TIER = 1
               MOVE 0275 TO WS-RATE-BP
           END-IF.

      *    R-005: compute raw interest = principal * rate, rate in bp/10000
           COMPUTE WS-RATE-DEC = WS-RATE-BP / 10000
           COMPUTE WS-TEMP = WS-PRINCIPAL * WS-RATE-DEC

      *    R-006: round to the cent using COBOL's ROUNDED clause, which is
      *    round-half-away-from-zero — NOT Python's default banker's
      *    rounding (round-half-to-even). Values landing exactly on the
      *    half cent are where a naive Python port diverges (R-009).
           COMPUTE WS-INTEREST ROUNDED = WS-TEMP.

      *    R-007: two-digit year window, pivot at 50. 00-49 -> 20xx,
      *    50-99 -> 19xx. A value of 51 means 1951; a value of 49 means
      *    2049. Only affects a promo-eligibility flag downstream in the
      *    full module — not modelled further here (out of scope note
      *    for R-007's own vectors).
      *    (No further COBOL needed for R-007 in this trimmed practice
      *    module; it exists purely as a rule to synthesise vectors for.)

      *    R-008: signed balance field uses TRAILING SEPARATE sign, i.e.
      *    the last character of the raw feed IS the sign ('+'/'-'),
      *    not a magnitude digit. A naive port that treats the last
      *    character as a digit will misread the value (R-010).

           PERFORM PARA-CAP-CHECK.

       PARA-CAP-CHECK.
      *    UNDOCUMENTED BEHAVIOUR — no business rule in the validated
      *    list describes this paragraph. It caps interest at 500.00
      *    whenever WS-TIER = 3. This is the R-022-equivalent pathology:
      *    the traceability checker should flag this as untraceable
      *    behaviour; it must be REPORTED, not silently reimplemented.
           MOVE WS-INTEREST TO WS-CAPPED-INTEREST
           IF WS-TIER = 3 AND WS-INTEREST > 500.00
               MOVE 500.00 TO WS-CAPPED-INTEREST
           END-IF.

       END PROGRAM INTCALC.
