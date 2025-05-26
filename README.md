# Codebase for Bachelor Thesis: **Design of Hollow Section Joints: Comparison of Design Methods**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![MySQL 8.0+](https://img.shields.io/badge/MySQL-8.0%2B-orange)](https://www.mysql.com/)

## Version: 0.1

## Purpose
This repository contains the codebase developed for my bachelor thesis **"Design of Hollow Section Joints: Comparison of Design Methods"** at Brno University of Technology. The project implements a computational workflow for comparing different design standards (AISC, EN, and Fpr_EN) for hollow section joints using Component-Based Finite Element Method (CBFEM) analysis.

---

## Codebase Structure

```plaintext
bachelor_thesis_doi/
├── Code_Config_yaml/          # Design standard configurations
│   ├── AISC/                  # American Institute of Steel Construction
│   │   ├── CHS_K.yaml
│   │   ├── CHS_T_and_Y.yaml
│   │   └── CHS_X.yaml
│   ├── EN/                    # Eurocode configurations
│   │   ├── CHS_K.yaml
│   │   ├── CHS_T_and_Y.yaml
│   │   └── CHS_X.yaml
│   └── Fpr_EN/                # Draft Eurocode configurations
│       ├── CHS_K.yaml
│       ├── CHS_T_and_Y.yaml
│       └── CHS_X.yaml
├── csv_cross_section/         # Cross-section databases
│   ├── Circular_hollow_CHS(cf).csv
│   ├── Circular_hollow_CHS.csv
│   ├── Rectangular_hollow_RHS.csv
│   └── Rectangular_hollow_SHS.csv
├── idea_model/                # IDEA StatiCa connection models
│   ├── chs_k.ideaCon
│   ├── chs_x.ideaCon
│   └── chs_y.ideaCon
├── src/                       # Source code
│   ├── calc/                  # Calculation modules
│   │   ├── gen_sample_helper/
│   │   ├── base_classes.py
│   │   ├── generate_samples.py
│   │   ├── idea_calculator.py
│   │   └── idea_load_generator.py
│   ├── e/                     # Evaluation scripts
│   │   ├── eval_code_to_code.py
│   │   ├── eval_linear_regression.py
│   │   ├── eval_multiple_plots.py
│   │   ├── eval_res_code_runner.py
│   │   └── eval_res_to_diff_code.py
│   └── u/                     # Utility modules
│       ├── utils_data_import.py
│       ├── utils_idea_calculator.py
│       ├── utils_plastic_strain_investigation.py
│       └── utils_data_plotting.py
├── .gitignore
├── LICENSE
├── db_schema.sql              # MySQL database schema
└── requirements.txt           # Python dependencies