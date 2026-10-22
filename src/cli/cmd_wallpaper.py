"""Offline wallpaper/template package validation."""


def add_parser(subp):
    parser = subp.add_parser('wallpaper', help='Inspect wallpaper packages without a device')
    sub = parser.add_subparsers(dest='wallpaper_sub', required=True)
    validate = sub.add_parser('validate', help='Check ZIP integrity, layout and document syntax')
    validate.add_argument('path')
    validate.add_argument('--ios-version', default=None, help='Check template iOS version constraints')
    validate.set_defaults(func=run)
    return parser


def run(args):
    from src.cli.output import set_result
    from src.controllers.wallpaper_validation import validate_wallpaper, validation_text
    report = validate_wallpaper(args.path, args.ios_version)
    set_result(report)
    print(validation_text(report))
    return 0 if report['valid'] else 1
