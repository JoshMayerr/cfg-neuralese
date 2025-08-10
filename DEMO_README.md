# CFG-Neuralese Demo System

This demo system implements the three-act structure outlined in `DEMO.md` to showcase the evolution of communication protocols.

## 🎭 Demo Structure

**Act 1: Offline Optimization** - Run a longer optimization to generate the best grammar and few-shots
**Act 2: Live Process** - Show the evolutionary process on stage with verbose logging
**Act 3: Use Saved Language** - Demonstrate the evolved language with audience guessing

## 🚀 Quick Start

### 1. Run the Complete Demo

```bash
python scripts/demo.py --all
```

### 2. Run Individual Acts

```bash
# Act 1: Generate best artifacts (run this first)
python scripts/demo.py --act 1

# Act 2: Show live evolution process
python scripts/demo.py --act 2

# Act 3: Demonstrate evolved language
python scripts/demo.py --act 3
```

### 3. Interactive Mode

```bash
python scripts/demo.py
```

## 📁 Artifact Structure

After running Act 1, you'll have:

```
artifacts/
  best/
    grammar.lark          # Final evolved grammar
    fewshots.json         # Speaker/listener few-shots
  runs/
    live_TIMESTAMP/       # Live demo results
      round_log.csv       # Per-round metrics
      grammars/           # Grammar versions per round
```

## 🔧 Manual Commands

### Offline Optimization

```bash
python scripts/offline_optimize.py
```

### Live Process Demo

```bash
python scripts/live_process.py
```

### Use Saved Language

```bash
python src/run/use_language.py
```

## 📊 Demo Flow

1. **Before the talk**: Run `python scripts/demo.py --act 1` to generate best artifacts
2. **On stage**: Run `python scripts/demo.py --act 2` to show evolution process
3. **Audience interaction**: Run `python scripts/demo.py --act 3` for guessing game

## 🎯 Key Features

- **Verbose logging** for live demonstrations
- **Artifact management** for saving/loading best results
- **Few-shot examples** for consistent language behavior
- **Audience interaction** with scene generation and guessing
- **Modular design** for running individual components

## 🐛 Troubleshooting

- **Missing artifacts**: Run Act 1 first to generate required files
- **Import errors**: Make sure you're in the project root directory
- **API issues**: Check your OpenAI API key configuration

## 📝 Notes

- Keep few-shots small (2-3 examples) for consistent behavior
- The evolved grammar should be stable and compact
- Test the saved language before the demo to ensure consistency
