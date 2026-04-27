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


### scan source psuedo-code into [Instruction]s
def scan_source(source: str) -> list[Instruction]:
    lines = source.split("\n")
    instructions = []

    for line in lines:
        line = line.strip()
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
    leaders = {0}

    for i, instr in enumerate(instructions):
        match instr:
            case Label(_):
                leaders.add(i)
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
            case Assign(_, _):
                if i < len(blocks) - 1:
                    edges[i][i + 1] = 1
            case Goto(label):
                edges[i][find_label_block(blocks, label)] = 1
            case IfGoto(_, label):
                if i < len(blocks) - 1:
                    edges[i][i + 1] = 1
                edges[i][find_label_block(blocks, label)] = 1
            # NOTE: if label or return is last instruction, no-op

    return edges


def parse_expr_vars(expr: str) -> set[str]:
    vars = set()
    symbols = expr.split(" ")
    for symbol in symbols:
        if symbol.isidentifier():
            vars.add(symbol)
    return vars


class CFG:
    blocks: list[BasicBlock]
    edges: list[list[int]]

    _pred: list[set[int]]
    _succ: list[set[int]]
    _def: list[set[str]]
    _use: list[set[str]]
    _live_in: list[set[str]]
    _live_out: list[set[str]]
    # instruction-level liveness: for each block, a list of live sets per instruction (bottom-up)
    _instr_live: list[list[set[str]]]

    def __init__(self, blocks: list[BasicBlock], edges: list[list[int]]):
        self.blocks = blocks
        self.edges = edges
        n = len(blocks)
        self._pred = [set() for _ in range(n)]
        self._succ = [set() for _ in range(n)]
        self._def = [set() for _ in range(n)]
        self._use = [set() for _ in range(n)]
        self._live_in = [set() for _ in range(n)]
        self._live_out = [set() for _ in range(n)]
        self._instr_live = [[] for _ in range(n)]

    ### populate pred and succ from the adjacency matrix
    def _build_pred_succ(self):
        for i in range(len(self.blocks)):
            for j in range(len(self.blocks)):
                if self.edges[i][j]:
                    self._succ[i].add(j)
                    self._pred[j].add(i)

    ### populate def and use by scanning each block's instructions
    def _build_def_use(self):
        def extract_uses(i: int, expr: str):
            vars = parse_expr_vars(expr)
            for var in vars:
                if var not in self._def[i]:
                    self._use[i].add(var)

        for i, block in enumerate(self.blocks):
            for instr in block.instructions:
                match instr:
                    case Assign(dest, expr):
                        extract_uses(i, expr)
                        self._def[i].add(dest)
                    case IfGoto(cond, _):
                        extract_uses(i, cond)
                    case Return(expr):
                        extract_uses(i, expr)

    ### iteratively compute live-in and live-out for each block until convergence
    def _liveness_analysis(self):
        while True:
            old_out = [s.copy() for s in self._live_out]
            old_in = [s.copy() for s in self._live_in]

            for v, _ in enumerate(self.blocks):
                # out[v] = union of all in[w] for w in succ(v)
                for w in self.succ(v):
                    self._live_out[v] |= self._live_in[w]

                # in[v] = use(v) union (out[v] - def(v))
                self._live_in[v] = self.use(v) | (self._live_out[v] - self.defi(v))

            if old_out == self._live_out and old_in == self._live_in:
                break

    ### compute live set at each instruction by propagating live_out backwards through the block
    def _instr_liveness_analysis(self):
        for v, block in enumerate(self.blocks):
            live = self._live_out[v].copy()
            instr_live = []
            for instr in reversed(block.instructions):
                instr_live.append(live.copy())
                match instr:
                    case Assign(dest, expr):
                        live = (live - {dest}) | parse_expr_vars(expr)
                    case IfGoto(cond, _):
                        live |= parse_expr_vars(cond)
                    case Return(expr):
                        live |= parse_expr_vars(expr)
            self._instr_live[v] = list(reversed(instr_live))

    def pred(self, v: int) -> set[int]:
        return self._pred[v]

    def succ(self, v: int) -> set[int]:
        return self._succ[v]

    def defi(self, v: int) -> set[str]:
        return self._def[v]

    def use(self, v: int) -> set[str]:
        return self._use[v]

    def live_in(self, v: int) -> set[str]:
        return self._live_in[v]

    def live_out(self, v: int) -> set[str]:
        return self._live_out[v]

    def instr_live(self, v: int) -> list[set[str]]:
        return self._instr_live[v]


# Interference Graph class with variables as vertices and edges as interference
class IG:
    _cfg: CFG
    variables: set[str]
    interference: dict[str, set[str]]

    def __init__(self, cfg: CFG):
        self._cfg = cfg
        self.variables = set()
        self.interference = {}

    def _get_variables(self):
        for block in self._cfg.blocks:
            for instr in block.instructions:
                match instr:
                    case Assign(dest, expr):
                        self.variables.add(dest)
                        self.variables |= parse_expr_vars(expr)
                    case IfGoto(cond, _):
                        self.variables |= parse_expr_vars(cond)
                    case Return(expr):
                        self.variables |= parse_expr_vars(expr)

        # instantiate edge map with vertices
        for a in self.variables:
            self.interference[a] = set()

    def _get_interferences(self):
        for v, block in enumerate(self._cfg.blocks):
            for i, instr in enumerate(block.instructions):
                match instr:
                    case Assign(dest, _):
                        for b in self._cfg.instr_live(v)[i]:
                            if dest != b:
                                self.interference[dest].add(b)
                                self.interference[b].add(dest)


def main():
    # note, expressions must have spaces delimiting symbols because my parser is lazy
    # furthermore, only simple arithmetic operations are allowed (+, -, *, /) for the same reason
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
    cfg._build_pred_succ()
    cfg._build_def_use()
    cfg._liveness_analysis()
    cfg._instr_liveness_analysis()

    ig = IG(cfg)
    ig._get_variables()
    ig._get_interferences()

    # greedy coloring!!!
    colors = {a: 0 for a in ig.variables}  # 0 = uncolored
    for a in ig.variables:
        # get set of colors we are neighboring
        neighbor_colors = {colors[x] for x in ig.interference[a]}

        # pick the lowest number (color) not in neighbor_colors
        i = 1
        while i in neighbor_colors:
            i += 1
        colors[a] = i


if __name__ == "__main__":
    main()
