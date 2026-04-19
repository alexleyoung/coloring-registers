# overview

## What is register allocation?

Computer programs store data in **variables (can also be imagined as virtual registers)**. Unfortunately, programs can
have a (theoretically) unlimited number of variables, but computers have a phyiscal limit on the number of registers
they can use to store said variables. When a CPU runs out of registers, data **spills** to primary storage, most often
RAM (random access memory). RAM is magnitudes slower than register access, and thus the crux of the problem: how can we
allocate variables to registers in a way which maximizes a variable's time in a register during its lifetime and
minimizes spills.

## Liveness Analysis

A variable is **live** if it is *used* (instantiated or used in computation) in any given *block* (a scope of program 
code).

Thus, if two variables are simultaneously live, we can't assign them to the same register. Conversely, if two
variables are not both live, we *can* assign them to the same register.

## Graph Coloring?

So, we construct a **interference graph**. An interference graph is an undirected graph of variables as nodes and edges
between nodes with *interference*, interference meaning the two variables are simultaneously live.

Then, to find some allocation of the variables, we can use *graph coloring* to find which variables (nodes) and be
allocated to any given register. Clearly, the less colors (and the bigger the color classes) we have, the less registers
we need to store a program's data, and the less we need to spill into RAM.

# Mechanisms

## Control Flow Graph (CFG)

A **control flow graph** is a graph of a program where nodes are blocks of code with no control flow (i.e., divide the
program code into blocks at control flow branch points). Edges point to other blocks where control flow may direct the
program.

### Helper functions

*pred* is a function which, given a vertex in a CFG, returns the set of vertices which *precede* it. I.e., 
$pred(v) = \{w \in V \| (w,v) \in E \}$

*succ* is a function which, given a vertex in a CFG, returns the set of vertices which *succede* it. I.e., 
$pred(v) = \{w \in V \| (v,w) \in E \}$

### Definition and use

*def* is a function which returns the set of variables *defined* in a given block of a CFG.

*use* is a function which returns the set of variables *used* in a given block of a CFG.

### Live-in & Live-out

**Live variable**: A variable is **live** if it contains a value that *may* be used in the future.

**Liveness analysis**: Compute live-in to a node and live-out from a node.

**Live-in**: The set of variables that are live on any incoming edge.

**Live-out**: The set of variables that are live on any outgoing edge.

How to compute live-in and live-out? *Data-flow analysis*.
