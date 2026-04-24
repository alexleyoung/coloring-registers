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

    for line in lines:
        line = line.strip()
        # ensure line not empty
        if not line:
            continue

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


### helper which finds "leaders", instructions which start new basic blocks
def find_leaders(instructions: list[Instruction]) -> list[int]:
    # first instruction is always a leader, since control flow starts there
    leaders = {0}

    for i, instr in enumerate(instructions):
        match instr:
            # labels are jump targets, so they start new blocks
            case Label(_):
                leaders.add(i)
            # jumps break control flow, so the following instruction must be a leader
            case Goto(_) | IfGoto(_, _) | Return(_):
                if i + 1 < len(instructions):
                    leaders.add(i + 1)

    return list(leaders)


### parse instructions into blocks
def parse_blocks(instructions: list[Instruction]) -> list[BasicBlock]:
    blocks = []
    leaders = sorted(find_leaders(instructions))

    for i in range(len(leaders)):
        if i == len(leaders) - 1:
            blocks.append(BasicBlock(instructions[leaders[i] :]))
        else:
            blocks.append(BasicBlock(instructions[leaders[i] : leaders[i + 1]]))

    return blocks


### helper to find block with [label] as the first instruction
def find_label_block(blocks: list[BasicBlock], label: str) -> int:
    for i, block in enumerate(blocks):
        match block.instructions[0]:
            # non-control block
            case Label(name):
                if name == label:
                    return i

    raise Exception(f"label '{label}' does not exist")


### generate adjacency matrix from basic blocks
def parse_edges(blocks: list[BasicBlock]) -> list[list[int]]:
    n = len(blocks)
    edges = [[0 for _ in range(n)] for _ in range(n)]
    for i, block in enumerate(blocks):
        match block.instructions[-1]:
            # non-control block
            case Assign(_, _):
                if i < len(blocks) - 1:
                    edges[i][i + 1] = 1
            # jump only directs to label block
            case Goto(label):
                edges[i][find_label_block(blocks, label)] = 1
            # if go to can go to label block or next block
            case IfGoto(_, label):
                if i < len(blocks) - 1:
                    edges[i][i + 1] = 1
                edges[i][find_label_block(blocks, label)] = 1
            # NOTE: if label or return is last instruction, no-op

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
