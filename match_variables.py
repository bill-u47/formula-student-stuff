#!/usr/bin/env python3


import pandas as pd
import csv
from typing import Dict, List, Tuple, Set
import re

class VehicleTelemetryMatcher:
    """
    Intelligent matcher for vehicle telemetry variables between Motec and CarSim systems.
    """
    
    def __init__(self):
        """Initialize the matcher with position mappings and domain knowledge."""
        # Position mapping: Motec notation → CarSim notation
        self.position_map = {
            'FL': 'L1',  # Front Left
            'FR': 'R1',  # Front Right
            'RL': 'L2',  # Rear Left
            'RR': 'R2',  # Rear Right
        }
        
        # Reverse mapping for CarSim → Motec
        self.reverse_position_map = {v: k for k, v in self.position_map.items()}
        
        # Physics notation mappings
        self.physics_notation = {
            'X': 'Longitudinal',
            'Y': 'Lateral', 
            'Z': 'Vertical',
            'x': 'Long',
            'y': 'Lat',
            'z': 'Vert'
        }
        
        # Semantic equivalences
        self.semantic_equivalents = {
            'gforce': ['accel', 'acceleration', 'a'],
            'gyro': ['rate', 'av', 'angularvelocity'],
            'speed': ['velocity', 'v', 'spin'],
            'susp': ['suspension', 'jounce', 'compression', 'cmp'],
            'brake': ['bk', 'pbk'],
            'temp': ['temperature', 't'],
            'rotor': ['rtr'],
            'wheel': ['whl'],
            'engine': ['eng'],
            'throttle': ['thr'],
            'steer': ['str'],
            'fuel': ['qfuel', 'mfuel']
        }
        
        # Load data
        self.dictionary = None
        self.motec_headers = []
        self.carsim_headers = []
        self.matches = []
        
    def normalize_text(self, text: str) -> str:
        """Normalize text: lowercase and remove special characters."""
        return re.sub(r'[^a-z0-9]', '', str(text).lower())
    
    def remove_whitespace(self, text: str) -> str:
        """Remove all whitespace from text."""
        return re.sub(r'\s+', '', str(text))
    
    def extract_tokens(self, text: str) -> List[str]:
        """Extract meaningful tokens from text."""
        # Remove units in parentheses
        text = re.sub(r'\([^)]*\)', '', str(text))
        normalized = self.normalize_text(text)
        
        # Extract all alphanumeric sequences
        tokens = re.findall(r'\w+', normalized)
        
        # Filter stopwords
        stopwords = {'the', 'of', 'for', 'at', 'in', 'on', 'to', 'a', 'an', 'and', 'is'}
        tokens = [t for t in tokens if t not in stopwords]
        
        return tokens
    
    def extract_position(self, text: str) -> str:
        """Extract wheel position from variable name (FL, FR, RL, RR, L1, R1, L2, R2)."""
        text_upper = text.upper()
        
        # Check for Motec notation (FL, FR, RL, RR)
        for pos in ['FL', 'FR', 'RL', 'RR']:
            if pos in text_upper:
                return pos
        
        # Check for CarSim notation (L1, R1, L2, R2)
        for pos in ['L1', 'R1', 'L2', 'R2']:
            if pos in text_upper:
                # Convert to Motec notation for consistency
                return self.reverse_position_map.get(pos, '')
        
        return ''
    
    def map_position_motec_to_carsim(self, motec_pos: str) -> str:
        """Map Motec position notation to CarSim notation."""
        return self.position_map.get(motec_pos, '')
    
    def semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts."""
        tokens1 = set(self.extract_tokens(text1))
        tokens2 = set(self.extract_tokens(text2))
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Direct token overlap (Jaccard similarity)
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        direct_score = intersection / union if union > 0 else 0.0
        
        # Semantic equivalence boost
        semantic_matches = 0
        for t1 in tokens1:
            for t2 in tokens2:
                if t1 == t2:
                    continue
                # Check if semantically equivalent
                for key, equivalents in self.semantic_equivalents.items():
                    if (t1 == key or t1 in equivalents) and (t2 == key or t2 in equivalents):
                        semantic_matches += 1
                        break
        
        semantic_boost = min(semantic_matches * 0.1, 0.3)
        
        return min(direct_score + semantic_boost, 1.0)
    
    def load_dictionary(self, filepath: str = 'dictionary.csv'):
        """Load dictionary mapping from CSV."""
        print("=== LOADING DICTIONARY ===")
        try:
            # Read dictionary with first 2 columns
            df = pd.read_csv(filepath, usecols=[0, 1], names=['shorthand', 'longhand'], 
                           header=0, encoding='utf-8')
            
            df = df.dropna()
            df['shorthand_clean'] = df['shorthand'].apply(self.remove_whitespace)
            df['longhand_clean'] = df['longhand'].apply(self.remove_whitespace)
            
            self.dictionary = df
            
            print(f"✓ Dictionary loaded: {len(df)} entries")
            print(f"  Sample: {df['shorthand'].iloc[0]} → {df['longhand'].iloc[0]}")
            print()
            
        except Exception as e:
            print(f"✗ Error loading dictionary: {e}")
            raise
    
    def load_motec_data(self, filepath: str = 'fb24MotecSmaller.csv'):
        """Load Motec telemetry data (headers in row 15)."""
        print("=== LOADING MOTEC TELEMETRY DATA ===")
        try:
            # Read row 15 as headers (0-indexed = row 14)
            df = pd.read_csv(filepath, header=14, nrows=0, encoding='utf-8')
            self.motec_headers = df.columns.tolist()
            
            print(f"✓ Motec variables loaded: {len(self.motec_headers)}")
            print(f"  Sample: {self.motec_headers[:3]}")
            print()
            
        except Exception as e:
            print(f"✗ Error loading Motec data: {e}")
            raise
    
    def load_carsim_data(self, filepath: str = 'oct14CarsimSmaller.csv'):
        """Load CarSim sensor data (headers in row 1)."""
        print("=== LOADING CARSIM SENSOR DATA ===")
        try:
            df = pd.read_csv(filepath, nrows=0, encoding='utf-8')
            self.carsim_headers = df.columns.tolist()
            
            print(f"✓ CarSim variables loaded: {len(self.carsim_headers)}")
            print(f"  Sample: {self.carsim_headers[:3]}")
            print()
            
        except Exception as e:
            print(f"✗ Error loading CarSim data: {e}")
            raise
    
    def get_dictionary_description(self, shorthand: str) -> str:
        """Get longhand description from dictionary for a given shorthand."""
        shorthand_clean = self.remove_whitespace(shorthand)
        
        if self.dictionary is None:
            return shorthand
        
        match = self.dictionary[self.dictionary['shorthand_clean'] == shorthand_clean]
        
        if not match.empty:
            return match.iloc[0]['longhand']
        
        return shorthand
    
    def match_exact_names(self):
        """Step 1: Find exact variable name matches."""
        print("=== STEP 1: EXACT NAME MATCHING ===")
        matches = []
        
        for motec_var in self.motec_headers:
            for carsim_var in self.carsim_headers:
                if self.normalize_text(motec_var) == self.normalize_text(carsim_var):
                    matches.append({
                        'Motec_Variable': motec_var,
                        'CarSim_Variable': carsim_var,
                        'Confidence': 1.0,
                        'Match_Type': 'Exact',
                        'Dictionary_Description': 'Identical variable names',
                        'Notes': 'No dictionary needed - exact string match'
                    })
        
        print(f"✓ Found {len(matches)} exact matches")
        if matches:
            print(f"  Example: {matches[0]['Motec_Variable']} = {matches[0]['CarSim_Variable']}")
        print()
        
        return matches
    
    def match_accelerations(self):
        """Step 2: Match acceleration variables (G Force → Ax/Ay/Az)."""
        print("=== STEP 2: ACCELERATION MATCHING ===")
        matches = []
        
        # Define acceleration patterns
        accel_patterns = [
            {
                'motec': ['C185 G Force Lat', 'F IMU Vehicle Accel Lateral', 'R IMU Vehicle Accel Lateral'],
                'carsim': ['Ay_SM', 'Ay_Rd'],
                'axis': 'Lateral (Y)',
                'confidence_base': 1.0
            },
            {
                'motec': ['C185 G Force Long', 'F IMU Vehicle Accel Long', 'R IMU Vehicle Accel Long'],
                'carsim': ['Ax_SM', 'Ax_Rd'],
                'axis': 'Longitudinal (X)',
                'confidence_base': 1.0
            },
            {
                'motec': ['C185 G Force Vert', 'F IMU Vehicle Accel Vert', 'R IMU Vehicle Accel Vert'],
                'carsim': ['Az_SM', 'Az_Rd'],
                'axis': 'Vertical (Z)',
                'confidence_base': 1.0
            }
        ]
        
        for pattern in accel_patterns:
            for motec_var in self.motec_headers:
                if any(p in motec_var for p in pattern['motec']):
                    for carsim_var in pattern['carsim']:
                        if carsim_var in self.carsim_headers:
                            desc = self.get_dictionary_description(carsim_var)
                            confidence = pattern['confidence_base']
                            if '_Rd' in carsim_var:
                                confidence -= 0.05  # Road frame slightly less confident
                            
                            matches.append({
                                'Motec_Variable': motec_var,
                                'CarSim_Variable': carsim_var,
                                'Confidence': confidence,
                                'Match_Type': 'Acceleration',
                                'Dictionary_Description': desc,
                                'Notes': f"{pattern['axis']} acceleration"
                            })
        
        print(f"✓ Found {len(matches)} acceleration matches")
        print()
        return matches
    
    def match_gyroscopes(self):
        """Step 3: Match gyroscope/angular velocity variables."""
        print("=== STEP 3: GYROSCOPE MATCHING ===")
        matches = []
        
        gyro_patterns = [
            {
                'motec': ['F IMU Gyro Roll Velocity', 'R IMU Gyro Roll Velocity'],
                'carsim': ['AVx', 'AV_R'],
                'axis': 'Roll (X)',
                'body_fixed': True
            },
            {
                'motec': ['F IMU Gyro Pitch Velocity', 'R IMU Gyro Pitch Velocity'],
                'carsim': ['AVy', 'AV_P'],
                'axis': 'Pitch (Y)',
                'body_fixed': True
            },
            {
                'motec': ['F IMU Gyro Yaw Velocity', 'R IMU Gyro Yaw Velocity'],
                'carsim': ['AVz', 'AV_Y'],
                'axis': 'Yaw (Z)',
                'body_fixed': True
            }
        ]
        
        for pattern in gyro_patterns:
            for motec_var in self.motec_headers:
                if any(p in motec_var for p in pattern['motec']):
                    for carsim_var in pattern['carsim']:
                        if carsim_var in self.carsim_headers:
                            desc = self.get_dictionary_description(carsim_var)
                            
                            # Determine if body-fixed or Euler
                            is_euler = '_' in carsim_var  # AV_R, AV_P, AV_Y are Euler
                            frame = 'Euler' if is_euler else 'body-fixed'
                            
                            matches.append({
                                'Motec_Variable': motec_var,
                                'CarSim_Variable': carsim_var,
                                'Confidence': 1.0,
                                'Match_Type': 'Gyroscope',
                                'Dictionary_Description': desc,
                                'Notes': f"{pattern['axis']} rate ({frame})"
                            })
        
        print(f"✓ Found {len(matches)} gyroscope matches")
        print()
        return matches
    
    def match_wheel_speeds(self):
        """Step 4: Match wheel speed variables with position mapping."""
        print("=== STEP 4: WHEEL SPEED MATCHING ===")
        matches = []
        
        for motec_var in self.motec_headers:
            if 'Wheel Speed' in motec_var:
                # Extract position (FL, FR, RL, RR)
                motec_pos = self.extract_position(motec_var)
                if motec_pos:
                    # Map to CarSim notation
                    carsim_pos = self.map_position_motec_to_carsim(motec_pos)
                    carsim_var = f'AVy_{carsim_pos}'
                    
                    if carsim_var in self.carsim_headers:
                        desc = self.get_dictionary_description(carsim_var)
                        
                        matches.append({
                            'Motec_Variable': motec_var,
                            'CarSim_Variable': carsim_var,
                            'Confidence': 1.0,
                            'Match_Type': 'Wheel',
                            'Dictionary_Description': desc,
                            'Notes': f"Wheel spin (rpm) - {motec_pos}={carsim_pos}"
                        })
        
        print(f"✓ Found {len(matches)} wheel speed matches")
        print()
        return matches
    
    def match_suspension(self):
        """Step 5: Match suspension position variables."""
        print("=== STEP 5: SUSPENSION MATCHING ===")
        matches = []
        
        for motec_var in self.motec_headers:
            if 'Susp Pos' in motec_var:
                motec_pos = self.extract_position(motec_var)
                if motec_pos:
                    carsim_pos = self.map_position_motec_to_carsim(motec_pos)
                    
                    # Primary match: Jnc (jounce)
                    carsim_var_jnc = f'Jnc_{carsim_pos}'
                    if carsim_var_jnc in self.carsim_headers:
                        desc = self.get_dictionary_description(carsim_var_jnc)
                        matches.append({
                            'Motec_Variable': motec_var,
                            'CarSim_Variable': carsim_var_jnc,
                            'Confidence': 1.0,
                            'Match_Type': 'Suspension',
                            'Dictionary_Description': desc,
                            'Notes': f"Jounce (compression) - {motec_pos}={carsim_pos}"
                        })
                    
                    # Secondary match: CmpT (total compression)
                    carsim_var_cmp = f'CmpT_{carsim_pos}'
                    if carsim_var_cmp in self.carsim_headers:
                        desc = self.get_dictionary_description(carsim_var_cmp)
                        matches.append({
                            'Motec_Variable': motec_var,
                            'CarSim_Variable': carsim_var_cmp,
                            'Confidence': 0.95,
                            'Match_Type': 'Suspension',
                            'Dictionary_Description': desc,
                            'Notes': f"Total compression - {motec_pos}={carsim_pos}"
                        })
        
        print(f"✓ Found {len(matches)} suspension matches")
        print()
        return matches
    
    def match_brake_pressure(self):
        """Step 6: Match brake pressure variables."""
        print("=== STEP 6: BRAKE PRESSURE MATCHING ===")
        matches = []
        
        brake_mappings = [
            {'motec': 'Brake Pressure Front', 'positions': ['L1', 'R1'], 'axle': 'Front'},
            {'motec': 'Brake Pressure Rear', 'positions': ['L2', 'R2'], 'axle': 'Rear'}
        ]
        
        for mapping in brake_mappings:
            for motec_var in self.motec_headers:
                if mapping['motec'] in motec_var:
                    for pos in mapping['positions']:
                        carsim_var = f'PbkCh_{pos}'
                        if carsim_var in self.carsim_headers:
                            desc = self.get_dictionary_description(carsim_var)
                            motec_pos = self.reverse_position_map[pos]
                            
                            matches.append({
                                'Motec_Variable': motec_var,
                                'CarSim_Variable': carsim_var,
                                'Confidence': 0.95,
                                'Match_Type': 'Brake',
                                'Dictionary_Description': desc,
                                'Notes': f"{mapping['axle']} brake pressure - {motec_pos}={pos}"
                            })
        
        print(f"✓ Found {len(matches)} brake pressure matches")
        print()
        return matches
    
    def match_rotor_temperatures(self):
        """Step 7: Match brake rotor temperature variables."""
        print("=== STEP 7: ROTOR TEMPERATURE MATCHING ===")
        matches = []
        
        # Rotor temp pattern: FL/FR/RL/RR Rotor Temp 1/2/3/4/Max
        for motec_var in self.motec_headers:
            if 'Rotor Temp' in motec_var:
                motec_pos = self.extract_position(motec_var)
                if motec_pos:
                    carsim_pos = self.map_position_motec_to_carsim(motec_pos)
                    carsim_var = f'T_Rtr_{carsim_pos}'
                    
                    if carsim_var in self.carsim_headers:
                        desc = self.get_dictionary_description(carsim_var)
                        
                        # Higher confidence for "Max" variants
                        confidence = 1.0 if 'Max' in motec_var else 0.95
                        note_suffix = 'Max of sensors' if 'Max' in motec_var else 'Multiple sensors to single output'
                        
                        matches.append({
                            'Motec_Variable': motec_var,
                            'CarSim_Variable': carsim_var,
                            'Confidence': confidence,
                            'Match_Type': 'Temperature',
                            'Dictionary_Description': desc,
                            'Notes': f"Rotor temperature {motec_pos}={carsim_pos} - {note_suffix}"
                        })
        
        print(f"✓ Found {len(matches)} rotor temperature matches")
        print()
        return matches
    
    def match_engine_powertrain(self):
        """Step 8: Match engine and powertrain variables."""
        print("=== STEP 8: ENGINE/POWERTRAIN MATCHING ===")
        matches = []
        
        engine_mappings = [
            {'motec': 'Engine Speed', 'carsim': 'AV_Eng', 'confidence': 1.0},
            {'motec': 'Throttle Position', 'carsim': ['Throttle', 'Thr_Eng', 'Thr_Intl'], 
             'confidence': [1.0, 0.98, 0.95]},
            {'motec': 'Gear', 'carsim': ['GearStat', 'Gear_CL', 'Gear_OL'], 
             'confidence': [1.0, 0.90, 0.85]},
        ]
        
        for mapping in engine_mappings:
            for motec_var in self.motec_headers:
                if mapping['motec'] in motec_var:
                    carsim_vars = mapping['carsim'] if isinstance(mapping['carsim'], list) else [mapping['carsim']]
                    confidences = mapping['confidence'] if isinstance(mapping['confidence'], list) else [mapping['confidence']]
                    
                    for carsim_var, conf in zip(carsim_vars, confidences):
                        if carsim_var in self.carsim_headers:
                            desc = self.get_dictionary_description(carsim_var)
                            
                            matches.append({
                                'Motec_Variable': motec_var,
                                'CarSim_Variable': carsim_var,
                                'Confidence': conf,
                                'Match_Type': 'Engine/Powertrain',
                                'Dictionary_Description': desc,
                                'Notes': f"{mapping['motec']} measurement"
                            })
        
        print(f"✓ Found {len(matches)} engine/powertrain matches")
        print()
        return matches
    
    def match_gps(self):
        """Step 9: Match GPS variables."""
        print("=== STEP 9: GPS MATCHING ===")
        matches = []
        
        gps_mappings = [
            {'motec': 'GPS Altitude', 'carsim': ['GPS_Altitude'], 'confidence': [1.0]},
            {'motec': 'GPS Latitude', 'carsim': ['GPS_Lat', 'GPS_LatA'], 'confidence': [1.0, 0.95]},
            {'motec': 'GPS Longitude', 'carsim': ['GPS_Long', 'GPSlongA'], 'confidence': [1.0, 1.0]},
            {'motec': 'GPS Speed', 'carsim': ['Vx'], 'confidence': [0.85]},
        ]
        
        for mapping in gps_mappings:
            for motec_var in self.motec_headers:
                if mapping['motec'] in motec_var:
                    for carsim_var, conf in zip(mapping['carsim'], mapping['confidence']):
                        if carsim_var in self.carsim_headers:
                            desc = self.get_dictionary_description(carsim_var)
                            
                            matches.append({
                                'Motec_Variable': motec_var,
                                'CarSim_Variable': carsim_var,
                                'Confidence': conf,
                                'Match_Type': 'GPS',
                                'Dictionary_Description': desc,
                                'Notes': f"GPS {mapping['motec']}"
                            })
        
        print(f"✓ Found {len(matches)} GPS matches")
        print()
        return matches
    
    def match_velocity(self):
        """Step 10: Match velocity/speed variables."""
        print("=== STEP 10: VELOCITY MATCHING ===")
        matches = []
        
        velocity_mappings = [
            {'motec': 'Ground Speed', 'carsim': ['Vx', 'Vx_SM', 'Vx_Fwd'], 
             'confidence': [1.0, 1.0, 0.95]},
            {'motec': 'Drive Speed', 'carsim': ['Vx'], 'confidence': [0.90]},
        ]
        
        for mapping in velocity_mappings:
            for motec_var in self.motec_headers:
                if mapping['motec'] in motec_var:
                    for carsim_var, conf in zip(mapping['carsim'], mapping['confidence']):
                        if carsim_var in self.carsim_headers:
                            desc = self.get_dictionary_description(carsim_var)
                            
                            matches.append({
                                'Motec_Variable': motec_var,
                                'CarSim_Variable': carsim_var,
                                'Confidence': conf,
                                'Match_Type': 'Velocity',
                                'Dictionary_Description': desc,
                                'Notes': f"Longitudinal velocity"
                            })
        
        print(f"✓ Found {len(matches)} velocity matches")
        print()
        return matches
    
    def match_fuel(self):
        """Step 11: Match fuel-related variables."""
        print("=== STEP 11: FUEL MATCHING ===")
        matches = []
        
        fuel_mappings = [
            {'motec': 'Fuel Flow', 'carsim': 'Qfuel', 'confidence': 1.0},
            {'motec': 'Fuel Used M1', 'carsim': 'Mfuel', 'confidence': 1.0},
        ]
        
        for mapping in fuel_mappings:
            for motec_var in self.motec_headers:
                if mapping['motec'] in motec_var:
                    carsim_var = mapping['carsim']
                    if carsim_var in self.carsim_headers:
                        desc = self.get_dictionary_description(carsim_var)
                        
                        matches.append({
                            'Motec_Variable': motec_var,
                            'CarSim_Variable': carsim_var,
                            'Confidence': mapping['confidence'],
                            'Match_Type': 'Fuel',
                            'Dictionary_Description': desc,
                            'Notes': f"Fuel measurement"
                        })
        
        print(f"✓ Found {len(matches)} fuel matches")
        print()
        return matches
    
    def match_distance(self):
        """Step 12: Match distance/odometer variables."""
        print("=== STEP 12: DISTANCE MATCHING ===")
        matches = []
        
        distance_mappings = [
            {'motec': 'Odometer', 'carsim': 'Station', 'confidence': 0.90},
            {'motec': 'Trip Distance', 'carsim': 'Station', 'confidence': 0.85},
            {'motec': 'Distance', 'carsim': 'Station', 'confidence': 0.90},
            {'motec': 'Lap Distance', 'carsim': 'Sta_Road', 'confidence': 0.80},
        ]
        
        for mapping in distance_mappings:
            for motec_var in self.motec_headers:
                if mapping['motec'] == motec_var or mapping['motec'] in motec_var:
                    carsim_var = mapping['carsim']
                    if carsim_var in self.carsim_headers:
                        desc = self.get_dictionary_description(carsim_var)
                        
                        matches.append({
                            'Motec_Variable': motec_var,
                            'CarSim_Variable': carsim_var,
                            'Confidence': mapping['confidence'],
                            'Match_Type': 'Distance',
                            'Dictionary_Description': desc,
                            'Notes': f"Distance/path measurement"
                        })
        
        print(f"✓ Found {len(matches)} distance matches")
        print()
        return matches
    
    def match_steering(self):
        """Step 13: Match steering-related variables."""
        print("=== STEP 13: STEERING MATCHING ===")
        matches = []
        
        for motec_var in self.motec_headers:
            if 'Steered Angle' in motec_var or 'Steer Angle' in motec_var:
                steering_vars = [
                    ('Steer_SW', 0.95, 'Steering wheel angle'),
                    ('Steer_L1', 0.90, 'FL wheel steer angle'),
                    ('Steer_R1', 0.90, 'FR wheel steer angle'),
                ]
                
                for carsim_var, conf, note in steering_vars:
                    if carsim_var in self.carsim_headers:
                        desc = self.get_dictionary_description(carsim_var)
                        
                        matches.append({
                            'Motec_Variable': motec_var,
                            'CarSim_Variable': carsim_var,
                            'Confidence': conf,
                            'Match_Type': 'Steering',
                            'Dictionary_Description': desc,
                            'Notes': note
                        })
        
        print(f"✓ Found {len(matches)} steering matches")
        print()
        return matches
    
    def run_matching(self):
        """Execute the complete matching process."""
        print("=" * 70)
        print("VEHICLE TELEMETRY VARIABLE MATCHER")
        print("Motec → CarSim Variable Matching with Dictionary Validation")
        print("=" * 70)
        print()
        
        # Execute all matching steps
        all_matches = []
        
        all_matches.extend(self.match_exact_names())
        all_matches.extend(self.match_accelerations())
        all_matches.extend(self.match_gyroscopes())
        all_matches.extend(self.match_wheel_speeds())
        all_matches.extend(self.match_suspension())
        all_matches.extend(self.match_brake_pressure())
        all_matches.extend(self.match_rotor_temperatures())
        all_matches.extend(self.match_engine_powertrain())
        all_matches.extend(self.match_gps())
        all_matches.extend(self.match_velocity())
        all_matches.extend(self.match_fuel())
        all_matches.extend(self.match_distance())
        all_matches.extend(self.match_steering())
        
        self.matches = all_matches
        
        return all_matches
    
    def generate_report(self):
        """Generate summary report of matches."""
        print("=" * 70)
        print("MATCHING SUMMARY")
        print("=" * 70)
        print()
        
        df = pd.DataFrame(self.matches)
        
        if df.empty:
            print("No matches found.")
            return
        
        # Sort by confidence
        df = df.sort_values('Confidence', ascending=False)
        
        # Statistics
        total_matches = len(df)
        unique_motec = df['Motec_Variable'].nunique()
        unique_carsim = df['CarSim_Variable'].nunique()
        
        conf_1_0 = len(df[df['Confidence'] == 1.0])
        conf_0_95 = len(df[(df['Confidence'] >= 0.95) & (df['Confidence'] < 1.0)])
        conf_0_90 = len(df[(df['Confidence'] >= 0.90) & (df['Confidence'] < 0.95)])
        conf_0_85 = len(df[(df['Confidence'] >= 0.85) & (df['Confidence'] < 0.90)])
        conf_below = len(df[df['Confidence'] < 0.85])
        
        print(f"Total Matches: {total_matches}")
        print(f"Unique Motec Variables Matched: {unique_motec} / {len(self.motec_headers)} "
              f"({100*unique_motec/len(self.motec_headers):.1f}%)")
        print(f"Unique CarSim Variables Matched: {unique_carsim} / {len(self.carsim_headers)} "
              f"({100*unique_carsim/len(self.carsim_headers):.1f}%)")
        print()
        
        print("Confidence Distribution:")
        print(f"  1.00 (Perfect): {conf_1_0} matches")
        print(f"  0.95-0.99: {conf_0_95} matches")
        print(f"  0.90-0.94: {conf_0_90} matches")
        print(f"  0.85-0.89: {conf_0_85} matches")
        print(f"  < 0.85: {conf_below} matches")
        print()
        
        print("Match Type Distribution:")
        for match_type, count in df['Match_Type'].value_counts().items():
            print(f"  {match_type}: {count} matches")
        print()
        
        # Top 20 matches
        print("Top 20 Highest Confidence Matches:")
        print("-" * 70)
        for idx, row in df.head(20).iterrows():
            print(f"{row['Motec_Variable']:40} → {row['CarSim_Variable']:15} "
                  f"({row['Confidence']:.2f}) [{row['Match_Type']}]")
        print()
        
        return df
    
    def save_results(self, output_file: str = 'matched_variables.csv'):
        """Save matches to CSV file."""
        if not self.matches:
            print("No matches to save.")
            return
        
        df = pd.DataFrame(self.matches)
        df = df.sort_values('Confidence', ascending=False)
        
        df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL)
        print(f"✓ Results saved to: {output_file}")
        print()


def main():
    """Main execution function."""
    # Initialize matcher
    matcher = VehicleTelemetryMatcher()
    
    # Load data
    matcher.load_dictionary('dictionary.csv')
    matcher.load_motec_data('fb24MotecSmaller.csv')
    matcher.load_carsim_data('oct14CarsimSmaller.csv')
    
    # Run matching
    matches = matcher.run_matching()
    
    # Generate report
    df = matcher.generate_report()
    
    # Save results
    matcher.save_results('matched_variables_validated.csv')
    
    print("=" * 70)
    print("MATCHING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()