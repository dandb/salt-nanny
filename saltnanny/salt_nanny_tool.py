from argparse import ArgumentParser
from .salt_nanny import SaltNanny


def get_args():
    parser = ArgumentParser()
    parser.add_argument('host', type=str, help='Redis Host that stores salt returns.')
    parser.add_argument('minions', type=str, nargs='+', help='List of Highstated Minions')
    parser.add_argument('-t', '--type', action='store', dest='type', type=str, default='redis', help='Type of external job cache(redis/etc).')
    parser.add_argument('-p', '--port', action='store', dest='port', type=int, default=6379, help='Redis port.')
    parser.add_argument('-l', '--log', action='store', dest='log_file', type=str, default=None, help='Log file.')
    parser.add_argument('-e', '--custom-event', action='store', dest='custom_event', type=str, default='state.highstate', help='Custom Event if this is not a highstate')
    parser.add_argument('-x', '--max-attempts', action='store', dest='max_attempts', type=int, default=15, help='Custom Event if this is not a highstate')
    parser.add_argument('-I', '--intervals', action='store', dest='intervals', type=int, nargs=3, default=[15, 60, 2], help='Custom Wait intervals and multiplier')
    parser.add_argument('-r', '--last-return', action='store_true', dest='last_return', help='Fetch last highstate result.')
    parser.add_argument('-j', '--earliest-jid', action='store', dest='earliest_jid', nargs='?', default=0, type=int, help='Fetch last highstate result stored after this time')
    return parser.parse_args()


def tool_main():
    args = get_args()
    cache_config = {'type': args.type, 'host': args.host, 'port': args.port, 'db': '0'}
    salt_nanny = SaltNanny(cache_config, args.log_file, args.custom_event, args.intervals[0], args.intervals[1], args.intervals[2])
    salt_nanny.initialize(args.minions)
    return salt_nanny.parse_last_return(args.earliest_jid) if args.last_return else salt_nanny.track_returns(args.max_attempts)


def main():  # pragma: no cover
    exit(tool_main())


if __name__ == '__main__':  # pragma: no cover
    main()
