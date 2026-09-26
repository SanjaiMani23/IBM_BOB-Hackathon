// Mock data for CodeLens frontend — replace with API calls for backend integration

export interface DiffLine {
  type: 'add' | 'remove' | 'context' | 'header';
  lineNum?: number;
  content: string;
}

export interface ChangedFile {
  path: string;
  additions: number;
  deletions: number;
  status: 'modified' | 'added' | 'deleted';
}

export type Severity = 'critical' | 'high' | 'medium' | 'low';

export interface Finding {
  id: string;
  severity: Severity;
  file: string;
  line: number;
  title: string;
  explanation: string;
  recommendation: string;
  type: 'bug' | 'optimization' | 'security' | 'structure';
}

export interface AnalysisSummary {
  filesAnalyzed: number;
  issuesDetected: number;
  optimizations: number;
  highPriority: number;
  analysisTime: string;
  commit: string;
  branch: string;
  repository: string;
}

export const mockChangedFiles: ChangedFile[] = [
  { path: 'src/services/payment.js', additions: 14, deletions: 6, status: 'modified' },
  { path: 'src/controllers/order.js', additions: 8, deletions: 3, status: 'modified' },
  { path: 'src/utils/validation.js', additions: 22, deletions: 0, status: 'added' },
  { path: 'src/models/cart.js', additions: 5, deletions: 9, status: 'modified' },
  { path: 'src/routes/checkout.js', additions: 3, deletions: 1, status: 'modified' },
  { path: 'src/middleware/auth.js', additions: 11, deletions: 4, status: 'modified' },
  { path: 'tests/payment.test.js', additions: 30, deletions: 2, status: 'modified' },
];

export const mockDiffLines: DiffLine[] = [
  { type: 'header', content: '--- a/src/services/payment.js' },
  { type: 'header', content: '+++ b/src/services/payment.js' },
  { type: 'header', content: '@@ -42,14 +42,18 @@ async function processPayment(order) {' },
  { type: 'context', lineNum: 42, content: '  const session = await db.startTransaction();' },
  { type: 'context', lineNum: 43, content: '  try {' },
  { type: 'remove', lineNum: 44, content: '-   const result = calculateTotal();' },
  { type: 'add', lineNum: 44, content: '+   const result = calculateTotal(items);' },
  { type: 'context', lineNum: 45, content: '    if (!result) {' },
  { type: 'remove', lineNum: 46, content: '-     return null;' },
  { type: 'add', lineNum: 46, content: '+     throw new PaymentError("Calculation failed");' },
  { type: 'context', lineNum: 47, content: '    }' },
  { type: 'add', lineNum: 48, content: '+   const charge = await stripe.charge({' },
  { type: 'add', lineNum: 49, content: '+     amount: result.total,' },
  { type: 'add', lineNum: 50, content: '+     currency: result.currency,' },
  { type: 'add', lineNum: 51, content: '+   });' },
  { type: 'context', lineNum: 52, content: '    await session.commit();' },
  { type: 'context', lineNum: 53, content: '    return charge;' },
  { type: 'header', content: '@@ -68,6 +72,9 @@ async function processPayment(order) {' },
  { type: 'context', lineNum: 68, content: '  const items = await db.query(' },
  { type: 'remove', lineNum: 69, content: '-   `SELECT * FROM cart WHERE user_id = ${userId}`' },
  { type: 'add', lineNum: 69, content: '+   `SELECT * FROM cart WHERE user_id = $1`, [userId]' },
  { type: 'context', lineNum: 70, content: '  );' },
  { type: 'add', lineNum: 71, content: '+   if (!items.length) return { total: 0, items: [] };' },
  { type: 'context', lineNum: 72, content: '  for (const item of items) {' },
  { type: 'remove', lineNum: 73, content: '-   price += getPrice(item.id);' },
  { type: 'add', lineNum: 73, content: '+   price += await getPrice(item.id);' },
  { type: 'context', lineNum: 74, content: '  }' },
];

