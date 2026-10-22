"""Inspect or save a redacted local support report."""
import json


def add_parser(subp):
    parser = subp.add_parser('diagnostics', help='Preview or export redacted diagnostics')
    sub = parser.add_subparsers(dest='diagnostics_sub', required=True)
    sub.add_parser('show', help='Show the redacted report').set_defaults(func=run)
    export = sub.add_parser('export', help='Save a redacted ZIP archive locally')
    export.add_argument('--out', required=True)
    export.set_defaults(func=run)
    return parser


def run(args):
    from src.cli.common import bootstrap
    from src.cli.output import set_result
    from src.controllers.diagnostics import collect_diagnostics, write_diagnostics
    report = collect_diagnostics(bootstrap())
    if args.diagnostics_sub == 'show':
        set_result(report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        write_diagnostics(args.out, report)
        set_result(dict(path=args.out, redacted=True))
        print(f'Diagnostic archive saved: {args.out}')
    return 0
