# v8 Protocol: Compiler and System Integration

Status: protocol draft

This document defines the redesigned v8 experiment family.

It does not report completed results.

## Purpose

v8 tests whether CNBE-oriented language, compiler, runtime, and system prototypes behave correctly under defined fixtures.

The historical v8 series includes Chinese programming mapping, compiler integration, Spike end-to-end validation, and operating-system prototypes.

The redesigned protocol separates toy-language correctness, compiler correctness, runtime behavior, and system smoke tests.

## Research Question

Can the CNBE-oriented compiler and system path compile, execute, and reject fixtures according to a frozen language specification?

## Required Specification

Before final testing, the stage must define:

- lexical grammar,
- syntax grammar,
- semantic rules,
- supported data types,
- unsupported constructs,
- code generation target,
- runtime assumptions,
- expected fixture outputs.

## Fixture Classes

Required positive fixtures:

- hello program,
- arithmetic,
- branch,
- loop,
- array or sequence,
- function or procedure if supported,
- structure or record if supported.

Required negative fixtures:

- lexical error,
- syntax error,
- unsupported construct,
- invalid identifier,
- invalid control flow,
- invalid memory or type use when applicable.

## Metrics

Primary metric:

- fixture pass rate.

Secondary metrics:

- parse success rate,
- expected rejection rate,
- generated assembly match,
- runtime output match,
- emulator execution pass rate,
- diagnostic quality.

## Trace and Output Rules

Reports must include:

- source fixture,
- expected output,
- generated intermediate representation when applicable,
- generated assembly when applicable,
- emulator or runtime output,
- comparison result.

Manual correction of generated output is prohibited unless logged as a failed run.

## System Prototype Rules

Operating-system or reader demos must be labeled as smoke tests unless they include:

- boot log,
- deterministic input,
- expected output,
- reproducible build command,
- negative behavior checks,
- supported feature list.

## Failure Conditions

The v8 run is invalid if:

- language specification is absent,
- only positive demos are tested,
- negative tests are omitted,
- generated code is manually patched without audit,
- emulator logs are missing,
- OS demo is reported as complete OS validation.

## Reporting Boundary

Allowed conclusion:

```text
Under the frozen fixture suite and toolchain, the CNBE-oriented compiler/system path passed / failed the defined integration tests.
```

Disallowed conclusions:

- production programming language readiness,
- complete OS readiness,
- complete compiler correctness,
- hardware readiness from software-only tests.
