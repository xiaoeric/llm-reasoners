#!/usr/bin/bash
CUDA_VISIBLE_DEVICES=0,1 python examples/tot_game24/inference.py --model /data/haotian/RAP_tune/Llama-2-13B-GPTQ
