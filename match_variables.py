#!/usr/bin/env python3
"""
match_variables.py
Intelligently matches variables between Motec telemetry and Carsim sensor data
using a dictionary for semantic mapping.

Usage: python match_variables.py
"""

import pandas as pd
import re
from difflib import SequenceMatcher
import sys

def remove_whitespace(text):
    """Remove all whitespace from text"""
    return re.sub(r'\s+', '', str(text))

def normalize_text(text):
    """Normalize text: lowercase and remove special characters"""
    return re.sub(r'[^a-z0-9]', '', str(text).lower())

def extract_tokens(text):
    """Extract meaningful tokens from text, filtering stopwords"""
    # Remove units in parentheses
    text = re.sub(r'\([^)]*\)', '', str(text))
    text = normalize_text(text)
    
    # Split into words
    tokens = re.findall(r'\w+', text)
    
    # Filter stopwords
    stopwords = {'the', 'of', 'for', 'at', 'in', 'on', 'to', 'a', 'an', 'and'}
    tokens = [t for t in tokens if t not in stopwords]
    
    return tokens

def token_similarity(text1, text2):
    """Calculate token-based similarity score between two texts"""
    tokens1 = set(extract_tokens(text1))
    tokens2 = set(extract_tokens(text2))
    
    if not tokens1 or not tokens2:
        return 0.0
    
    # Jaccard similarity
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    
    return intersection / union if union > 0 else 0.0

def sequence_similarity(text1, text2):
    """Calculate sequence similarity using SequenceMatcher"""
    return SequenceMatcher(None, normalize_text(text1), normalize_text(text2)).ratio()

def load_dictionary(filepath='dictionary.csv'):
    """Load dictionary mapping from CSV"""
    print("=== LOADING DICTIONARY ===")
    try:
        dict_df = pd.read_csv(filepath)
        
        # Column A = shorthand, Column B = longhand
        dict_df['shorthand_clean'] = dict_df.iloc[:, 0].apply(remove_whitespace)
        dict_df['longhand_clean'] = dict_df.iloc[:, 1].apply(remove_whitespace)
        
        # Create mapping dictionary
        short_to_long = dict(zip(dict_df['shorthand_clean'], dict_df['longhand_clean']))
        
        print(f"Dictionary loaded: {len(short_to_long)} entries")
        print("Column A (shorthand) → Column B (longhand)\n")
        
        return short_to_long, dict_df
    except Exception as e:
        print(f"Error loading dictionary: {e}")
        sys.exit(1)

def load_telemetry_data(filepath='fb24MotecSmaller.csv'):
    """Load Motec telemetry data (headers in row 15)"""
    print("=== LOADING TELEMETRY DATA (MOTEC) ===")
    try:
        # Read row 15 as headers (0-indexed, so row 14)
        df = pd.read_csv(filepath, header=14, nrows=0)
        headers_raw = df.columns.tolist()
        headers_clean = [remove_whitespace(h) for h in headers_raw]
        
        print(f"Telemetry variables: {len(headers_raw)}\n")
        return headers_raw, headers_clean
    except Exception as e:
        print(f"Error loading telemetry data: {e}")
        sys.exit(1)

def load_sensor_data(filepath='oct14CarsimSmaller.csv'):
    """Load Carsim sensor data (headers in row 1)"""
    print("=== LOADING SENSOR DATA (CARSIM) ===")
    try:
        df = pd.read_csv(filepath, nrows=0)
        headers_raw = df.columns.tolist()
        headers_clean = [remove_whitespace(h) for h in headers_raw]
        
        print(f"Sensor variables: {len(headers_raw)}\n")
        return headers_raw, headers_clean
    except Exception as e:
        print(f"Error loading sensor data: {e}")
        sys.exit(1)

