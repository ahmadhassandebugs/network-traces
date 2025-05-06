import argparse

from processors.trace1 import Trace1Processor

def main():
    parser = argparse.ArgumentParser(description="Process trace files.")
    parser.add_argument("-t", "--trace", type=str, required=True,
                        help="Trace name (e.g., trace1, trace2, etc.)")
    parser.add_argument("-p", "--print_stats", action="store_true",
                        help="Print statistics after processing")
    parser.add_argument("-f", "--force_regenerate", action="store_true",
                        help="Force regeneration of cooked trace")
    parser.add_argument("-m", "--max_trace_len_mb", type=float, default=20,
                        help="Maximum trace length in MB")
    parser.add_argument("-g", "--granularity_secs", type=float, default=1.0,
                        help="Granularity in seconds")
    parser.add_argument("-c", "--clip_tput_mbps", type=float, nargs=2, default=[0.01, 2000.0],
                        help="Clip throughput in Mbps (min, max)")
    args = parser.parse_args()

    if args.trace == "trace1":
        processor = Trace1Processor(
            print_stats=args.print_stats,
            force_regenerate=args.force_regenerate,
            max_trace_len_mb=args.max_trace_len_mb,
            granularity_secs=args.granularity_secs,
            clip_tput_mbps=args.clip_tput_mbps
        )
    else:
        raise ValueError(f"Trace {args.trace} is not supported. Please choose a valid trace name.")
    
    processor.process_trace()


if __name__ == "__main__":
    main()
