import argparse
import json
import os
import sys

def run(args):
    print(args)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('days', type=int, help='Number of days in the future to look')

    sys.exit(run(parser.parse_args()))
