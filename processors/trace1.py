import os
import zipfile

from .base import BaseTraceProcessor

class Trace1Processor(BaseTraceProcessor):
    def __init__(self, force_regenerate=False, print_stats=True,
                 max_trace_len_mb=20, granularity_secs=1.0, clip_tput_mbps=[0.01, 2000.0]):
        super().__init__("trace1", force_regenerate, print_stats,
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
        pass
