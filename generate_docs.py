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

def enrich_toml_data(data, comments):
    """Add unit and description info from comments to TOML data"""
    for section_name in data:
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

def process_toml_files(input_dir, output_dir, templates_dir):
    """Process all TOML files in input_dir and generate static HTML files in output_dir"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    templates_path = Path(templates_dir)
    
    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader(str(templates_path)))
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
                data = tomli.load(f)
            
            # Parse comments to extract units and descriptions
            comments = parse_toml_comments(toml_file)
            
            # Enrich data with unit and description info
            data = enrich_toml_data(data, comments)
            
            # Extract equipment info
            shaker_info = data.get('shaker', {})
            manufacturer = shaker_info.get('manufacturer', 'Unknown')
            model = shaker_info.get('model', 'Unknown')
            title = f"{manufacturer} {model}"

            # Copy associated manuals if they exist
            manuals_input_path = input_path / 'manuals'
            if manuals_input_path.exists():
                if 'manual' in shaker_info:
                    manual = shaker_info['manual']
                    src = manuals_input_path / manual
                    if src.exists():
                        dst = manuals_output_path / manual
                        shutil.copy2(src, dst)
                        print(f"✓ Copied manual: {manual}")
            
            # Create HTML file name
            html_file = output_path / f"{toml_file.stem}.html"
            
            # Render template with data
            html_content = equipment_template.render(
                title=title,
                equipment_data=data
            )
            
            # Write HTML file
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✓ Generated: {html_file.name}")
            
            # Copy associated images if they exist
            images_input_path = input_path / 'images'
            if images_input_path.exists():
                for section_data in data.values():
                    if isinstance(section_data, dict) and 'images' in section_data:
                        images = section_data['images']
                        if isinstance(images, str):
                            images = [images]
                        elif isinstance(images, dict):
                            images = [images['path']]
                        elif isinstance(images, list):
                            images = [img['path'] if isinstance(img, dict) else img for img in images]
                        
                        for image in images:
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
                'model': model
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