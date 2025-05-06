import os
import shutil
import logging
import json
import glob
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

class BaseTraceProcessor(ABC):
    """
    Abstract base class for processing network traces.

    Subclasses must implement the _extract_relevant_files and _parse_raw_data
    methods to handle specific trace formats.
    """
    def __init__(self, trace_name: str, force_regenerate=False, print_stats=True, direction="both",
                 max_trace_len_mb=20, granularity_secs=1.0, clip_tput_mbps=[0.01, 2000.0]):
        """
        Initialize the BaseTraceProcessor with the name of the trace file.
        """
        self.trace_name = trace_name
        self.force_regenerate = force_regenerate
        self.print_stats = print_stats
        self.direction = direction
        self.max_trace_len_mb = max_trace_len_mb
        self.granularity_secs = granularity_secs
        self.clip_tput_mbps = clip_tput_mbps
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        proj_dir = os.path.dirname(current_dir)
        metadata_dir = os.path.join(proj_dir, 'metadata')
        raw_trace_dir = os.path.join(proj_dir, 'raw_traces')
        cooked_trace_dir = os.path.join(proj_dir, 'cooked_traces')
        self.metadata_path = os.path.join(metadata_dir, f"{trace_name}.json")
        self.raw_trace_path = os.path.join(raw_trace_dir, f"{trace_name}.zip")
        self.cooked_trace_path = os.path.join(cooked_trace_dir, f"{trace_name}")  # add number suffix and extension later
        self.temp_dir = os.path.join(proj_dir, 'temp')
        
        if not os.path.exists(self.metadata_path):
            raise FileNotFoundError(f"Metadata file {self.metadata_path} does not exist")
        try:
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
            logging.debug(f"Metadata loaded successfully from {self.metadata_path}")
        except json.JSONDecodeError as e:
            raise e
        
        if not os.path.exists(self.raw_trace_path) and "download_url" not in self.metadata:
            raise FileNotFoundError(f"Raw trace file {self.raw_trace_path} does not exist or download_url is missing in metadata")
        
        if not os.path.exists(cooked_trace_dir):
            os.makedirs(cooked_trace_dir, exist_ok=True)
            logging.debug(f"Created directory for cooked trace at {cooked_trace_dir}")
        
    
    @abstractmethod
    def _extract_files(self):
        """
        Extract relevant files from the raw trace.
        
        :return: List of extracted file paths.
        """
        pass
    
    @abstractmethod
    def _parse_raw_data(self, extracted_files):
        """
        Parse the raw data files.
        
        :param extracted_files: List of extracted file paths.
        :return: dataframe containing parsed data.
        """
        pass

    def process_trace(self):
        """
        Process the trace by extracting files and parsing raw data.
        Save the processed data to csv file/s.
        """
        check_files = glob.glob(f"{self.cooked_trace_path}*")
        if len(check_files) > 0 and not self.force_regenerate:
            logging.info(f"Cooked trace already exists at {self.cooked_trace_path}. Use -f/--force_regenerate to regenerate.") 
            return
        for file in check_files:
            os.remove(file)
            logging.debug(f"Removed existing cooked trace file: {file}")
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        extracted_files = self._extract_files()
        sorted(extracted_files)
        logging.info(f"Extracted {len(extracted_files)} files to {self.temp_dir}")
        logging.debug(f"Extracted files: {extracted_files}")
        
        df = self._parse_raw_data(extracted_files)
        logging.info(f"Parsed raw data from {len(extracted_files)} files")
            
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logging.debug(f"Temporary directory {self.temp_dir} removed")
            
        df = self.post_process(df)
        logging.info(f"Post-processing completed for {self.trace_name}")
        
        if self.print_stats: self.print_data_stats(df)
        
        self.save_to_csv(df)
        logging.info(f"Saved processed data to {self.cooked_trace_path}")
                        
    def post_process(self, df):
        """
        Post-process the trace data if needed.
        
        - get desired granularity
        - clip throughput values
        """
        directions = ['downlink', 'uplink'] if self.direction == 'both' else [self.direction]
        dfs = []
        for dir in directions:
            dir_df = df[df['dir'] == dir]
            if dir_df.empty:
                raise ValueError(f"Trace does not contain data for direction {dir}")
            for run_number in dir_df['run'].unique():
                run_df = dir_df[dir_df['run'] == run_number].copy(deep=True)
                run_df.sort_values(by=['time'], inplace=True)
                min_time_diff = run_df['time'].diff().min()
                if min_time_diff > self.granularity_secs:
                    raise ValueError(f"Minimum time difference {min_time_diff} is greater than the desired granularity {self.granularity_secs}")
                # bin and group by time
                run_df['time'] = np.floor(run_df['time'] / self.granularity_secs) * self.granularity_secs
                run_df = run_df.groupby(['run', 'time', 'dir', 'file'], as_index=False).agg({'tput': 'mean'})
                # fill in missing time slots
                time_range = np.arange(run_df['time'].min(), run_df['time'].max() + self.granularity_secs, self.granularity_secs)
                run_df = run_df.set_index('time').reindex(time_range, fill_value=0).reset_index()
                run_df.rename(columns={'index': 'time'}, inplace=True)
                assert len(run_df) == len(time_range), f"Number of rows {len(run_df)} does not match expected number of rows {len(time_range)}"
                # clip throughput values
                run_df['tput'] = np.clip(run_df['tput'], self.clip_tput_mbps[0], self.clip_tput_mbps[1])
                run_df['tput'] = run_df['tput']
                run_df['run'] = int(run_number)
                dfs.append(run_df)
        df = pd.concat(dfs, ignore_index=True)
        return df
    
    def save_to_csv(self, df):
        """
        Save the processed dataframe to a CSV file.
        
        - max_trace_len_mb split
        - save to csv
        """
        labels = {
            'downlink': 'dl',
            'uplink': 'ul'
        }
        directions = ['downlink', 'uplink'] if self.direction == 'both' else [self.direction]
        for dir in directions:
            dir_df = df[df['dir'] == dir].copy(deep=True)
            dir_df.drop(columns=['dir', 'file'], inplace=True)
            dir_df.sort_values(by=['run', 'time'], inplace=True)
            dir_df.reset_index(drop=True, inplace=True)
            df_size = df.memory_usage(deep=True).sum()
            chunks = int(df_size / (self.max_trace_len_mb * 1024 * 1024))
            if chunks > 1:
                chunk_size = int(len(dir_df) / chunks)
                for i in range(chunks):
                    start_idx = i * chunk_size
                    end_idx = (i + 1) * chunk_size if i < chunks - 1 else len(dir_df)
                    chunk_df = dir_df.iloc[start_idx:end_idx]
                    chunk_file_name = f"{self.cooked_trace_path}_{labels[dir]}_{i}.csv"
                    chunk_df.to_csv(f"{chunk_file_name}", index=False)
                    logging.debug(f"Saved chunk {i + 1}/{chunks} to {chunk_file_name}")
            else:
                chunk_file_name = f"{self.cooked_trace_path}_{labels[dir]}_0.csv"
                dir_df.to_csv(f"{chunk_file_name}", index=False)
                logging.debug(f"Saved data to {self.cooked_trace_path}")
    
    def print_data_stats(self, df):
        """
        Get statistics about the processed trace.
        
        :return: Dictionary containing statistics.
        """
        # compute stats for directions separately
        stats = {}
        directions = ['downlink', 'uplink'] if self.direction == 'both' else [self.direction]
        for dir in directions:
            dir_df = df[df['dir'] == dir]
            stats[dir] = {
                'num_runs': len(dir_df['run'].unique()),
                'num_datapoints': len(dir_df),
                'tput_mean': dir_df['tput'].mean(),
                'tput_std': dir_df['tput'].std(),
                'tput_min': dir_df['tput'].min(),
                'tput_max': dir_df['tput'].max(),
                'data_size_mb': dir_df.memory_usage(deep=True).sum() / (1024 * 1024),
                'data_files': int(dir_df.memory_usage(deep=True).sum() / (self.max_trace_len_mb * 1024 * 1024))
            }
        logging.info(f"Statistics for {self.trace_name}:")
        logging.info(json.dumps(stats, indent=4))
