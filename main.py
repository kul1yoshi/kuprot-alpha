import builtins
import secrets
import keyword
import string
import random
import ast

class Transformer(ast.NodeTransformer):
    def __init__(self):
        self.name_map = {}
        self.in_joined_str = False
        self.reserved_names = set(keyword.kwlist) | set(dir(builtins))
        self.scope_stack = [set()]
    
    def _generate_random_string(self, length):
        return "".join(secrets.choice(string.ascii_letters) for _ in range(length))
    
    def _generate_obfuscated_name(self, original_name):
        if original_name not in self.name_map:
            while True:
                new_name = f"{self._generate_random_string(random.randint(6, 24))}"
                if new_name not in self.name_map.values():
                    self.name_map[original_name] = new_name
                    break
        
        return self.name_map[original_name]
    
    def _can_obfuscate_name(self, name):
        return (name not in self.reserved_names and
                not name.startswith("__") and
                not any(name in scope for scope in self.scope_stack))
    
    def visit_FunctionDef(self, node):
        if self._can_obfuscate_name(node.name):
            node.name = self._generate_obfuscated_name(node.name)
        
        self.scope_stack.append(set())
        for arg in node.args.args:
            if self._can_obfuscate_name(arg.arg):
                arg.arg = self._generate_obfuscated_name(arg.arg)
                self.scope_stack[-1].add(arg.arg)
        
        self.generic_visit(node)
        self.scope_stack.pop()
        return node
    
    def visit_ClassDef(self, node):
        if self._can_obfuscate_name(node.name):
            node.name = self._generate_obfuscated_name(node.name)
        
        self.scope_stack.append(set())
        self.generic_visit(node)
        self.scope_stack.pop()
        return node
    
    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Load)) and self._can_obfuscate_name(node.id):
            node.id = self._generate_obfuscated_name(node.id)
        
        return node
    
    def visit_arg(self, node):
        if self._can_obfuscate_name(node.arg):
            node.arg = self._generate_obfuscated_name(node.arg)
            self.scope_stack[-1].add(node.arg)
        
        return node
    
    def visit_Import(self, node):
        for alias in node.names:
            self.reserved_names.add(alias.name)
            if alias.asname and self._can_obfuscate_name(alias.asname):
                alias.asname = self._generate_obfuscated_name(alias.asname)
                self.scope_stack[-1].add(alias.asname)
        
        return node
    
    def visit_ImportFrom(self, node):
        self.reserved_names.add(node.module)
        for alias in node.names:
            self.reserved_names.add(alias.name)
            if alias.asname and self._can_obfuscate_name(alias.asname):
                alias.asname = self._generate_obfuscated_name(alias.asname)
                self.scope_stack[-1].add(alias.asname)
        
        return node
    
    def visit_Attribute(self, node):
        if node.attr in self.name_map:
            if not (isinstance(node.value, ast.Name) and node.value.id in self.reserved_names):
                node.attr = self.name_map[node.attr]
        
        self.generic_visit(node)
        return node
    
    def visit_JoinedStr(self, node):
        prev_in_joined_str = self.in_joined_str
        self.in_joined_str = True
        new_values = []
        
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts = []
                for c in value.value:
                    n = ord(c)
                    math_expr = self.mathfuscate(n)
                    parts.append(f"chr({math_expr})")
                if len(parts) == 1:
                    new_value = ast.FormattedValue(
                        value=ast.parse(parts[0], mode="eval").body,
                        conversion=-1,
                        format_spec=None
                    )
                else:
                    expr = " + ".join(parts)
                    new_value = ast.FormattedValue(
                        value=ast.parse(expr, mode="eval").body,
                        conversion=-1,
                        format_spec=None
                    )
                new_values.append(new_value)
            elif isinstance(value, ast.FormattedValue):
                new_value = self.visit(value.value)
                new_values.append(ast.FormattedValue(
                    value=new_value,
                    conversion=value.conversion,
                    format_spec=self.visit(value.format_spec) if value.format_spec else None
                ))
            else:
                new_values.append(self.visit(value))
        
        self.in_joined_str = prev_in_joined_str
        node.values = new_values
        return node
    
    def visit_Constant(self, node):
        if isinstance(node.value, str) and not self.in_joined_str:
            new_elts = []
            for c in node.value:
                n = ord(c)
                math_expr = self.mathfuscate(n * 7 + 42)
                new_elts.append(
                    ast.Call(
                        func=ast.Name(id="chr", ctx=ast.Load()),
                        args=[
                            ast.BinOp(
                                left=ast.BinOp(
                                    left=ast.Call(
                                        func=ast.Name(id="eval", ctx=ast.Load()),
                                        args=[ast.Constant(value=math_expr)],
                                        keywords=[]
                                    ),
                                    op=ast.Sub(),
                                    right=ast.Constant(value=42)
                                ),
                                op=ast.FloorDiv(),
                                right=ast.Constant(value=7)
                            )
                        ],
                        keywords=[]
                    )
                )
            joined = ast.Call(
                func=ast.Attribute(value=ast.Constant(value=""), attr="join", ctx=ast.Load()),
                args=[ast.List(elts=new_elts, ctx=ast.Load())],
                keywords=[]
            )
            return ast.copy_location(joined, node)
        
        return node

    def mathfuscate(self, n, depth=4):
        if depth <= 0:
            return str(n)

        if n == 0:
            return "((2 - 1) - (1))"

        ops = ["+", "-", "*", "//"]
        op = secrets.choice(ops)

        if op == "+":
            a = random.randint(1, n)
            b = n - a
        elif op == "-":
            a = n + random.randint(2, 24)
            b = a - n
        elif op == "*":
            divisors = [i for i in range(2, n + 1) if n % i == 0]
            if not divisors:
                return str(n)
            a = secrets.choice(divisors)
            b = n // a
        elif op == "//":
            if n == 0:
                return "1 // 1"
            b = random.randint(2, 8)
            a = n * b

        return f"({self.mathfuscate(a, depth - 1)} {op} {self.mathfuscate(b, depth - 1)})"

def transform_code(raw):
    tree = ast.parse(raw)
    transformer = Transformer()
    tree = transformer.visit(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)

if __name__ == "__main__":
    raw = open("sources\\in.py", "rb").read()
    open("sources\\out.py", "wb").write(transform_code(raw).encode())
