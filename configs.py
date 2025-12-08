DATA_PATH = "./data/RT_IOT2022.csv"     # <-- set the CSV path here
LABEL_COL_OVERRIDE = "Attack_type"      # <-- set label column name if auto-detect fails (e.g. 'label')

FEATURES_LIST = [
    "active.avg",
    "bwd_bulk_packets",
    "bwd_data_pkts_tot",
    "bwd_header_size_max",
    "bwd_iat.std",
    "bwd_pkts_payload.std",
    "bwd_pkts_per_sec",
    "flow_iat.max",
    "flow_iat.std",
    "flow_iat.tot",
    "flow_pkts_payload.max",
    "flow_pkts_payload.tot",
    "flow_pkts_per_sec",      
    "fwd_data_pkts_tot",
    "fwd_iat.tot",
    "idle.avg",
    "idle.max",
    "idle.min",
    "idle.tot",
    "payload_bytes_per_second"
]

N_KEEP = 20                          # number of features to keep (paper used 21)
SEEDS = list(range(10))              # 10 seeds as in paper
TEST_SIZE = 0.20                    # 80:20 train/test split
KNN_K = 5
