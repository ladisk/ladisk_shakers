# ...existing code...
import os
import tomli
import shutil
import re
from pathlib import Path
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

def read_template(template_path):
    """Read HTML template from file"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Template file not found at {template_path}. "
            "Please ensure the template exists."
        )

def parse_toml_comments(toml_path):
    """Extract unit and description from TOML comments"""
    comments = {}
    try:
        with open(toml_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Match: key = value # [unit] description
                match = re.match(r'\s*(\w+)\s*=\s*(.+?)\s*#\s*(.+)', line)
                if match:
                    key = match.group(1)
                    comment = match.group(3).strip()
                    
                    # Parse unit and description
                    unit_match = re.match(r'\[(.+?)\]\s*(.*)', comment)
                    if unit_match:
                        unit = unit_match.group(1)
                        description = unit_match.group(2)
                    else:
                        unit = ''
                        description = comment
                    
                    comments[key] = {
                        'unit': unit,
                        'description': description
                    }
    except Exception as e:
        print(f"Warning: Could not parse comments from {toml_path}: {e}")
    
    return comments

def enrich_toml_data(data, comments, exclude_sections=None):
    """Add unit and description info from comments to TOML data"""
    if exclude_sections is None:
        exclude_sections = {'additional_checks'}
    
    for section_name in data:
        if section_name in exclude_sections:
            continue
        if isinstance(data[section_name], dict):
            for key in list(data[section_name].keys()):
                if key in comments:
                    # Wrap value with metadata
                    original_value = data[section_name][key]
                    data[section_name][key] = {
                        'value': original_value,
                        'unit': comments[key]['unit'],
                        'description': comments[key]['description']
                    }
    return data

def parse_check_formula(formula_str):
    """Parse additional check formula to extract expression and comparison
    
    Example: "axial_stiffness / 2 * (displacement_pk_pk - travel_required) / 9.81 > payload_mass"
    Returns: {
        'left': 'axial_stiffness / 2 * (displacement_pk_pk - travel_required) / 9.81',
        'operator': '>',
        'right': 'payload_mass',
        'full': 'axial_stiffness / 2 * (displacement_pk_pk - travel_required) / 9.81 > payload_mass'
    }
    """
    # Handle dict input (from enriched data)
    if isinstance(formula_str, dict):
        formula_str = formula_str.get('value', '')
    
    if not isinstance(formula_str, str):
        formula_str = str(formula_str)
    
    # Find comparison operators (longer first)
    operators = ['>=', '<=', '==', '!=', '>', '<']
    
    for op in operators:
        if op in formula_str:
            parts = formula_str.split(op, 1)
            if len(parts) == 2:
                return {
                    'left': parts[0].strip(),
                    'operator': op,
                    'right': parts[1].strip(),
                    'full': formula_str.strip()
                }
    
    # If no comparison found, treat whole thing as expression
    return {
        'left': formula_str.strip(),
        'operator': None,
        'right': None,
        'full': formula_str.strip()
    }

def process_toml_files(input_dir, output_dir, templates_dir):
    """Process all TOML files in input_dir and generate static HTML files in output_dir"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    templates_path = Path(templates_dir)
    
    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader(str(templates_path)), trim_blocks=True, lstrip_blocks=True)
    equipment_template = env.get_template('equipment.html')
    index_template = env.get_template('index.html')
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create images directory in output
    images_output_path = output_path / 'images'
    images_output_path.mkdir(exist_ok=True)
    
    # Create manuals directory in output
    manuals_output_path = output_path / 'manuals'
    manuals_output_path.mkdir(exist_ok=True)

    # Copy static files (logo, etc.)
    static_input_path = templates_path / 'static'
    static_output_path = output_path / 'static'
    if static_input_path.exists():
        if static_output_path.exists():
            shutil.rmtree(static_output_path)
        shutil.copytree(static_input_path, static_output_path)
        print(f"✓ Copied static files to {static_output_path}")

    # List to store equipment information for index
    equipment_list = []
    
    # Process each TOML file
    for toml_file in sorted(input_path.glob('*.toml')):
        try:
            # Read and parse TOML file
            with open(toml_file, 'rb') as f:
                raw_data = tomli.load(f)
            
            # Parse comments to extract units and descriptions
            comments = parse_toml_comments(toml_file)
            
            # Enrich data with unit and description info (exclude additional_checks so checks remain raw strings)
            data = enrich_toml_data(dict(raw_data), comments, exclude_sections={'additional_checks'})
            
            # Parse additional checks to extract formulas (keep as structured dict)
            additional_checks = {}
            if 'additional_checks' in raw_data:
                for check_name, formula in raw_data['additional_checks'].items():
                    parsed = parse_check_formula(formula)
                    # attach unit/description from parsed comments (if present)
                    parsed['unit'] = comments.get(check_name, {}).get('unit', '')
                    parsed['description'] = comments.get(check_name, {}).get('description', '')
                    additional_checks[check_name] = parsed
            
            # Ensure input_parameters are present as mapping (wrap simple declarations)
            if 'input_parameters' in raw_data and isinstance(raw_data['input_parameters'], dict):
                # For any input param that wasn't enriched (e.g. declared as string "float"), wrap it with metadata
                for key, val in raw_data['input_parameters'].items():
                    if key not in data.get('input_parameters', {}):
                        unit = comments.get(key, {}).get('unit', '')
                        desc = comments.get(key, {}).get('description', '')
                        if 'input_parameters' not in data:
                            data['input_parameters'] = {}
                        data['input_parameters'][key] = {
                            'value': val,
                            'unit': unit,
                            'description': desc
                        }
            
            # Extract equipment info
            shaker_info = data.get('shaker', {})
            manufacturer = shaker_info.get('manufacturer', 'Unknown')
            model = shaker_info.get('model', 'Unknown')
            nominal_force = shaker_info.get('nominal_force', 'N/A')
            title = f"{manufacturer} {model}"

            # Copy associated manuals if they exist
            manuals_input_path = input_path / 'manuals'
            if manuals_input_path.exists() and manuals_input_path.is_dir():
                if 'manual' in shaker_info:
                    manual = shaker_info['manual']
                    src = manuals_input_path / manual
                    if src.exists():
                        dst = manuals_output_path / manual
                        shutil.copy2(src, dst)
                        print(f"✓ Copied manual: {manual}")
            
            # Create HTML file name
            html_file = output_path / f"{toml_file.stem}.html"
            
            # We want additional_checks displayed immediately after input_parameters.
            # Pass both equipment_data and additional_checks, and tell template which section to inject after.
            html_content = equipment_template.render(
                title=title,
                equipment_data=data,
                additional_checks=additional_checks,
                additional_checks_inject_after='input_parameters'
            )
            
            # Write HTML file
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✓ Generated: {html_file.name}")
            
            # Copy associated images if they exist
            images_input_path = input_path / 'images'
            if images_input_path.exists():
                for section_data in data.values():
                    if isinstance(section_data, dict) and 'image' in section_data:
                        image = section_data['image']
                        # Copy image file to output images directory if it exists
                        src = images_input_path / image
                        if src.exists():
                            dst = images_output_path / image
                            dst.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src, dst)
                            print(f"  ✓ Copied image: {image}")
            
            # Store information for index
            equipment_list.append({
                'filename': f"{toml_file.stem}.html",
                'title': title,
                'manufacturer': manufacturer,
                'model': model,
                'nominal_force': f'{nominal_force["value"]} {nominal_force["unit"]}'
            })
            
        except Exception as e:
            print(f"✗ Error processing {toml_file.name}: {str(e)}")
    
    # Generate index.html
    if equipment_list:
        # Sort equipment list by manufacturer and model
        equipment_list.sort(key=lambda x: (x['manufacturer'], x['model']))
        
        # Render index template
        index_content = index_template.render(
            equipment_items=equipment_list,
            generated_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        index_path = output_path / 'index.html'
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        print(f"✓ Generated: index.html with {len(equipment_list)} entries")
    else:
        print("✗ No TOML files found to process")

if __name__ == "__main__":
    process_toml_files("input", "docs", "templates")
