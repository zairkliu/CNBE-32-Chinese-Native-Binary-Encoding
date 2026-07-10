# v7 Protocol: RISC-V Hardware Instruction Validation

Status: protocol draft

This document defines the redesigned v7 experiment family.

It does not report completed results.

## Purpose

v7 tests whether CNBE-related instruction encodings and hardware behaviors are specified and reproducible.

The historical v7 artifacts include RISC-V validation, custom instruction validation, Spike integration, FPGA prototypes, and hardware-feature cooperation.

The redesigned protocol separates emulator conformance from FPGA or physical hardware evidence.

## Research Question

Can the defined CNBE instruction subset be encoded, decoded, executed, and traced reproducibly against a reference specification?

## Required Specification

Before execution, the stage must define:

- instruction names,
- binary encoding,
- operand fields,
- register effects,
- memory effects,
- exception behavior,
- unsupported cases,
- expected trace format.

No hardware claim may be made for behavior that is not specified.

## Test Fixtures

Required fixtures:

- encode/decode round trip,
- legal instruction execution,
- illegal instruction rejection,
- boundary operand values,
- register-state transitions,
- memory-state transitions when relevant,
- deterministic trace comparison.

Each fixture must have expected output.

## Runtime Targets

Report targets separately:

- assembler or encoder,
- disassembler or decoder,
- emulator,
- Spike or QEMU integration,
- FPGA prototype,
- physical hardware if available.

Evidence from one target must not be reported as evidence for another target.

## Metrics

Primary metric:

- fixture pass rate against expected trace.

Secondary metrics:

- encode/decode pass rate,
- register-state match,
- memory-state match,
- illegal-instruction rejection rate,
- trace reproducibility,
- toolchain reproducibility.

## Reproducibility

Reports must include:

- toolchain versions,
- emulator version,
- build command,
- fixture hash,
- expected trace hash,
- actual trace hash,
- commit SHA.

## Failure Conditions

The v7 run is invalid if:

- instruction semantics are not specified,
- expected traces are missing,
- trace logs are manually edited,
- emulator evidence is described as silicon evidence,
- unsupported instructions are omitted from the report,
- only a hello-world style demo is shown.

## Reporting Boundary

Allowed conclusion:

```text
Under the specified fixture set and runtime target, the CNBE instruction subset passed / failed reproducible trace validation.
```

Disallowed conclusions:

- production silicon readiness,
- complete RISC-V ecosystem support,
- complete hardware acceleration validation,
- operating-system readiness.
