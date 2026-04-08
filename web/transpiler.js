class ASTNode {}

class Program      extends ASTNode { constructor(stmts)    { super(); this.statements = stmts; } }
class NumberNode   extends ASTNode { constructor(v)        { super(); this.value = v; } }
class StringNode   extends ASTNode { constructor(v)        { super(); this.value = v; } }
class Identifier   extends ASTNode { constructor(n)        { super(); this.name = n; } }
class Assignment   extends ASTNode { constructor(n, v)     { super(); this.name = n; this.value = v; } }
class Print        extends ASTNode { constructor(e)        { super(); this.expression = e; } }
class BinaryOp     extends ASTNode { constructor(l, op, r) { super(); this.left = l; this.op = op; this.right = r; } }
class FunctionCall extends ASTNode { constructor(n, a)     { super(); this.name = n; this.args = a; } }

class If extends ASTNode {
  constructor(cond, body, elifs = [], elseBody = []) {
    super();
    this.condition    = cond;
    this.body         = body;
    this.elif_clauses = elifs;
    this.else_body    = elseBody;
  }
}

class While extends ASTNode {
  constructor(cond, body) {
    super();
    this.condition = cond;
    this.body = body;
  }
}

class For extends ASTNode {
  constructor(v, start, stop, step, body) {
    super();
    this.var   = v;
    this.start = start;
    this.stop  = stop;
    this.step  = step;
    this.body  = body;
  }
}

function reviveAST(obj) {
  if (!obj || typeof obj !== 'object') return obj;

  switch (obj.type) {
    case 'Program':
      return new Program((obj.statements || []).map(reviveAST));

    case 'Assignment':
      return new Assignment(obj.name, reviveAST(obj.value));

    case 'Print':
      return new Print(reviveAST(obj.expression));

    case 'BinaryOp':
      return new BinaryOp(reviveAST(obj.left), obj.op, reviveAST(obj.right));

    case 'If':
      return new If(
        reviveAST(obj.condition),
        (obj.body         || []).map(reviveAST),
        (obj.elif_clauses || []).map(([c, b]) => [reviveAST(c), b.map(reviveAST)]),
        (obj.else_body    || []).map(reviveAST)
      );

    case 'While':
      return new While(
        reviveAST(obj.condition),
        (obj.body || []).map(reviveAST)
      );

    case 'For':
      return new For(
        obj.var,
        reviveAST(obj.start),
        reviveAST(obj.stop),
        obj.step ? reviveAST(obj.step) : null,
        (obj.body || []).map(reviveAST)
      );

    case 'FunctionCall':
      return new FunctionCall(obj.name, (obj.args || []).map(reviveAST));

    case 'NumberNode':
      return new NumberNode(obj.value);

    case 'StringNode':
      return new StringNode(obj.value);

    case 'Identifier':
      return new Identifier(obj.name);

    default:
      // Unknown node type — just pass it through as-is
      return obj;
  }
}

async function runPipeline(sourceCode) {
  let raw;

  try {
    const resp = await fetch('/api/transpile', {
      method:      'POST',
      headers:     { 'Content-Type': 'application/json' },
      body:        JSON.stringify({ source: sourceCode }),
      credentials: 'include',
    });

    if (!resp.ok) {
      return {
        tokens: null, ast: null, symbolTable: null,
        optimizedAst: null, jsCode: null,
        unsupported: [],
        error: {
          stage:   'Network',
          message: `Server returned ${resp.status} ${resp.statusText}`,
        },
      };
    }

    raw = await resp.json();

  } catch (err) {
    return {
      tokens: null, ast: null, symbolTable: null,
      optimizedAst: null, jsCode: null,
      unsupported: [],
      error: {
        stage:   'Network',
        message: `Could not reach the backend: ${err.message}`,
      },
    };
  }

  // Turn the plain JSON trees back into class instances
  if (raw.ast)          raw.ast          = reviveAST(raw.ast);
  if (raw.optimizedAst) raw.optimizedAst = reviveAST(raw.optimizedAst);

  return raw;
}
function formatTokens(tokens) {
  if (!tokens || !tokens.length) return 'No tokens.';

  const rows = tokens
    .filter(t => t.type !== 'EOF')
    .map(t => `${String(t.type).padEnd(20)} ${String(t.value).padEnd(15)} line ${t.line}`);

  const header = `${'TYPE'.padEnd(20)} ${'VALUE'.padEnd(15)} POSITION`;
  const divider = '-'.repeat(55);

  return `${header}\n${divider}\n${rows.join('\n')}`;
}