import argparse

from pen.eleksdraw import DEFAULT_SERIAL_PORT
from pen.eleksdraw import DRAW_HEIGHT_EU
from pen.eleksdraw import DRAW_WIDTH_EU
from pen.gcode import GCode
from pen.plotter import run_gcode, soft_reset
from pen.gcode import get_gcode_bounds


def up_main(args):
    run_gcode([GCode.pen_up()], device=args.device)


def down_main(args):
    run_gcode([GCode.pen_down()], device=args.device)


def move_main(args):
    run_gcode([GCode.move_fast(args.x, args.y)], device=args.device)


def reset_main(args):
    soft_reset(args.device)


def draw_main(args):
    commands = []
    with open(args.gcode) as r:
        for line in r:
            commands.append(line.strip())

    gcode_rect = get_gcode_bounds(commands)
    x_min, x_max, y_min, y_max = gcode_rect.to_xxyy()

    print('Bounds: {} {} {} {}'.format(x_min, x_max, y_min, y_max))

    # Maybe in the future we support some sort of 'glitch mode?'
    if x_min < 0.0 or x_max > DRAW_WIDTH_EU:
        raise RuntimeError('Invalid x boundaries! {} {}'.format(x_min, x_max))
    if y_min < 0.0 or y_max > DRAW_HEIGHT_EU:
        raise RuntimeError('Invalid y boundaries: {} {}'.format(y_min, y_max))

    trace_bounds_commands = [
        GCode.move_fast([0, 0]),
        GCode.move_fast([x_min, y_min]),
        GCode.move_fast([x_max, y_min]),
        GCode.move_fast([x_max, y_max]),
        GCode.move_fast([x_min, y_max]),
        GCode.move_fast([x_min, y_min]),
    ]

    all_commands = trace_bounds_commands

    all_commands.append(GCode.set_feed_rate(args.feed_rate))

    if args.frame:
        all_commands += [
            GCode.move_fast(0, 0),
            GCode.pen_down(),
            GCode.move_linear([x_min, y_min], 2000),
            GCode.move_linear([x_max, y_min], 2000),
            GCode.move_linear([x_max, y_max], 2000),
            GCode.move_linear([x_min, y_max], 2000),
            GCode.move_linear([x_min, y_min], 2000),
            GCode.pen_up(),
        ]

    if not args.test:
        all_commands += commands

    all_commands.append(GCode.move_home())

    if args.no_pen:
        all_commands = [command for command in commands if not GCode.is_pen_down_command(command)]

    run_gcode(all_commands, device=args.device)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', default=DEFAULT_SERIAL_PORT)

    subparsers = parser.add_subparsers()


    up_parser = subparsers.add_parser('up')
    up_parser.set_defaults(main=up_main)

    down_parser = subparsers.add_parser('down')
    down_parser.set_defaults(main=down_main)

    move_parser = subparsers.add_parser('move')
    move_parser.add_argument('--x', type=float)
    move_parser.add_argument('--y', type=float)
    move_parser.set_defaults(main=move_main)

    reset_parser = subparsers.add_parser('reset')
    reset_parser.set_defaults(main=reset_main)

    draw_parser = subparsers.add_parser('draw')
    draw_parser.add_argument('--gcode')
    draw_parser.add_argument('--feed_rate', default=1000, type=int)
    draw_parser.add_argument('--test', action='store_true')
    draw_parser.add_argument('--frame', action='store_true')
    draw_parser.add_argument('--no_pen', action='store_true')
    draw_parser.set_defaults(main=draw_main)

    args = parser.parse_args()

    if not hasattr(args, 'main'):
        parser.print_help()
        return -1
    args.main(args)


if __name__ == '__main__':
    main()
