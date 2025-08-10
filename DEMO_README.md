# CFG-Neuralese Demo Guide

Simple 3-act demo showing the evolution of communication protocols.

## 🎭 Demo Flow

1. **Act 1**: Generate best artifacts (run before talk)
2. **Act 2**: Show evolution process on stage
3. **Act 3**: Demonstrate evolved language with audience guessing

## 🚀 Usage

### Act 1: Generate Best Artifacts

```bash
python scripts/offline_optimize.py
```

- Runs **10 rounds** of evolution (thorough optimization)
- Uses batch size of **100** for better evaluation
- Automatically finds the most recent run directory
- Saves best grammar to `artifacts/best/grammar.lark`
- Saves few-shots to `artifacts/best/fewshots.json`
- Collects **3 few-shot examples** from the evolved grammar

**Note**: The script checks if best artifacts already exist and will skip regeneration unless you delete `artifacts/best/` first.

### Act 2: Live Evolution Demo

```bash
python scripts/live_process.py
```

- Shows 3 rounds of evolution on stage
- Loads your best grammar as starting point
- Saves results to `artifacts/runs/live_<timestamp>/`

### Act 3: Language Demonstration

```bash
python test_step3.py
```

- Loads evolved grammar and few-shots
- Generates random scenes for audience guessing
- Shows Speaker→Listener communication

## 🎯 Demo Day

**Before talk**: Run Act 1 (takes ~10-15 minutes)
**On stage**: Run Act 2, then Act 3

## 📁 What Gets Created

```
artifacts/
├── best/                    # Best artifacts for demo
│   ├── grammar.lark        # Evolved grammar
│   └── fewshots.json       # Few-shot examples (3 examples)
└── runs/                    # Run logs
    ├── run_YYYYMMDD_HHMM/  # Offline optimization (10 rounds)
    └── live_TIMESTAMP/     # Live demo results
```

## ⚡ Quick Start

1. **Generate artifacts**: `python scripts/offline_optimize.py`
2. **Wait for completion** (~10-15 minutes)
3. **Demo ready!** Best grammar and few-shots are saved

The offline script automatically handles the evolution, finds the best grammar, and prepares everything needed for the live demo. 🎭✨
