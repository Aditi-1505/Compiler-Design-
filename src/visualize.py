import tkinter as tk
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from lexer import Lexer
from parser import Parser, print_ast
from parser import (
    Program, Number, String, Identifier,
    BinaryOp, Assignment, Print, If, While, For, FunctionCall,
)
from transformer import Transformer
from semantic import SemanticAnalyzer
BG        = "#f5f0eb"
SURFACE   = "#fffcf8"
PANEL_HDR = "#f0ebe3"
BORDER    = "#ddd6cc"
TEXT      = "#2d2926"
TEXT_DIM  = "#8c7f74"
TEXT_BRT  = "#1a1410"
ACCENT    = "#3d7ebf"
ACCENT2   = "#7b52ab"
ACCENT3   = "#c87d2f"
ERROR_FG  = "#b83232"
ERROR_BG  = "#fdf0f0"
EDGE_RAW  = "#bbb0a4"
EDGE_OPT  = "#c5b8d8"

NODE_COLORS = {
    "Program":      "#5b9bd5",
    "Assignment":   "#9b72c8",
    "Print":        "#4aaa82",
    "BinaryOp":     "#d4902a",
    "If":           "#d05050",
    "While":        "#c4648a",
    "For":          "#7a6ebf",
    "FunctionCall": "#3aacbc",
    "Number":       "#63b58a",
    "String":       "#c4a030",
    "Identifier":   "#7097c4",
}

OP_SYMBOL = {
    "PLUS": "+",
    "MINUS": "-",
    "MULTIPLY": "x",
    "DIVIDE": "/",
    "FLOOR_DIVIDE": "//",
    "MODULO": "%",
    "DOUBLE_EQUALS": "==",
    "NOT_EQUALS": "!=",
    "LESS_THAN": "<",
    "GREATER_THAN": ">",
    "LESS_EQUAL": "<=",
    "GREATER_EQUAL": ">=",
}

NW = 118
NH = 44
H_GAP = 20
V_GAP = 50

def get_children(node):
    if isinstance(node, Program):
        return node.statements
    if isinstance(node, Assignment):
        return [node.value]
    if isinstance(node, Print):
        return [node.expression]
    if isinstance(node, BinaryOp):
        return [node.left, node.right]
    if isinstance(node, FunctionCall):
        return node.args
    if isinstance(node, If):
        kids = [node.condition] + list(node.body)
        for cond, body in node.elif_clauses:
            kids += [cond] + list(body)
        kids += list(node.else_body)
        return kids
    if isinstance(node, While):
        return [node.condition] + list(node.body)
    if isinstance(node, For):
        parts = [node.start, node.stop]
        if node.step:
            parts.append(node.step)
        return parts + list(node.body)
    return []

def node_labels(node):
    if isinstance(node, Program):
        return "Program", ""
    if isinstance(node, Assignment):
        return "Assign", node.name
    if isinstance(node, Print):
        return "Print", ""
    if isinstance(node, BinaryOp):
        sym = OP_SYMBOL.get(node.op.name, node.op.name)
        return "BinaryOp", sym
    if isinstance(node, FunctionCall):
        return "Call", node.name
    if isinstance(node, If):
        return "If", ""
    if isinstance(node, While):
        return "While", ""
    if isinstance(node, For):
        return "For", node.var
    if isinstance(node, Number):
        return "Number", str(node.value)
    if isinstance(node, String):
        return "String", f'"{node.value}"'
    if isinstance(node, Identifier):
        return "Ident", node.name
    return type(node).__name__, ""

class LayoutNode:
    __slots__ = ("ast", "kids", "width", "x", "y")

    def __init__(self, ast_node, kids):
        self.ast = ast_node
        self.kids = kids
        self.width = 0
        self.x = 0
        self.y = 0

def build_layout(node):
    kids = [build_layout(c) for c in get_children(node)]
    lay = LayoutNode(node, kids)
    if not kids:
        lay.width = NW
    else:
        total = sum(k.width for k in kids) + H_GAP * (len(kids) - 1)
        lay.width = max(NW, total)
    return lay

