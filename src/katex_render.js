// Reads a JSON array of {tex, display} from stdin, prints a JSON array of HTML strings.
const katex = require('katex');
let input = '';
process.stdin.on('data', d => (input += d));
process.stdin.on('end', () => {
  const items = JSON.parse(input);
  const out = items.map(({ tex, display }) => {
    try {
      return katex.renderToString(tex, { displayMode: display, output: 'html', throwOnError: true, strict: 'ignore' });
    } catch (e) {
      console.error('KaTeX error in: ' + tex + '\n' + e.message);
      process.exitCode = 1;
      return '<span class="katex-error">' + tex + '</span>';
    }
  });
  process.stdout.write(JSON.stringify(out));
});
