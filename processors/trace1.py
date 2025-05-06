import os
import zipfile
import logging
import pandas as pd

from .base import BaseTraceProcessor

class Trace1Processor(BaseTraceProcessor):
    def __init__(self, force_regenerate=False, print_stats=True, direction="both",
                 max_trace_len_mb=20, granularity_secs=1.0, clip_tput_mbps=[0.01, 2000.0]):
        super().__init__("trace1", force_regenerate, print_stats, direction,
                         max_trace_len_mb, granularity_secs, clip_tput_mbps)
    
    def _extract_files(self):    
        with zipfile.ZipFile(self.raw_trace_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)
            
        extracted_files = []
        for root, _, files in os.walk(self.temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                extracted_files.append(file_path)
        return extracted_files

    def _parse_raw_data(self, extracted_files):
        for f_idx, file in enumerate(extracted_files):
            logging.debug(f"\tprocessing file {f_idx + 1}/{len(extracted_files)}: {file}")
            df = pd.read_csv(file, low_memory=False)
            directions = ['downlink', 'uplink'] if self.direction == 'both' else [self.direction]
            dfs = []
            for dir in directions:
                dir_df = df[df['direction'] == dir][['timestamp', 'run_number', 'Throughput']]
                if dir_df.empty:
                    raise ValueError(f"File {file} does not contain data for direction {dir}")
                logging.debug(f"\t\tunique run numbers in {dir} data: {dir_df['run_number'].nunique()}")
                dir_df['timestamp'] = pd.to_datetime(dir_df['timestamp'])
                for run_number in dir_df['run_number'].unique():
                    run_df = dir_df[dir_df['run_number'] == run_number].copy(deep=True)
                    min_timestamp = run_df['timestamp'].min()
                    run_df['timestamp'] = (run_df['timestamp'] - min_timestamp).dt.total_seconds()
                    run_df['file'] = os.path.basename(file)
                    run_df['direction'] = dir
                    dfs.append(run_df)
            df = pd.concat(dfs, ignore_index=True)
            df.rename(columns={'timestamp': 'time', 'Throughput': 'tput', 'direction': 'dir',
                               'run_number': 'run', 'file': 'file'}, inplace=True)
        return df
