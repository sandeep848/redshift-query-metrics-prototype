# Redshift Query Metrics Capacity Prototype

An **offline capacity-planning prototype** for exported Amazon Redshift query metrics. It is intentionally different from [redshift-streaming-analytics](https://github.com/sandeep848/redshift-streaming-analytics), which is a production-style Kafka ingestion and live dashboard system.

## Separate responsibility

| Repository | Responsibility |
|---|---|
| This prototype | Analyze one exported CSV and produce a capacity recommendation |
| `redshift-streaming-analytics` | Continuously ingest, store and visualize live metrics |

No AWS credentials, Kafka broker or Redshift connection is required here.

## Decision logic

The planner combines three normalized signals:

- 95th-percentile queue delay: 45%
- spill-event rate: 35%
- 95th-percentile concurrency: 20%

The resulting pressure score maps to a transparent recommendation. The thresholds are deliberately explicit so they can be reviewed and adjusted rather than hidden behind an LLM.

## Input schema

~~~text
queue_seconds
execution_seconds
spill_mb
scanned_mb
concurrency
~~~

## Run

~~~bash
git clone https://github.com/sandeep848/redshift-query-metrics-prototype.git
cd redshift-query-metrics-prototype
pip install pandas pytest
python capacity_planner.py workload.csv --output capacity_report.json
~~~

## Test

~~~bash
pytest
~~~

## Files

- `capacity_planner.py` — offline scoring CLI
- `tests/test_capacity_planner.py` — deterministic behavior tests
- `post-final.py` — earlier exploratory dashboard retained for project history

## Limitations

The thresholds are heuristic and must be calibrated against workload cost, service-level objectives and actual cluster behavior before operational use.