export const mockFindings: Finding[] = [
  {
    id: 'f1',
    severity: 'high',
    file: 'src/services/payment.js',
    line: 44,
    title: 'Potential null reference',
    explanation:
      'The changed function accesses the response object without first validating whether the API returned valid data. If the upstream service returns null or undefined, subsequent property accesses will throw a runtime exception.',
    recommendation:
      'Add response validation before property access. Use optional chaining (?.) or explicit null guard before accessing result.total and result.currency.',
    type: 'bug',
  },
  {
    id: 'f2',
    severity: 'high',
    file: 'src/services/payment.js',
    line: 73,
    title: 'Repeated async call inside loop',
    explanation:
      'getPrice() is now awaited inside a for...of loop. Each iteration triggers a separate database round-trip. For large carts this will degrade response time significantly and may saturate the connection pool.',
    recommendation:
      'Batch the price lookup outside the loop using a single query. Use Promise.all() if concurrent fetches are acceptable, or preferably batch-load all item IDs in one SQL query.',
    type: 'optimization',
  },
  {
    id: 'f3',
    severity: 'medium',
    file: 'src/controllers/order.js',
    line: 18,
    title: 'Missing transaction rollback on error',
    explanation:
      'The catch block in the changed function does not call session.rollback(). A failed payment operation will leave the database transaction open, which can lead to lock contention under load.',
    recommendation:
      'Add session.rollback() in the catch block before re-throwing. Consider wrapping the entire try/catch pattern in a utility that guarantees rollback.',
    type: 'bug',
  },
  {
    id: 'f4',
    severity: 'medium',
    file: 'src/middleware/auth.js',
    line: 31,
    title: 'JWT secret read inside request handler',
    explanation:
      'The updated code reads process.env.JWT_SECRET on every incoming request rather than caching it at module initialization. While not a critical bug, this adds unnecessary overhead to every authenticated route.',
    recommendation:
      'Cache the secret in a module-level constant at startup. This avoids repeated environment variable lookups on hot paths.',
    type: 'optimization',
  },
  {
    id: 'f5',
    severity: 'medium',
    file: 'src/utils/validation.js',
    line: 5,
    title: 'Duplicate validation logic',
    explanation:
      'The newly added validation.js module re-implements email and phone validation that already exists in src/helpers/validators.js. This creates two sources of truth that will diverge over time.',
    recommendation:
      'Remove the duplicate implementations and import from the existing validators module. If behavioural differences are intentional, document them clearly.',
    type: 'structure',
  },
  {
    id: 'f6',
    severity: 'low',
    file: 'src/models/cart.js',
    line: 77,
    title: 'Unnecessary abstraction layer',
    explanation:
      'The CartItem wrapper class introduced in this change wraps a plain object with no additional methods or validation. It adds indirection without benefit at this stage.',
    recommendation:
      'Use a TypeScript interface or plain Zod schema instead of a class if no methods are needed. Remove the class if it is purely structural.',
    type: 'structure',
  },
  {
    id: 'f7',
    severity: 'low',
    file: 'src/routes/checkout.js',
    line: 12,
    title: 'Console.log left in production path',
    explanation:
      'A console.log statement was introduced in the checkout route handler. This will output sensitive order data to server logs in production.',
    recommendation:
      'Remove the console.log or replace with a structured logger that respects log level configuration.',
    type: 'bug',
  },
  {
    id: 'f8',
    severity: 'critical',
    file: 'src/services/payment.js',
    line: 69,
    title: 'SQL injection vector removed — verify migration',
    explanation:
      'The diff shows the raw string interpolation in the SQL query was changed to a parameterized query. This is a security improvement. However, the old insecure pattern may still exist in other query sites that were not part of this diff.',
    recommendation:
      'Run a codebase-wide search for template literal SQL patterns. Audit all other db.query() callsites to ensure parameterization is applied consistently.',
    type: 'security',
  },
];

export const mockSummary: AnalysisSummary = {
  filesAnalyzed: 7,
  issuesDetected: 8,
  optimizations: 3,
  highPriority: 3,
  analysisTime: '1.42s',
  commit: 'a7f3c2e',
  branch: 'feature/payment-refactor',
  repository: 'acme-corp/checkout-service',
};
