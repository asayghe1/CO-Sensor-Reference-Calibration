# External public dataset

The source dataset is [Gas sensor array temperature modulation (UCI 487)](https://archive.ics.uci.edu/dataset/487/gas+sensor+array+temperature+modulation), DOI [10.24432/C5S302](https://doi.org/10.24432/C5S302). UCI lists the citation as J. Burgus (2018), and the data license as [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Credit UCI and the dataset creator; see `../DATA_LICENSE.md`.

The release's saved-evidence reproduction needs **no raw-data download**. For optional source-data provenance inspection, use the official UCI record's **Download** button. Keep the resulting approximately 175 MB download outside Git tracking; do not add it to this repository. Rename the outer download to `uci487.zip` in the ignored directory below:

```text
data/
  DATASET_MANIFEST.json
  README.md
  external/                       # ignored; absent from release
    uci487.zip                    # official outer download
      README.txt                  # member of outer archive
      gas-sensor-array-temperature-modulation.zip
        README.txt                # member of nested archive
        20160930_203718.csv        # D1
        20161001_231809.csv        # D2
        20161003_085624.csv        # D3: excluded nonmonotonic clock
        20161004_104124.csv        # D4
        20161005_140846.csv        # D5: development initialization
        20161006_182224.csv        # D6: development assessment
        20161007_210049.csv        # D7: development initialization
        20161008_234508.csv        # D8: development assessment
        20161010_095046.csv        # D9: development initialization
        20161011_113032.csv        # D10: development assessment / C5 initialization
        20161013_143355.csv        # D11: completed C5 assessment
        20161014_184659.csv        # D12: completed C5 assessment
        20161016_053656.csv        # D13: completed C5 assessment
```

The nested names above describe archive membership, not a requirement to unpack all members. The archive has 20 raw columns: time, CO, humidity, temperature, flow, heater and R1–R14. Only R1–R6 and R8–R13 entered the released scientific analyses. No raw columns or raw measurement CSVs are included in this repository. UCI270 is not a dependency.

Historically verified hashes:

- Outer archive SHA256: `cb5ce4a6af1a51b933d1979952d7845f0e9baac54e15a81a1e3599e8b85905d4`
- Nested archive SHA256: `4a6b4e3609aeff297dcbed084e7c85f1c88a8c5219417afebe99281c369dcd11`

These are project-verified identifiers, not checksums published by UCI. File/member sizes and hashes are in `DATASET_MANIFEST.json`, copied from the frozen input manifest. No new raw archive download or reserved-data inspection was performed for this release.

After a separate download, optional hash verification is:

```sh
python scripts/verify_dataset.py data/external/uci487.zip
```

This checks opaque archive bytes and the nested archive hash, without extracting or parsing raw sensor records. A mismatch must be investigated as a dataset/version difference. Do not overwrite the historical hashes to make a changed download pass. The original historical source expected the outer file at `data/co_chamber/uci487.zip`; that path is documented for provenance only and is not a requirement of the supported saved-evidence workflow.
