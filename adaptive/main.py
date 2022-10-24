#!/usr/bin/env python3

import sys

tasks = {
    'analyze': 'Analyze sequencing run',
    'test': 'Test adaptive functionality on a small dataset',
}

ordered_tasks = [
    'create',
    'test',
]


def print_usage_and_exit():
    print('Usage: adaptive <command> [options] <required arguments>', file=sys.stderr)
    print('\nTo get minimal usage for a command use:\n adaptive command', file=sys.stderr)
    print('\nTo get full help for a command use one of:\n adaptive command -h\nadaptive command --help\n', file=sys.stderr)
    print('\nAvailable commands:\n', file=sys.stderr)
    max_task_length = max([len(x) for x in list(tasks.keys())]) + 1
    for task in ordered_tasks:
        print('{{0: <{}}}'.format(max_task_length).format(task), tasks[task], sep=' ', file=sys.stderr)
    sys.exit(0)

def main():

    if len(sys.argv) == 1 or sys.argv[1] in ['-h', '-help', '--help']:
        print_usage_and_exit()

    task = sys.argv.pop(1)

    if task not in tasks:
        print('Task "' + task + '" not recognised. Cannot continue.\n', file=sys.stderr)
        print_usage_and_exit()

    exec('import  adaptive.' + task)
    exec(' adaptive.' + task + '.run()')

# call main function
if __name__ == '__main__':
    main()