import os
import shutil
import logging
import json
import glob
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BaseTraceProcessor(ABC):
    """
    Abstract base class for processing network traces.

    Subclasses must implement the _extract_relevant_files and _parse_raw_data
    methods to handle specific trace formats.
    """
    def __init__(self, trace_name: str, force_regenerate=False, print_stats=True,
                 max_trace_len_mb=20, granularity_secs=1.0, clip_tput_mbps=[0.01, 2000.0]):
        """
        Initialize the BaseTraceProcessor with the name of the trace file.
        """
        self.trace_name = trace_name
        self.force_regenerate = force_regenerate
        self.print_stats = print_stats
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
        
        if len(glob.glob(os.path.join(self.cooked_trace_path, '*'))) > 0 and not force_regenerate:
            logging.info(f"Cooked trace already exists at {self.cooked_trace_path}_NUM.csv... skipping processing.")
            return
        
        if not os.path.exists(self.metadata_path):
            logging.error(f"Metadata file {self.metadata_path} does not exist.")
            raise FileNotFoundError(f"Metadata file {self.metadata_path} does not exist.")
        try:
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
            logging.debug(f"Metadata loaded successfully from {self.metadata_path}.")
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from {self.metadata_path}: {e}")
            raise e
        
        if not os.path.exists(self.raw_trace_path) and "download_url" not in self.metadata:
            logging.error(f"Raw trace file {self.raw_trace_path} does not exist or download_url is missing in metadata.")
            raise FileNotFoundError(f"Raw trace file {self.raw_trace_path} does not exist or download_url is missing in metadata.")
        
        if not os.path.exists(self.cooked_trace_path):
            os.makedirs(self.cooked_trace_path, exist_ok=True)
            logging.debug(f"Created directory for cooked trace at {self.cooked_trace_path}.")
        
    
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
        """
        pass

    def process_trace(self):
        """
        Process the trace by extracting files and parsing raw data.
        Save the processed data to csv file/s.
        """
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        extracted_files = self._extract_files()
        logging.info(f"Extracted {len(extracted_files)} files to {self.temp_dir}.")
        logging.debug(f"Extracted files: {extracted_files}")
        
        self._parse_raw_data(extracted_files)
        logging.info(f"Saved processed data to {self.cooked_trace_path}.")
            
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logging.debug(f"Temporary directory {self.temp_dir} removed.")
            
        if self.print_stats:
            stats = self.get_stats()
            print(f"Statistics: {stats}")
    
    def get_stats(self):
        """
        Get statistics about the processed trace.
        
        :return: Dictionary containing statistics.
        """
        pass