def pass1_exact_matches(telem_raw, telem_clean, sensor_raw, sensor_clean):
    """Pass 1: Find exact variable name matches"""
    print("=== PASS 1: EXACT VARIABLE NAME MATCHES ===")
    matches = []
    
    for i, t_clean in enumerate(telem_clean):
        for j, s_clean in enumerate(sensor_clean):
            if t_clean.lower() == s_clean.lower():
                matches.append({
                    'Telemetry_Variable': telem_raw[i],
                    'Sensor_Variable': sensor_raw[j],
                    'MatchType': 'Exact',
                    'Confidence': 1.0,
                    'Description': 'Identical variable names'
                })
    
    print(f"Found {len(matches)} exact variable name matches\n")
    return matches

def pass2_dictionary_matches(telem_raw, telem_clean, sensor_raw, sensor_clean, 
                             short_to_long, matched_telem, matched_sensor):
    """Pass 2: Dictionary-based matching"""
    print("=== PASS 2: DICTIONARY-BASED MATCHING ===")
    matches = []
    
    for i, t_var in enumerate(telem_clean):
        t_var_raw = telem_raw[i]
        
        # Skip if already matched
        if t_var_raw in matched_telem:
            continue
        
        # Get longhand for telemetry variable
        if t_var in short_to_long:
            t_longhand = short_to_long[t_var]
        else:
            # Try to find semantic match in dictionary
            best_score = 0
            t_longhand = t_var
            for longhand in short_to_long.values():
                score = token_similarity(t_var, longhand)
                if score > best_score and score > 0.5:
                    best_score = score
                    t_longhand = longhand
        
        # Compare against all sensor variables
        for j, s_var in enumerate(sensor_clean):
            s_var_raw = sensor_raw[j]
            
            # Skip if already matched
            if s_var_raw in matched_sensor:
                continue
            
            # Get longhand for sensor variable
            if s_var in short_to_long:
                s_longhand = short_to_long[s_var]
            else:
                s_longhand = s_var
            
            # Calculate similarity
            similarity = token_similarity(t_longhand, s_longhand)
            
            if similarity > 0.5:
                match_type = 'Dictionary-Medium'
                if similarity > 0.7:
                    match_type = 'Dictionary-High'
                if similarity > 0.8:
                    match_type = 'Dictionary-Exact'
                
                matches.append({
                    'Telemetry_Variable': t_var_raw,
                    'Sensor_Variable': s_var_raw,
                    'MatchType': match_type,
                    'Confidence': round(similarity, 3),
                    'Description': f'T:{t_longhand} | S:{s_longhand}'
                })
                
                matched_telem.add(t_var_raw)
                matched_sensor.add(s_var_raw)
    
    print(f"Found {len(matches)} dictionary-based matches\n")
    return matches

def pass3_semantic_matches(telem_raw, telem_clean, sensor_raw, sensor_clean,
                          short_to_long, matched_telem, matched_sensor):
    """Pass 3: Semantic token matching"""
    print("=== PASS 3: SEMANTIC TOKEN MATCHING ===")
    matches = []
    
    for i, t_var in enumerate(telem_clean):
        t_var_raw = telem_raw[i]
        
        # Skip if already matched
        if t_var_raw in matched_telem:
            continue
        
        best_matches = []
        
        for j, s_var in enumerate(sensor_clean):
            s_var_raw = sensor_raw[j]
            
            # Skip if already matched
            if s_var_raw in matched_sensor:
                continue
            
            # Get sensor description
            s_description = short_to_long.get(s_var, s_var)
            
            # Calculate semantic similarity
            score = token_similarity(t_var, s_description)
            
            if score > 0.4:
                best_matches.append((s_var_raw, score, s_description))
        
        # Keep top matches
        if best_matches:
            best_matches.sort(key=lambda x: x[1], reverse=True)
            top_score = best_matches[0][1]
            
            # Keep matches within 0.1 of best score and > 0.5
            for s_var_raw, score, s_desc in best_matches:
                if score >= (top_score - 0.1) and score > 0.5:
                    matches.append({
                        'Telemetry_Variable': t_var_raw,
                        'Sensor_Variable': s_var_raw,
                        'MatchType': 'Semantic',
                        'Confidence': round(score, 3),
                        'Description': f'T:{t_var} | S:{s_desc}'
                    })
    
    print(f"Found {len(matches)} semantic matches\n")
    return matches

