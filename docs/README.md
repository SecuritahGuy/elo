# SportsEdge - NFL Elo Rating System

A comprehensive NFL Elo rating system with advanced features, backtesting capabilities, and extensible architecture.

## 🏗️ Architecture

```
sports-edge/
├── ingest/
│   └── nfl/
│       ├── data_loader.py      # NFL data ingestion
│       └── idmaps.py           # Team ID mapping utilities
├── models/
│   └── nfl_elo/
│       ├── config.py           # Typed configuration system
│       ├── ratings.py          # Core Elo rating classes
│       ├── updater.py          # Game update logic
│       ├── features.py         # Feature hooks for extensions
│       ├── evaluator.py        # Evaluation metrics
│       ├── backtest.py         # Walk-forward backtesting
│       ├── cli.py              # Command-line interface
│       └── constants.py        # System constants
├── notebooks/
│   └── nfl_elo_experiments.ipynb  # Example experiments
├── configs/                    # Configuration files
├── artifacts/                  # Output directory
├── tests/                      # Test suite
└── pyproject.toml             # Dependencies and project config
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd SportsEdge

# Install dependencies
poetry install

# Or with pip
pip install -e .
```

### Basic Usage

```bash
# Run a backtest with default settings
python -m models.nfl_elo.cli backtest --start 2020 --end 2024

# Run with custom configuration
python -m models.nfl_elo.cli backtest --config-path configs/default.json

# Compare multiple configurations
python -m models.nfl_elo.cli compare --config-dir configs

# Validate data quality
python -m models.nfl_elo.cli validate-data --start 2020 --end 2024

# Analyze results
python -m models.nfl_elo.cli analyze --history-file artifacts/nfl_elo_history.parquet
```

### Python API

```python
from ingest.nfl.data_loader import load_games
from models.nfl_elo.config import EloConfig
from models.nfl_elo.backtest import run_backtest

# Load data
games = load_games([2020, 2021, 2022, 2023, 2024])

# Create configuration
config = EloConfig(
    k=20.0,
    hfa_points=55.0,
    mov_enabled=True
)

# Run backtest
results = run_backtest(games, config)

# Access results
print(f"Brier Score: {results['metrics']['brier_score']:.4f}")
print(f"Log Loss: {results['metrics']['log_loss']:.4f}")
```

## 📊 Features

### Core Elo System
- **Standard Elo ratings** with configurable K-factor
- **Margin of Victory (MOV) multiplier** (FiveThirtyEight style)
- **Home Field Advantage (HFA)** adjustment
- **Preseason regression** to prevent rating drift
- **Safety rails** to limit extreme rating changes

### Advanced Features
- **Offense/Defense splits** (optional)
- **Feature hooks** for QB adjustments, rest days, weather, etc.
- **Walk-forward backtesting** with proper temporal ordering
- **Comprehensive evaluation metrics** (Brier score, log loss, calibration)
- **Configuration management** with Pydantic validation

### Data Integration
- **nfl-data-py integration** for schedules and results
- **Data validation** and quality checks
- **Team ID mapping** and normalization
- **Support for historical data** (2010-present)

## 🔧 Configuration

The system uses Pydantic for typed configuration management:

```python
class EloConfig(BaseModel):
    # Core parameters
    base_rating: float = 1500.0
    k: float = 20.0
    scale: float = 400.0
    hfa_points: float = 55.0
    preseason_regress: float = 0.75
    
    # MOV settings
    mov_enabled: bool = True
    mov_mult_a: float = 2.2
    mov_mult_b: float = 0.001
    
    # Safety rails
    max_rating_shift_per_game: float = 80.0
    
    # Offense/Defense split (optional)
    use_offdef_split: bool = False
    k_off: float = 12.0
    k_def: float = 12.0
```

## 📈 Evaluation Metrics

The system provides comprehensive evaluation metrics:

- **Brier Score**: Probability calibration (lower is better)
- **Log Loss**: Probability accuracy (lower is better)
- **Expected Calibration Error (ECE)**: Calibration quality
- **Sharpness**: Prediction variance
- **Accuracy**: Binary prediction accuracy
- **Calibration plots**: Visual calibration assessment

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=models/nfl_elo

# Run specific test file
poetry run pytest tests/test_elo_core.py
```

## 📓 Notebooks

The `notebooks/` directory contains example experiments:

- **nfl_elo_experiments.ipynb**: Comprehensive analysis and visualization
- Data exploration and validation
- Configuration comparison
- Rating trajectory analysis
- Performance visualization

## 🔌 Extension Points

The system is designed for easy extension:

### Feature Hooks
```python
def qb_delta_stub(row: pd.Series) -> float:
    # Implement QB adjustment logic
    return 0.0

def weather_adjustment(game_id: str, temperature: float) -> float:
    # Implement weather adjustment
    return 0.0
```

### Custom Configurations
```python
# High volatility configuration
high_k_config = EloConfig(k=30.0, max_rating_shift_per_game=100.0)

# Conservative configuration
conservative_config = EloConfig(k=15.0, hfa_points=40.0)
```

## 📊 Example Results

Typical performance metrics on 2020-2024 data:

- **Brier Score**: ~0.24-0.26
- **Log Loss**: ~0.65-0.70
- **ECE**: ~0.02-0.04
- **Accuracy**: ~65-70%

## 🛠️ Development

### Code Style
- **Black** for code formatting
- **isort** for import sorting
- **mypy** for type checking
- **pytest** for testing

### Adding New Features
1. Create feature hook in `features.py`
2. Add configuration parameters in `config.py`
3. Integrate into `updater.py` or `backtest.py`
4. Add tests in `tests/`
5. Update documentation

## 📚 References

- [FiveThirtyEight NFL Elo](https://fivethirtyeight.com/features/introducing-nfl-elo-ratings/)
- [nfl-data-py](https://github.com/nflverse/nfl_data_py)
- [Elo Rating System](https://en.wikipedia.org/wiki/Elo_rating_system)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions or issues:
1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed description
4. Include example code and error messages

---

**Note**: This is a research and educational project. Use at your own risk for any betting or financial applications.
