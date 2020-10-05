#!/bin/bash
# sampleにいる事前提
PYTHONPATH=src;$PYTHONPATH
cd sample
python monitoring_very_simple.py
cp -f fig_sample/test_mermaid.mmd fig_gen