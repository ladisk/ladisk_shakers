Source repository for the [LADISK Small Shakers github pages site](https://ladisk.github.io/ladisk_shakers/).

# LADISK Small Shakers

The website is built automatically when pushing to the `main` branch, and published using GitHub Pages.

# Static Site Generator Documentation

## Overview

This Python script generates a static website from TOML configuration files, creating individual shaker pages and an index page. It uses Jinja2 templates for HTML generation and includes support for images, manuals, and enriched metadata.

## Directory Structure

```
.
├── input/
│   ├── *.toml           # Equipment configuration files
│   ├── images/          # Equipment images
│   └── manuals/         # PDF manuals
├── templates/
│   ├── equipment.html   # Individual equipment page template
│   ├── index.html       # Index page template
│   └── static/          # CSS, logos, etc.
└── docs/                # Generated output (created automatically)
    ├── index.html
    ├── *.html
    ├── images/
    ├── manuals/
    └── static/
```

## Running the Script

```bash
python generate_docs.py
```

The script processes all `.toml` files in the `input/` directory and generates HTML files in the `docs/` directory.

## Creating TOML Files

### Basic Structure

```toml
[shaker]
manufacturer = "Acme"
model = "Model 100"
nominal_force = 1000  # [N] Maximum force output
manual = "acme_model100.pdf"  # Optional
image = "acme_100.jpg"        # Optional

[input_parameters]
payload_mass = "float"  # [kg] Mass of test payload
frequency = "float"     # [Hz] Test frequency

[additional_checks]
force_margin = "nominal_force * 0.8 > payload_mass * 9.81"  # [N] Safety margin check
[limits]
force_sine = 8.9 # [N] Sine force limit

[performance]
frequency_range = [5.0, 12000.0] # [Hz] Frequency range (useful)

[dimensions]
shaker_mass = 0.91 # [kg] Shaker mass
```

### Comment Syntax

Add units and descriptions using inline comments:

```toml
parameter = value  # [unit] Description text
```

- **Unit**: Enclosed in square brackets `[unit]`
- **Description**: Text following the unit

### Sections

- **`[shaker]`**: Equipment metadata (manufacturer, model, force, manual, image)
- **`[input_parameters]`**: User-configurable values (use `"float"` or `"string"` as placeholder)
- **`[additional_checks]`**: Formula-based validation checks (use comparison operators: `>`, `<`, `>=`, `<=`, `==`, `!=`)
- **Custom sections**: Any other sections are displayed as equipment specifications. Most common sections include `[limits]`, `[performance]`, and `[dimensions]`.

## Adding Images

1. Place image files in `input/images/`
2. Reference in TOML `[shaker]` section: `image = "filename.jpg"`
3. Images are automatically copied to `docs/images/`

## Adding Manuals

1. Place PDF files in `input/manuals/`
2. Reference in TOML `[shaker]` section: `manual = "filename.pdf"`
3. Manuals are automatically copied to `docs/manuals/`

## Input Parameters
Define user input parameters in the `[input_parameters]` section:

```toml
[input_parameters]
payload_mass = "float"  # [kg] Mass of the test payload
travel_required = "float"  # [mm] Desired travel
```

## Additional Checks Formula Syntax

Additional checks support mathematical expressions and comparison operators and can include parameters defined in `[input_parameters]` as well as all other normal toml sections

```toml
[additional_checks]
# Simple comparison
max_load = "payload_mass < 100"  # [kg] Maximum payload

# Complex expression
force_check = "axial_stiffness / 2 * (displacement_pk_pk - travel_required) / 9.81 > payload_mass"

# Multiple operators supported: > < >= <= == !=
```

## Output

- **Individual pages**: `docs/equipment-name.html`
- **Index page**: `docs/index.html` (auto-generated list of all equipment)
- **Assets**: Copied to `docs/images/`, `docs/manuals/`, `docs/static/`

## Example TOML File

```toml
[shaker]
manufacturer = "VibeTech"
model = "VT-5000"
nominal_force = 5000  # [N] Peak sine force
manual = "vibetech_vt5000.pdf"
image = "vt5000.jpg"

[specifications]
frequency_range = "5-3000"  # [Hz] Operating frequency range
max_displacement = 51  # [mm] Peak-to-peak displacement
max_acceleration = 100  # [g] Peak acceleration
weight = 145  # [kg] Shaker weight

[input_parameters]
payload_mass = "float"  # [kg] Test specimen mass
test_frequency = "float"  # [Hz] Desired test frequency
required_acceleration = "float"  # [g] Target acceleration level

[additional_checks]
payload_limit = "payload_mass <= 50"  # [kg] Maximum recommended payload
frequency_valid = "test_frequency >= 5 and test_frequency <= 3000"  # [Hz] Frequency within range
force_adequate = "nominal_force * 0.9 > payload_mass * required_acceleration * 9.81"  # [N] Force margin check
```

## Notes


- All TOML files in `input/` are processed automatically when the script runs
- The script is run automatically and the site is rebuilt on each push to the `main` branch.
- The script will print status messages for each file processed and any errors encountered
- Generated timestamp is added to the index page automatically

## Dependencies

Required Python packages are listed in `requirements.txt`. Install them using pip:
```bash
pip install -r requirements.txt
```
