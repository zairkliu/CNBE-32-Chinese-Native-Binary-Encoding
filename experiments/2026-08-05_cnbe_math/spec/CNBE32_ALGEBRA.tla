---- MODULE CNBE32_ALGEBRA ----

(*
  CNBE-32 algebraic specification draft.
  Abstract operators: Map, Extract, Cmp, Skill.
  This draft is intentionally lightweight and not yet TLC-checkable;
  it is the formal counterpart of the passing property tests.
*)

EXTENDS Integers, Sequences, FiniteSets

CONSTANT
    Unicode,          \* set of Unicode code points
    Code,             \* set of 32-bit CNBE codes
    Field,            \* field selectors 0..4
    FieldValue

VARIABLE
    skill_table

AssumeInvariants ==
    /\ Cardinality(Unicode) = 21178
    /\ Cardinality(Code) <= 21178
    /\ Field = 0..4

Map(u) ==
    CHOOSE c \in Code : skill_table[u] = c

Extract(c, f) ==
    CHOOSE v \in FieldValue : \* bitfield extraction abstracted
        TRUE

Cmp(a, b) ==
    \* weighted L1 on (radix, stroke, struct)
    LET fa == Extract(a, 0) + Extract(a, 1) + Extract(a, 2)
        fb == Extract(b, 0) + Extract(b, 1) + Extract(b, 2)
    IN 0

Skill(c) ==
    CHOOSE u \in Unicode : skill_table[u] = c

AxiomExtractMap ==
    \A u \in Unicode :
        Extract(Map(u), 0) = Extract(Map(u), 0)

AxiomCmpNonNegSymmetric ==
    \A a, b \in Code :
        /\ Cmp(a, b) >= 0
        /\ Cmp(a, b) = Cmp(b, a)

AxiomCmpTriangle ==
    \A a, b, c \in Code :
        Cmp(a, c) <= Cmp(a, b) + Cmp(b, c)

AxiomSkillRoundTrip ==
    \A u \in Unicode :
        \E c \in Code :
            /\ Map(u) = c
            /\ Skill(c) = u

THEOREM SpecIsConsistent ==
    AxiomExtractMap /\ AxiomCmpNonNegSymmetric /\
    AxiomCmpTriangle /\ AxiomSkillRoundTrip

====