def assign_x(lay, left=0):
    if not lay.kids:
        lay.x = left + lay.width // 2
        return
    cx = left
    for k in lay.kids:
        assign_x(k, cx)
        cx += k.width + H_GAP
    lay.x = (lay.kids[0].x + lay.kids[-1].x) // 2

def flatten(lay, y=0, out=None):
    if out is None:
        out = []
    lay.y = y
    out.append(lay)
    for k in lay.kids:
        flatten(k, y + NH + V_GAP, out)
    return out

FONT_NODE  = ("Helvetica", 10, "bold")
FONT_SUB   = ("Helvetica", 9)
FONT_TIP   = ("Helvetica", 9)
FONT_UI    = ("Helvetica", 10)
FONT_UI_B  = ("Helvetica", 10, "bold")
FONT_SMALL = ("Helvetica", 8)
FONT_CODE  = ("Courier New", 12)

def draw_tree(canvas, ast_root, is_opt=False):
    canvas.delete("all")
    if ast_root is None:
        canvas.create_text(24, 24, text="(nothing to show)",
                           fill=TEXT_DIM, anchor="nw", font=FONT_UI)
        return

    lay = build_layout(ast_root)
    assign_x(lay, 24)
    nodes = flatten(lay, y=24)
    max_x = max(n.x + NW // 2 for n in nodes) + 36
    max_y = max(n.y + NH for n in nodes) + 36
    canvas.config(scrollregion=(0, 0, max_x, max_y))
    edge_col = EDGE_OPT if is_opt else EDGE_RAW
    for n in nodes:
        for k in n.kids:
            x1, y1 = n.x, n.y + NH
            x2, y2 = k.x, k.y
            mid_y = (y1 + y2) // 2
            canvas.create_line(x1, y1, x1, mid_y, x2, mid_y, x2, y2,
                               fill=edge_col, width=1.5)

    for n in nodes:
        col = NODE_COLORS.get(type(n.ast).__name__, "#aaaaaa")
        rx = n.x - NW // 2
        ry = n.y
        tag = f"n{id(n)}"
        optimized = getattr(n.ast, "_optimized", False)

        canvas.create_rectangle(rx + 3, ry + 3, rx + NW + 3, ry + NH + 3,
                                 fill="#ccc4ba", outline="")

        if optimized:
            canvas.create_rectangle(rx - 2, ry - 2, rx + NW + 2, ry + NH + 2,
                                     fill="", outline=ACCENT3, width=2, tags=tag)

        canvas.create_rectangle(rx, ry, rx + NW, ry + NH,
                                 fill=col, outline="#f1dada", width=1, tags=tag)

        top, sub = node_labels(n.ast)
        cx = rx + NW // 2
        if sub:
            canvas.create_text(cx, ry + 14, text=top,
                               fill="#ffffff", font=FONT_NODE, tags=tag)
            sub_disp = sub if len(sub) <= 14 else sub[:13] + "..."
            canvas.create_text(cx, ry + 30, text=sub_disp,
                               fill="#c8a7a7", font=FONT_SUB, tags=tag)
        else:
            canvas.create_text(cx, ry + 22, text=top,
                               fill="#ffffff", font=FONT_NODE, tags=tag)

        if optimized:
            canvas.create_text(rx + NW - 5, ry + 5, text="*",
                               fill=ACCENT3, font=("Helvetica", 11, "bold"),
                               anchor="ne", tags=tag)

        _bind_tooltip(canvas, tag, n.ast)

_tip_win = None

def _bind_tooltip(canvas, tag, node):
    def on_enter(e):
        global _tip_win
        _hide_tooltip()
        lines = [f"Type:   {type(node).__name__}"]
        if isinstance(node, (Assignment, FunctionCall)):
            lines.append(f"Name:   {node.name}")
        if isinstance(node, (Number, String)):
            lines.append(f"Value:  {node.value}")
        if isinstance(node, Identifier):
            lines.append(f"Name:   {node.name}")
        if isinstance(node, BinaryOp):
            sym = OP_SYMBOL.get(node.op.name, node.op.name)
            lines.append(f"Op:     {sym}  ({node.op.name})")
        if isinstance(node, For):
            lines.append(f"Var:    {node.var}")
        if getattr(node, "_optimized", False):
            lines.append("* optimized node")
        _tip_win = tk.Toplevel(canvas)
        _tip_win.wm_overrideredirect(True)
        _tip_win.configure(bg=BORDER)
        outer = tk.Frame(_tip_win, bg=BORDER, padx=1, pady=1)
        outer.pack()
        inner = tk.Frame(outer, bg=SURFACE, padx=10, pady=8)
        inner.pack()
        tk.Label(inner, text="\n".join(lines), font=FONT_TIP,
                 bg=SURFACE, fg=TEXT, justify="left").pack()
        x = canvas.winfo_rootx() + e.x + 16
        y = canvas.winfo_rooty() + e.y - 8
        _tip_win.geometry(f"+{x}+{y}")
    canvas.tag_bind(tag, "<Enter>", on_enter)
    canvas.tag_bind(tag, "<Leave>", lambda e: _hide_tooltip())

def _hide_tooltip():
    global _tip_win
    if _tip_win:
        try:
            _tip_win.destroy()
        except Exception:
            pass
        _tip_win = None

def mark_optimized(raw_node, opt_node):
    if raw_node is None and opt_node is None:
        return
    if type(raw_node) != type(opt_node):
        if opt_node is not None:
            opt_node._optimized = True
        return
    changed = False
    if isinstance(opt_node, Number) and isinstance(raw_node, Number):
        changed = str(opt_node.value) != str(raw_node.value)
    if changed:
        opt_node._optimized = True
        return
    for r, o in zip(get_children(raw_node), get_children(opt_node)):
        mark_optimized(r, o)

def count_optimized(node):
    if node is None:
        return 0
    total = 1 if getattr(node, "_optimized", False) else 0
    for k in get_children(node):
        total += count_optimized(k)
    return total

SAMPLE = """\
x = 5 + 3
y = x * 1
z = 10 + 0

print(x)
print(y + 0)
if x > 2:
    print(x)
elif z == 10:
    print(z)
else:
    print(0)
for i in range(3):
    print(i)
"""

class ASTVisualizerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AST Visualizer")
        self.geometry("1320x800")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self._build_ui()
        self._text.insert("1.0", SAMPLE.strip())
        self.__dict__["editor"] = self._text
        self.__dict__["canvas"] = self._canvas_raw_solo

    def _build_ui(self):
        self._build_header()
        body = tk.PanedWindow(self, orient="horizontal",
                              bg=BORDER, sashwidth=5, sashrelief="flat")
        body.pack(fill="both", expand=True)
        left = tk.Frame(body, bg=SURFACE)
        body.add(left, minsize=260, width=300)
        self._build_editor_panel(left)
        right = tk.Frame(body, bg=BG)
        body.add(right, minsize=500)
        self._build_tree_panel(right)

    def _build_header(self):
        bar = tk.Frame(self, bg=SURFACE, height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Frame(bar, bg=BORDER, height=1).place(relx=0, rely=1.0,
                                                  relwidth=1, anchor="sw")
        tk.Label(bar, text="AST Visualizer", bg=SURFACE, fg=TEXT_BRT,
                 font=("Helvetica", 14, "bold")).pack(side="left", padx=18, pady=14)
        self._status_var = tk.StringVar(value="")
        tk.Label(bar, textvariable=self._status_var,
                 bg=SURFACE, fg=TEXT_DIM, font=FONT_UI).pack(side="right", padx=18)
        tk.Label(bar, text="Ctrl+Enter to run",
                 bg=SURFACE, fg=TEXT_DIM, font=FONT_SMALL).pack(side="right", padx=2)

    def _build_editor_panel(self, parent):
        tk.Label(parent, text="Source code", bg=SURFACE, fg=TEXT_DIM,
                 font=FONT_SMALL, anchor="w", pady=7).pack(fill="x", padx=14)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")

        edit_frame = tk.Frame(parent, bg=SURFACE)
        edit_frame.pack(fill="both", expand=True)

        self._text = tk.Text(
            edit_frame, bg=SURFACE, fg=TEXT,
            insertbackground=ACCENT,
            font=FONT_CODE, relief="flat", bd=0,
            wrap="none", padx=12, pady=10,
            selectbackground="#c8dff4",
            undo=True,
        )
        sb = tk.Scrollbar(edit_frame, orient="vertical", command=self._text.yview)
        self._text.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._text.pack(fill="both", expand=True)
        self._text.bind("<Tab>",
            lambda e: (self._text.insert("insert", "    "), "break")[1])

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")

        btn_bar = tk.Frame(parent, bg=SURFACE, pady=10, padx=14)
        btn_bar.pack(fill="x")
        tk.Button(
            btn_bar, text="Clear", command=self._clear,
            bg=PANEL_HDR, fg=TEXT_DIM, activebackground=BORDER,
            font=FONT_UI, relief="flat", padx=12, pady=6, bd=0,
        ).pack(side="left")
        tk.Button(
            btn_bar, text="Visualize  >", command=self._run,
            bg=ACCENT, fg="white", activebackground="#2d6aad",
            activeforeground="white", font=FONT_UI_B,
            relief="flat", padx=14, pady=6, bd=0,
        ).pack(side="right")

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")
        leg = tk.Frame(parent, bg=SURFACE, padx=14, pady=10)
        leg.pack(fill="x")
        tk.Label(leg, text="Node types", bg=SURFACE, fg=TEXT_DIM,
                 font=FONT_SMALL).pack(anchor="w", pady=(0, 5))
        grid = tk.Frame(leg, bg=SURFACE)
        grid.pack(anchor="w")
        for i, (name, col) in enumerate(NODE_COLORS.items()):
            row, col_idx = divmod(i, 2)
            f = tk.Frame(grid, bg=SURFACE)
            f.grid(row=row, column=col_idx, sticky="w", padx=(0, 14), pady=2)
            tk.Canvas(f, width=12, height=12, bg=col,
                      highlightthickness=0).pack(side="left")
            tk.Label(f, text=f"  {name}", bg=SURFACE, fg=TEXT_DIM,
                     font=FONT_SMALL).pack(side="left")

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=(6, 0))
        tk.Label(parent, text="  * amber border = optimized node",
                 bg=SURFACE, fg=ACCENT3, font=FONT_SMALL,
                 anchor="w", pady=6).pack(fill="x")

    def _build_tree_panel(self, parent):
        tab_bar = tk.Frame(parent, bg=SURFACE)
        tab_bar.pack(fill="x")
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")

        self._tabs = {}
        for key, label in [("raw", "Raw AST"), ("opt", "Optimized")]:
            f = tk.Frame(tab_bar, bg=SURFACE)
            f.pack(side="left")
            lbl = tk.Label(f, text=label, bg=SURFACE, fg=TEXT_DIM,
                           font=FONT_UI, pady=11, padx=14)
            lbl.pack()
            self._tabs[key] = (f, lbl)
            f.bind("<Button-1>",   lambda e, k=key: self._switch_tab(k))
            lbl.bind("<Button-1>", lambda e, k=key: self._switch_tab(k))

        content = tk.Frame(parent, bg=BG)
        content.pack(fill="both", expand=True)

        self._frame_raw = tk.Frame(content, bg=BG)
        self._make_pane(self._frame_raw, "Raw AST", "raw_solo", fill=True)
        self._frame_opt = tk.Frame(content, bg=BG)
        self._make_pane(self._frame_opt, "Optimized AST", "opt_solo", fill=True)
        self._switch_tab("raw")

    def _make_pane(self, parent, title, canvas_key, fill=False):
        pane = tk.Frame(parent, bg=BG)
        if fill:
            pane.pack(fill="both", expand=True)
        hdr = tk.Frame(pane, bg=PANEL_HDR, pady=7)
        hdr.pack(fill="x")
        tk.Label(hdr, text=title, bg=PANEL_HDR, fg=TEXT,
                 font=FONT_UI_B, padx=14).pack(side="left")
        if "opt" in canvas_key:
            self._opt_count_var = tk.StringVar(value="")
            tk.Label(hdr, textvariable=self._opt_count_var,
                     bg=PANEL_HDR, fg=ACCENT3, font=FONT_SMALL,
                     padx=12).pack(side="right")
        tk.Frame(pane, bg=BORDER, height=1).pack(fill="x")
        wrap = tk.Frame(pane, bg=BG)
        wrap.pack(fill="both", expand=True)
        cv = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(wrap, orient="vertical",   command=cv.yview)
        hsb = tk.Scrollbar(wrap, orient="horizontal", command=cv.xview)
        cv.config(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        hsb.pack(side="bottom", fill="x")
        vsb.pack(side="right",  fill="y")
        cv.pack(fill="both", expand=True)

        cv.bind("<MouseWheel>",
                lambda e, c=cv: c.yview_scroll(-1 * (e.delta // 120), "units"))
        cv.bind("<Button-4>", lambda e, c=cv: c.yview_scroll(-1, "units"))
        cv.bind("<Button-5>", lambda e, c=cv: c.yview_scroll( 1, "units"))
        cv.bind("<ButtonPress-1>", lambda e, c=cv: c.scan_mark(e.x, e.y))
        cv.bind("<B1-Motion>",     lambda e, c=cv: c.scan_dragto(e.x, e.y, gain=1))

        setattr(self, f"_canvas_{canvas_key}", cv)
        return pane

    def _switch_tab(self, key):
        self._frame_raw.pack_forget()
        self._frame_opt.pack_forget()

        for k, (f, lbl) in self._tabs.items():
            active = (k == key)
            lbl.config(
                fg=ACCENT if active else TEXT_DIM,
                font=FONT_UI_B if active else FONT_UI,
                bg="#eae3da" if active else SURFACE,
            )
            f.config(bg="#eae3da" if active else SURFACE)

        frame_map = {
            "raw": self._frame_raw,
            "opt": self._frame_opt,
        }
        frame_map[key].pack(fill="both", expand=True)

    def _clear(self):
        self._text.delete("1.0", "end")
        for key in ("raw_solo", "opt_solo"):
            cv = getattr(self, f"_canvas_{key}", None)
            if cv:
                cv.delete("all")
        self._status_var.set("")
        if hasattr(self, "_opt_count_var"):
            self._opt_count_var.set("")

    def _run(self):
        code = self._text.get("1.0", "end").rstrip()
        if not code:
            return
        try:
            tokens = Lexer(code).tokenize()
            raw_ast = Parser(tokens).parse()
            SemanticAnalyzer().analyze(raw_ast)

            tokens2 = Lexer(code).tokenize()
            raw_ast2 = Parser(tokens2).parse()
            opt_ast = Transformer().transform(raw_ast2)

            mark_optimized(raw_ast, opt_ast)
            n_opt = count_optimized(opt_ast)

            for key, ast, is_opt in [
                ("raw_solo", raw_ast, False),
                ("opt_solo", opt_ast, True),
            ]:
                draw_tree(getattr(self, f"_canvas_{key}"), ast, is_opt)

            if n_opt:
                label = f"{n_opt} optimisation{'s' if n_opt != 1 else ''} applied"
            else:
                label = "no changes"
            self._opt_count_var.set(label)
            self._status_var.set("Parsed successfully")

        except Exception as exc:
            self._show_error(str(exc))
            self._status_var.set(f"Error: {exc}")

    def _show_error(self, msg):
        for key in ("raw_solo", "opt_solo"):
            cv = getattr(self, f"_canvas_{key}", None)
            if not cv:
                continue
            cv.delete("all")
            cv.create_rectangle(20, 20, 660, 110,
                                 fill=ERROR_BG, outline="#e8b0b0", width=1)
            cv.create_text(32, 36, text="Error", fill=ERROR_FG,
                           font=FONT_UI_B, anchor="nw")
            cv.create_text(32, 58, text=msg, fill=ERROR_FG,
                           font=FONT_UI, anchor="nw", width=600)
if __name__ == "__main__":
    app = ASTVisualizerApp()
    app.bind("<Control-Return>", lambda e: app._run())
    app.mainloop()