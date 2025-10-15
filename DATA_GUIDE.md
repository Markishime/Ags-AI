## Data Inputs (where to put your files)

You can start with the examples already in the `json/` folder or upload your own.

### What the app expects
For each parameter (e.g., “Available P (mg/kg)”), the app needs an average value. If you provide multiple samples, the engine computes the average for you.

Typical shape inside the app:
```
{
  "parameter_statistics": {
    "Available P (mg/kg)": {"average": 2.3},
    "Exch. K (meq/100 g)": {"average": 0.101}
  }
}
```

The app maps common names (e.g., “Avail P (mg/kg)” and “Available P (mg/kg)”) to the correct parameter so your tables are accurate.

### Tips
- If a parameter is missing, it will simply not show up or be marked N/A in some tables
- Use consistent units (mg/kg for Boron, %, meq/100 g) as shown in the sample files
- For quick testing, upload the provided sample JSONs in `json/`

