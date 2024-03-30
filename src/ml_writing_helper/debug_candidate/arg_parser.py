import argparse


def arg_parser():
    parser = argparse.ArgumentParser(description='ML Writing Helper')
    # parser.add_argument('--debug', action='store_true', help='Debug mode')
    # parser.add_argument('--input', type=str, help='Input file')
    parser.add_argument('--output', choices=['eps', 'pdf', 'png'], help='Output Extension')
    return parser.parse_args()