def main():
    """Main execution function"""
    # Load data
    short_to_long, dict_df = load_dictionary()
    telem_raw, telem_clean = load_telemetry_data()
    sensor_raw, sensor_clean = load_sensor_data()
    
    # Track matched variables
    matched_telem = set()
    matched_sensor = set()
    
    # Pass 1: Exact matches
    exact_matches = pass1_exact_matches(telem_raw, telem_clean, sensor_raw, sensor_clean)
    matched_telem.update([m['Telemetry_Variable'] for m in exact_matches])
    matched_sensor.update([m['Sensor_Variable'] for m in exact_matches])
    
    # Pass 2: Dictionary matches
    dict_matches = pass2_dictionary_matches(telem_raw, telem_clean, sensor_raw, sensor_clean,
                                           short_to_long, matched_telem, matched_sensor)
    
    # Pass 3: Semantic matches
    semantic_matches = pass3_semantic_matches(telem_raw, telem_clean, sensor_raw, sensor_clean,
                                             short_to_long, matched_telem, matched_sensor)
    
    # Combine all matches
    print("=== COMBINING RESULTS ===")
    all_matches = exact_matches + dict_matches + semantic_matches
    
    if all_matches:
        # Create DataFrame
        results_df = pd.DataFrame(all_matches)
        
        # Sort by confidence
        results_df = results_df.sort_values('Confidence', ascending=False)
        
        # Filter high confidence (>= 0.7)
        high_conf_df = results_df[results_df['Confidence'] >= 0.7]
        
        print(f"\nTotal matches found (all confidence levels): {len(results_df)}")
        print(f"Matches with confidence >= 0.7: {len(high_conf_df)}")
        
        print("\nTop 30 matches (confidence >= 0.7):")
        print(high_conf_df.head(30).to_string(index=False))
        
        # Save results
        results_df.to_csv('variable_matches_all.csv', index=False)
        print("\n✓ All results saved to: variable_matches_all.csv")
        
        high_conf_df.to_csv('variable_matches_high_confidence.csv', index=False)
        print("✓ High confidence results (>= 0.7) saved to: variable_matches_high_confidence.csv")
        
        # Summary statistics
        print("\n=== SUMMARY STATISTICS ===")
        print(f"Exact name matches: {len(exact_matches)}")
        print(f"Dictionary matches: {len(dict_matches)}")
        print(f"Semantic matches: {len(semantic_matches)}")
        print(f"Total matches (all): {len(all_matches)}")
        
        print("\nAll Matches:")
        print(f"  Telemetry variables matched: {len(results_df['Telemetry_Variable'].unique())} / {len(telem_raw)} "
              f"({100 * len(results_df['Telemetry_Variable'].unique()) / len(telem_raw):.1f}%)")
        print(f"  Sensor variables matched: {len(results_df['Sensor_Variable'].unique())} / {len(sensor_raw)} "
              f"({100 * len(results_df['Sensor_Variable'].unique()) / len(sensor_raw):.1f}%)")
        
        print("\nHigh Confidence Matches (>= 0.7):")
        print(f"  Telemetry variables matched: {len(high_conf_df['Telemetry_Variable'].unique())} / {len(telem_raw)} "
              f"({100 * len(high_conf_df['Telemetry_Variable'].unique()) / len(telem_raw):.1f}%)")
        print(f"  Sensor variables matched: {len(high_conf_df['Sensor_Variable'].unique())} / {len(sensor_raw)} "
              f"({100 * len(high_conf_df['Sensor_Variable'].unique()) / len(sensor_raw):.1f}%)")
    else:
        print("No matches found.")
    
    print("\n=== COMPLETE ===")

if __name__ == "__main__":
    main()