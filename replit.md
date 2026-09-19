# TrafficAI on Replit

## Scheduled jobs

The `TrafficAI scheduler` workflow runs:

- `python scripts/run_update.py` every 30 minutes
- `python scripts/predict_traffic.py` every 2 minutes

Start the scheduler manually with:

```bash
python scripts/run_scheduler.py
```

The data update requires the `HERE_API_KEY` secret for HERE traffic data.
Open-Meteo weather data does not require a key.

The prediction job requires the six trained model files referenced by
`scripts/predict_traffic.py` in the `ml/` directory. These files are not
included in the imported repository.