import kagglehub

path = kagglehub.dataset_download(
    "tunguz/online-retail",
    output_dir="./data/raw"
)