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
    lines = source.split("\n")
    instructions = []

    for i in range(len(lines)):
        line = lines[i]
        if "if" in line:
            cond = re.search(r"\((.*?)\)", line)
            if not cond:
                raise Exception("no condition in if")
            target = line[line.find("goto ") + 5 :].strip()
            instructions.append(IfGoto(cond.group(1), target))
        elif "goto" in line:
            target = line[line.find("goto ") + 5 :].strip()
            instructions.append(Goto(target))
        elif "return" in line:
            val = line[line.find("return ") + 7 :].strip()
            instructions.append(Return(val))
        elif "=" in line:
            parts = line.split("=")
            dest = parts[0].strip()
            expr = parts[1].strip()
            instructions.append(Assign(dest, expr))
        elif ":" in line:
            label_name = line[: line.find(":")].strip()
            instructions.append(Label(label_name))
        else:
            raise Exception(f"Failed to parse line: {line}")

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
