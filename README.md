# Network Traces

A public repository of diverse network traces for use in reproducible network emulation experiments. This dataset supports research in network protocols, mobile systems, and performance benchmarking.

## Repository Structure

```python
network-traces/
├── raw_traces/             # Zipped raw traces (can be coooked or not)
│   ├── trace1.zip
│   ├── trace2.zip
│   └── ...
├── metadata/               # Metadata JSON files per trace
│   └── trace1.json
├── processors/             # Trace processing scripts per trace type
│   └── trace_1_processor.py
├── dataloader/             # Shared numpy-based trace loader
│   └── dataloader.py
├── tools/                  # Conversion tools (e.g., mm_trace_gen)
│   └── mm_trace_gen.py
├── README.md
└── requirements.txt
```

```json
{
  "name": "trace1",
  "source": "WiFi 802.11ac",
  "label": "wifi-ac",
  "type": "raw",
  "description": "WiFi 802.11ac trace from a crowded environment",
  "date": "2023-06-15",
  "granularity_secs": 1,
  "unit": "Mbps",
  "direction": "downlink",
  "download_url": "https://example.com/wifi_ac_trace1.zip",
  "processor_script": "processors/wifi_ac_processor.py"
}
```

### 🛠️ Trace Processor

Located in `processors/`, each script implements a class that:

- Loads the raw trace  
- Fills missing or zero values (e.g., below `0.01 Mbps`)  
- Normalizes to fixed granularity (e.g., 1 sec)  
- Offers dry-run summary statistics before processing  

---

### 📦 Shared DataLoader

Located in `dataloader/dataloader.py`. Loads any processed trace into standardized NumPy format. Handles:

- Duration clipping  
- Scaling  
- Optional filtering  

---

### 🧪 MM Trace Generator

`tools/mm_trace_gen.py`:

- Converts cooked traces to Mahimahi format  
- Estimates total output size and prompts user  
- Supports batching, splitting, and format validation  

## Scratchpad

- each trace is zipped file, has a name and a readme file, has associated metadata in another json file, has a processing class derived from the template class
- if zip file is large, download it from the link in the metadata file
- this should generate cooked traces with 1 sec granularity (fill in missing values) given trace len in secs and max traces
  - some other options are avg. max min throughput, and scaling factor
  - dry run option to show the stats of the traces before generating cooked traces
- an optional data loader class to load the traces in numpy arrays given trace name
- a mm_trace_gen class to convert cokked traces to mm traces
  - show total size of the traces in bytes beforehand with rough estimate and prompt to continue or not

- add dates or readme files to the traces
- networks: wifi (ac, ad), cellular (4G, 5G), satellite (LEO), fixed (LAN)
- remove zero values in the traces by default (delat = 0.01 Mbps)
