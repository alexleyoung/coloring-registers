from dataclasses import dataclass
import re


@dataclass
class Assign:
    dest: str
    expr: str


@dataclass
class Label:
    name: str


@dataclass
class Goto:
    target: str


@dataclass
class IfGoto:
    cond: str
    target: str


@dataclass
class Return:
    expr: str


Instruction = Assign | Label | Goto | IfGoto | Return


@dataclass
class BasicBlock:
    instructions: list[Instruction]


@dataclass
class CFG:
    blocks: list[BasicBlock]

    # adjacency list of block indcies from [self.blocks]
    edges: list[list[int]]


### scan source psuedo-code into [Instruction]s
def scan_source(source: str) -> list[Instruction]:
    instructions = []
    return instructions


### parse instructions into blocks
def parse_blocks(instructions: list[Instruction]) -> list[BasicBlock]:
    blocks = []
    return blocks


### generate adjacency matrix from basic blocks
def parse_edges(blocks: list[BasicBlock]) -> list[list[int]]:
    n = len(blocks)
    edges = [[0 for _ in range(n)] for _ in range(n)]
    return edges


def main():
    pseudo_code = """
        z = 10
        x = 0
        y = 1
        loop:
        if (x < n) goto body
        goto end
        body:
        z = x * 2 + y
        x = x + 1
        y = x + z
        goto loop
        end:
        return y
    """

    instructions = scan_source(pseudo_code)
    blocks = parse_blocks(instructions)
    edges = parse_edges(blocks)

    cfg = CFG(blocks, edges)


if __name__ == "__main__":
    main()
