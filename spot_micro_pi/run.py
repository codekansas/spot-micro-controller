import argparse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    if args.debug:
        print('Debug mode enabled')
    else:
        print('Debug mode disabled')


if __name__ == "__main__":
    main()
