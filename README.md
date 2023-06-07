# Instant Messaging Meets Video Conferencing: Studying the Performance of IM Video Calls
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8006901.svg)](https://doi.org/10.5281/zenodo.8006901)

This repository holds the data associated to the [TMA 2023](https://tma.ifip.org/2023/accepted-papers/) [paper](https://www.comsys.rwth-aachen.de/fileadmin/papers/2023/2023-grote-mvca-fairness.pdf) of the same name.

# Publication

* Laurenz Grote, Ike Kunze, Constantin Sander, and Klaus Wehrle: *Instant Messaging Meets Video Conferencing: Studying the Performance of IM Video Calls*. In Proceedings of the IFIP/IEEE Network Traffic Measurement and Analysis Conference (TMA '23), 2023.

If you use any portion of our work, please consider citing our publication.

```
@Inproceedings {2023-grote-mvca-fairness,
   title = {Instant Messaging Meets Video Conferencing: Studying the Performance of IM Video Calls},
   year = {2023},
   month = {6},
   publisher = {IFIP/IEEE},
   booktitle = {Proceedings of the Network Traffic Measurement and Analysis Conference (TMA '23)},
   author = {Grote, Laurenz and Kunze, Ike and Sander, Constantin and Wehrle, Klaus}
}
```

# data/: Dataset

Holds the data set containing all the data plotted in the paper as well as additional measurements.
Data format:

All measurements are indexed by `index.csv`.
Every row in this file identifies a measurement by a GUID and contains all relevant metadata (scenario type, available bandwidth...).
Statistics on the packet level (throughput, queueing, loss and whether the call broke down during the experiment) are supplemented by `index_avgbwdist.csv`.
You should be able to easily join these files on the GUID column.

Where applicable, `index_qoe.csv` contains the aggregate BRISQUE value for the entire call as described in the paper.

The bandwidth profile style (Figure 3) measurements are contained in `bwprofiles.csv.gz`.
After decompression, you get all throughput samples of all measurement calls concatenated together.

# code/: Code Repository

Contains the code used to instrument the test bed.
Undocumented and never deployed beyond our very own test bed.
The code is not runnable as-is.
You need prepare the testbed computers as well as configure IP addresses, hostnames, paths and e-mail addresses within the code base.
Beyond here might be dragons.
