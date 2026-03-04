# Learning Journal

Notes and random thoughts landing page for experimenting with the models and application.

## 3/4/26

[Generated Newsletter](2026-03-04-Newsletter.md)

- qwen3.5:9b is badass
- running on my homelab with less vram causes the researcher to just dump a summary cause the context is much smaller 4096 vs 3768 on the macbook, unified memory is really quite awesome.
- the 4b size of qwen3.5 was noticeably worse when it came to handling incomplete articles and following directions. the editor never caught on that these articles should be cut and the writer produced less content overall.

`nvidia-smi` output during a runtime load with 

```python
RESEARCHER_MODEL = "qwen3.5:9b"
WRITER_MODEL = "qwen3.5:9b"
EDITOR_MODEL = "qwen3.5:9b"
NUM_CTX = 32768
```
So the 9b actually fits OK on the NVIDIA RTX 2070S with 8GB VRAM. It is noticebly slower however.

```txt
Wed Mar  4 09:41:20 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 550.120                Driver Version: 550.120        CUDA Version: 12.4     |
|-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 2070 ...    Off |   00000000:03:00.0  On |                  N/A |
| 39%   52C    P2             87W /  215W |    7567MiB /   8192MiB |     37%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
                                                                                         
+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI        PID   Type   Process name                              GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A      1950      G   /usr/lib/xorg/Xorg                             94MiB |
|    0   N/A  N/A      2203      G   /usr/bin/gnome-shell                           57MiB |
|    0   N/A  N/A   3666360      C   /usr/local/bin/ollama                        7410MiB |
+-----------------------------------------------------------------------------------------+
```

Big improvement over the failed 4B run. Comparing to yesterday's 9B MacBook output:

- 9 articles curated and summarized (vs yesterday's 10)
- Clean markdown formatting with proper [Title](link) syntax, althought not exactly what I intended this might actually work better to have the source be the link?
- Story of the Day has real depth
- Good topic diversity: storage, agents, security, models, MLOps

Overall I would call that a success. Something funny is there is a story that was also in yesterdays generated report. I need to add a DB with some sort of memory on like the past week or maybe 30 days of stories so it doesn't go repeating itself. The editor could access that or maybe the curator actually .. get new stories only.