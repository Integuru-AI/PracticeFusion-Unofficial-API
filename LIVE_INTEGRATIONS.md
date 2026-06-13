# Practice Fusion Unofficial API

Unofficial Python integrations for Practice Fusion.

## Integrations

- `practice_fusion_list_patients.py` - `list_patients` (33 live events).
- `practice_fusion_list_patients_alt.py` - `list_patients_alt` (13 live events).

## Usage

Each file exposes a `run(input, context)` or `run(headers, input)` style entrypoint, matching the source integration runtime.
Authenticated request headers/cookies are expected to be supplied by the caller when required.

Install dependencies:

```bash
pip install -r requirements.txt
```

## Info

This unofficial API is built by [Integuru.ai](https://integuru.ai/).

For custom requests or hosted authentication, contact richard@taiki.online.

See the [complete list of APIs by Integuru](https://github.com/Integuru-AI/APIs-by-Integuru).
