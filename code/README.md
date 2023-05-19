# MVCA Study Scripts
This repo contains all scripts used to control the MVCA study.

```
├──bootstrap/                                     Scripts to start the machines. Auto-invoked at boot.
│   ├── avdrunner/                                For machines running AVDs
│   ├── tcprunner/                                For machines running TCP endpoints
│   └── router/                                   For the machine running the router
│
├──controlscripts/                                Scripts to control the running machines
│   ├── avdrunner/                                For machines running AVDs
│   ├── tcprunner/                                For machines running TCP endpoints
│   ├── router/                                   For the machine running the router
│   └── orchestration/                            Orchestration scripts running on the router
│
└──evalscripts/                                   Scripts to evaluate the measurements and generate plots
```

