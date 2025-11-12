#!/usr/bin/env python3

import pandas as pd
import csv

def export_high_confidence_matches(
    matched_file='matched_variables_validated.csv',
    motec_file='fb24MotecSmaller.csv',
    carsim_file='oct14CarsimSmaller.csv',
    output_file='high_confidence_data_export.csv',
    confidence_threshold=0.9
):
    """
    Export actual data for matched variables with high confidence scores.
    Only exports the first Motec variable when multiple Motec vars match to the same CarSim var.
    Output format: Two-row header (Motec name, then CarSim name), then data.
    
    Args:
        matched_file: Path to the matched variables CSV
        motec_file: Path to original Motec telemetry CSV
        carsim_file: Path to original CarSim sensor CSV
        output_file: Path for the output CSV file
        confidence_threshold: Minimum confidence score (default 0.9)
    """
    
    print("=" * 70)
    print("HIGH CONFIDENCE DATA EXPORTER")
    print("=" * 70)
    print()
    
    # Step 1: Load matched variables
    print(f"Loading matched variables from: {matched_file}")
    matches_df = pd.read_csv(matched_file)
    print(f"✓ Loaded {len(matches_df)} total matches")
    print()
    
    # Step 2: Filter by confidence threshold
    print(f"Filtering for confidence >= {confidence_threshold}")
    high_conf_matches = matches_df[matches_df['Confidence'] >= confidence_threshold]
    print(f"✓ Found {len(high_conf_matches)} high-confidence matches")
    print()
    
    if high_conf_matches.empty:
        print("No matches meet the confidence threshold!")
        return
    
    # Sort by confidence (highest first) to prioritize best matches
    high_conf_matches = high_conf_matches.sort_values('Confidence', ascending=False)
    
    # Step 2.5: Remove duplicate CarSim variables (keep only first/best match)
    print("Removing duplicate CarSim outputs (keeping only first Motec input per CarSim output)...")
    
    # Track which CarSim variables we've already seen
    seen_carsim = set()
    skipped_matches = []
    unique_matches = []
    
    for idx, row in high_conf_matches.iterrows():
        carsim_var = row['CarSim_Variable']
        
        if carsim_var in seen_carsim:
            # Skip this match - we already have data for this CarSim variable
            skipped_matches.append({
                'Motec_Variable': row['Motec_Variable'],
                'CarSim_Variable': carsim_var,
                'Confidence': row['Confidence'],
                'Reason': 'Duplicate CarSim output'
            })
        else:
            # First time seeing this CarSim variable - keep it
            seen_carsim.add(carsim_var)
            unique_matches.append(row)
    
    # Convert back to DataFrame
    high_conf_matches = pd.DataFrame(unique_matches)
    
    print(f"✓ Kept {len(high_conf_matches)} unique matches")
    print(f"✓ Skipped {len(skipped_matches)} duplicate CarSim outputs")
    print()
    
    if skipped_matches:
        print("Skipped matches (duplicates):")
        for skip in skipped_matches[:10]:  # Show first 10
            print(f"  ✗ {skip['Motec_Variable']} → {skip['CarSim_Variable']} "
                  f"(Conf: {skip['Confidence']:.2f}) - {skip['Reason']}")
        if len(skipped_matches) > 10:
            print(f"  ... and {len(skipped_matches) - 10} more")
        print()
    
    # Step 3: Load original data files
    print(f"Loading Motec data from: {motec_file}")
    motec_df = pd.read_csv(motec_file, header=14)  # Row 15 (0-indexed = 14)
    print(f"✓ Loaded Motec data: {len(motec_df)} rows, {len(motec_df.columns)} columns")
    print()
    
    print(f"Loading CarSim data from: {carsim_file}")
    carsim_df = pd.read_csv(carsim_file, header=0)  # Row 1 (0-indexed = 0)
    print(f"✓ Loaded CarSim data: {len(carsim_df)} rows, {len(carsim_df.columns)} columns")
    print()
    
    # Step 4: Extract matched columns
    print("Extracting matched columns...")
    
    # Prepare output dataframe with CarSim data
    output_data = pd.DataFrame()
    
    # Track Motec and CarSim variable names for the two-row header
    motec_header = []
    carsim_header = []
    
    missing_carsim = []
    
    for idx, row in high_conf_matches.iterrows():
        motec_var = row['Motec_Variable']
        carsim_var = row['CarSim_Variable']
        
        # Extract CarSim data
        if carsim_var in carsim_df.columns:
            # Use temporary column names for now
            col_name = f"col_{len(output_data.columns)}"
            output_data[col_name] = carsim_df[carsim_var]
            
            # Store the actual names for headers
            motec_header.append(motec_var)
            carsim_header.append(carsim_var)
        else:
            missing_carsim.append(carsim_var)
    
    print(f"✓ Extracted {len(output_data.columns)} columns")
    
    if missing_carsim:
        print(f"⚠ Warning: {len(missing_carsim)} CarSim variables not found in data")
    print()
    
    # Step 5: Save to CSV with two-row header
    print(f"Saving to: {output_file}")
    
    # Create metadata header
    metadata_lines = [
        f"# High Confidence Variable Matches (Confidence >= {confidence_threshold})",
        f"# Unique Matches Exported: {len(high_conf_matches)}",
        f"# Duplicate Matches Skipped: {len(skipped_matches)}",
        f"# Motec Data Rows: {len(motec_df)}",
        f"# CarSim Data Rows: {len(carsim_df)}",
        "#",
        "# Format: Row 1 = Motec variable names, Row 2 = CarSim variable names, Rows 3+ = Data",
        "# Note: When multiple Motec variables matched the same CarSim variable,",
        "# only the first (highest confidence) Motec variable was exported.",
        "#",
        "# Exported Match Details:"
    ]
    
    # Add match details to metadata
    for idx, row in high_conf_matches.iterrows():
        metadata_lines.append(
            f"# {row['Motec_Variable']} → {row['CarSim_Variable']} "
            f"(Conf: {row['Confidence']:.2f}, Type: {row['Match_Type']})"
        )
    
    if skipped_matches:
        metadata_lines.append("#")
        metadata_lines.append("# Skipped Matches (Duplicate CarSim Outputs):")
        for skip in skipped_matches:
            metadata_lines.append(
                f"# SKIPPED: {skip['Motec_Variable']} → {skip['CarSim_Variable']} "
                f"(Conf: {skip['Confidence']:.2f})"
            )
    
    metadata_lines.append("#")
    
    # Write to file with custom two-row header
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        # Write metadata
        for line in metadata_lines:
            f.write(line + '\n')
        
        # Write first header row (Motec variable names)
        writer.writerow(motec_header)
        
        # Write second header row (CarSim variable names)
        writer.writerow(carsim_header)
        
        # Write data rows
        for _, row in output_data.iterrows():
            writer.writerow(row.values)
    
    print(f"✓ Data exported successfully!")
    print()
    
    # Step 6: Save skipped matches to separate file for reference
    if skipped_matches:
        skipped_file = output_file.replace('.csv', '_skipped.csv')
        skipped_df = pd.DataFrame(skipped_matches)
        skipped_df.to_csv(skipped_file, index=False)
        print(f"✓ Skipped matches saved to: {skipped_file}")
        print()
    
    # Step 7: Generate summary report
    print("=" * 70)
    print("EXPORT SUMMARY")
    print("=" * 70)
    print()
    print(f"Total high-confidence matches found: {len(high_conf_matches) + len(skipped_matches)}")
    print(f"Unique matches exported: {len(high_conf_matches)}")
    print(f"Duplicate matches skipped: {len(skipped_matches)}")
    print(f"Total columns in output: {len(output_data.columns)}")
    print(f"Data rows exported: {len(output_data)}")
    print()
    
    # Confidence distribution
    print("Confidence Distribution (Exported):")
    conf_1_0 = len(high_conf_matches[high_conf_matches['Confidence'] == 1.0])
    conf_0_95 = len(high_conf_matches[(high_conf_matches['Confidence'] >= 0.95) & 
                                       (high_conf_matches['Confidence'] < 1.0)])
    conf_0_90 = len(high_conf_matches[(high_conf_matches['Confidence'] >= 0.90) & 
                                       (high_conf_matches['Confidence'] < 0.95)])
    
    print(f"  1.00: {conf_1_0} matches")
    print(f"  0.95-0.99: {conf_0_95} matches")
    print(f"  0.90-0.94: {conf_0_90} matches")
    print()
    
    # Match type distribution
    print("Match Type Distribution (Exported):")
    for match_type, count in high_conf_matches['Match_Type'].value_counts().items():
        print(f"  {match_type}: {count} matches")
    print()
    
    # Sample of exported structure
    print("Sample of exported structure:")
    print("-" * 70)
    print("Row 1 (Motec):  ", end="")
    print(" | ".join(motec_header[:5]))
    print("Row 2 (CarSim): ", end="")
    print(" | ".join(carsim_header[:5]))
    print("Row 3 (Data):   ", end="")
    if len(output_data) > 0:
        print(" | ".join([str(v) for v in output_data.iloc[0, :5].values]))
    print()
    
    if len(high_conf_matches) > 5:
        print(f"... and {len(high_conf_matches) - 5} more columns")
    print()
    
    print("=" * 70)
    print("EXPORT COMPLETE")
    print("=" * 70)
    

def main():
    """Main execution function."""
    
    # You can adjust the confidence threshold here
    export_high_confidence_matches(
        matched_file='matched_variables_validated.csv',
        motec_file='fb24Motec.csv',
        carsim_file='oct14Carsim.csv',
        output_file='high_confidence_data_export.csv',
        confidence_threshold=0.9
    )
    
    # Optional: create separate exports for different confidence levels
    # Uncomment the lines below if you want additional files:
    
    # export_high_confidence_matches(
    #     output_file='perfect_confidence_data_export.csv',
    #     confidence_threshold=1.0
    # )
    
    # export_high_confidence_matches(
    #     output_file='very_high_confidence_data_export.csv',
    #     confidence_threshold=0.95
    # )


if __name__ == "__main__":
    main()