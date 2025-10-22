% compare_telemetry_sensor.m
% Intelligently compares fb24Motec.csv (telemetry) with oct14Carsim.csv (sensor)
% Uses dictionary.csv with semantic matching and token-based similarity
%
% NOTE: Motec headers are in row 15, Carsim headers are in row 1
%
% Author: bill-u47
% Date: 2025-01-22

%% Utility Functions
remove_whitespace = @(str) regexprep(str, '\s+', '');

function text_norm = normalize_text(str)
    text_norm = lower(regexprep(str, '[^a-zA-Z0-9]', ''));
end

% Extract meaningful tokens from text
function tokens = extract_tokens(text)
    % Remove units and normalize
    text = regexprep(text, '\([^)]*\)', ''); % Remove anything in parentheses
    text = normalize_text(text);
    
    % Split into tokens and filter stopwords
    stopwords = {'the', 'of', 'for', 'at', 'in', 'on', 'to', 'a', 'an', 'and'};
    tokens = regexp(text, '\w+', 'match');
    if ~isempty(tokens)
        tokens = tokens(~ismember(tokens, stopwords));
    end
end

% Calculate token similarity score between two texts
function score = token_similarity(text1, text2)
    tokens1 = extract_tokens(text1);
    tokens2 = extract_tokens(text2);
    
    if isempty(tokens1) || isempty(tokens2)
        score = 0;
        return;
    end
    
    % Count shared tokens
    shared = sum(ismember(tokens1, tokens2));
    total = length(unique([tokens1, tokens2]));
    
    if total == 0
        score = 0;
    else
        score = shared / total;
    end
end

%% Load Dictionary
fprintf('=== LOADING DICTIONARY ===\n'); %[output:963e497d]
try
    dict = readtable('dictionary.csv', 'VariableNamingRule', 'preserve');
catch
    error('Could not load dictionary.csv. Make sure the file exists in the current directory.');
end

shorthand_raw = dict{:,1};
longhand_raw = dict{:,2};

% Create mappings
shorthand_clean = cell(size(shorthand_raw));
longhand_clean = cell(size(longhand_raw));

for i = 1:length(shorthand_raw)
    if ischar(shorthand_raw{i}) || isstring(shorthand_raw{i})
        shorthand_clean{i} = remove_whitespace(char(shorthand_raw{i}));
        longhand_clean{i} = remove_whitespace(char(longhand_raw{i}));
    else
        shorthand_clean{i} = '';
        longhand_clean{i} = '';
    end
end

% Build lookup maps
short_to_long = containers.Map();
for i = 1:length(shorthand_clean)
    if ~isempty(shorthand_clean{i})
        short_to_long(shorthand_clean{i}) = longhand_clean{i};
    end
end

fprintf('Dictionary loaded: %d entries\n\n', length(shorthand_clean)); %[output:79c9dbf1]

%% Load Telemetry Data (Motec - headers in row 15)
fprintf('=== LOADING TELEMETRY DATA (MOTEC) ===\n'); %[output:0c7ce6af]
try %[output:group:38d4308d]
    % Read the file to get row 15 as headers
    opts = detectImportOptions('fb24Motec.csv', 'VariableNamingRule', 'preserve');
    opts.DataLine = 16; % Data starts at row 16
    opts.VariableNamesLine = 15; % Headers are in row 15
    
    telemetry_tbl = readtable('fb24Motec.csv', opts);
    telemetry_headers_raw = telemetry_tbl.Properties.VariableNames;
    
    telemetry_headers = cell(size(telemetry_headers_raw));
    for i = 1:length(telemetry_headers_raw)
        telemetry_headers{i} = remove_whitespace(telemetry_headers_raw{i});
    end
    fprintf('Telemetry variables: %d\n', length(telemetry_headers)); %[output:8e95651d]
catch ME
    error('Could not load fb24Motec.csv: %s', ME.message);
end %[output:group:38d4308d]

%% Load Sensor Data (Carsim - headers in row 1)
fprintf('=== LOADING SENSOR DATA (CARSIM) ===\n'); %[output:8d9c9816]
try %[output:group:39313069]
    sensor_tbl = readtable('oct14Carsim.csv', 'VariableNamingRule', 'preserve');
    sensor_headers_raw = sensor_tbl.Properties.VariableNames;
    sensor_headers = cell(size(sensor_headers_raw));
    for i = 1:length(sensor_headers_raw)
        sensor_headers{i} = remove_whitespace(sensor_headers_raw{i});
    end
    fprintf('Sensor variables: %d\n\n', length(sensor_headers)); %[output:13b00aac]
catch ME
    error('Could not load oct14Carsim.csv: %s', ME.message);
end %[output:group:39313069]

%% PASS 1: Exact Variable Name Matches
fprintf('=== PASS 1: EXACT VARIABLE NAME MATCHES ===\n'); %[output:18eaba69]
exact_matches = cell(0, 5);

for i = 1:length(telemetry_headers)
    for j = 1:length(sensor_headers)
        if strcmpi(telemetry_headers{i}, sensor_headers{j})
            exact_matches(end+1, 1:5) = {
                telemetry_headers_raw{i}, 
                sensor_headers_raw{j}, 
                'Exact', 
                1.0, 
                'Identical variable names'
            };
        end
    end
end

fprintf('Found %d exact variable name matches\n\n', size(exact_matches, 1)); %[output:078abb7d]

%% PASS 2: Dictionary-Based Matching
fprintf('=== PASS 2: DICTIONARY-BASED MATCHING ===\n'); %[output:38eb9012]
dict_matches = cell(0, 5);
matched_telemetry = {};
matched_sensor = {};

% Keep track of what was matched in Pass 1
if ~isempty(exact_matches)
    matched_telemetry = exact_matches(:,1);
    matched_sensor = exact_matches(:,2);
end

for ti = 1:length(telemetry_headers)
    t_var = telemetry_headers{ti};
    t_var_raw = telemetry_headers_raw{ti};
    
    % Skip if already matched in Pass 1
    if any(strcmp(matched_telemetry, t_var_raw))
        continue;
    end
    
    % Get longhand for telemetry variable (if it's a shorthand)
    if isKey(short_to_long, t_var)
        t_longhand = short_to_long(t_var);
    else
        % Try to find semantic match in dictionary longhand
        best_score = 0;
        t_longhand = '';
        for k = 1:length(longhand_clean)
            if ~isempty(longhand_clean{k})
                score = token_similarity(t_var, longhand_clean{k});
                if score > best_score && score > 0.5
                    best_score = score;
                    t_longhand = longhand_clean{k};
                end
            end
        end
        if isempty(t_longhand)
            t_longhand = t_var; % Use original if no match
        end
    end
    
    % Compare against all sensor variables
    for si = 1:length(sensor_headers)
        s_var = sensor_headers{si};
        s_var_raw = sensor_headers_raw{si};
        
        % Skip if already matched
        if any(strcmp(matched_sensor, s_var_raw))
            continue;
        end
        
        % Get longhand for sensor variable
        if isKey(short_to_long, s_var)
            s_longhand = short_to_long(s_var);
        else
            s_longhand = s_var;
        end
        
        % Calculate similarity between longhand descriptions
        similarity = token_similarity(t_longhand, s_longhand);
        
        % Lower threshold to 0.5 to catch more matches
        if similarity > 0.5
            match_type = 'Dictionary-Medium';
            if similarity > 0.7
                match_type = 'Dictionary-High';
            end
            if similarity > 0.8
                match_type = 'Dictionary-Exact';
            end
            
            dict_matches(end+1, 1:5) = {
                t_var_raw,
                s_var_raw,
                match_type,
                similarity,
                sprintf('T:%s | S:%s', t_longhand, s_longhand)
            };
            
            matched_telemetry{end+1} = t_var_raw;
            matched_sensor{end+1} = s_var_raw;
        end
    end
end

fprintf('Found %d dictionary-based matches\n\n', size(dict_matches, 1)); %[output:87f1db3d]

%% PASS 3: Semantic Token Matching
fprintf('=== PASS 3: SEMANTIC TOKEN MATCHING ===\n'); %[output:322c8cb7]
semantic_matches = cell(0, 5);

for ti = 1:length(telemetry_headers)
    t_var = telemetry_headers{ti};
    t_var_raw = telemetry_headers_raw{ti};
    
    % Skip if already matched
    if any(strcmp(matched_telemetry, t_var_raw))
        continue;
    end
    
    % Extract tokens from telemetry variable
    t_tokens = extract_tokens(t_var);
    
    best_matches = {};
    
    for si = 1:length(sensor_headers)
        s_var = sensor_headers{si};
        s_var_raw = sensor_headers_raw{si};
        
        % Skip if already matched
        if any(strcmp(matched_sensor, s_var_raw))
            continue;
        end
        
        % Get sensor longhand description
        if isKey(short_to_long, s_var)
            s_description = short_to_long(s_var);
        else
            s_description = s_var;
        end
        
        % Calculate semantic similarity
        score = token_similarity(t_var, s_description);
        
        if score > 0.4
            best_matches{end+1} = {s_var_raw, score, s_description};
        end
    end
    
    % Keep top matches
    if ~isempty(best_matches)
        % Sort by score
        scores = cellfun(@(x) x{2}, best_matches);
        [~, idx] = sort(scores, 'descend');
        
        % Take top 3 or those within 0.1 of best score
        top_score = scores(idx(1));
        keep_idx = scores >= (top_score - 0.1) & scores > 0.4;
        
        for k = find(keep_idx)
            semantic_matches(end+1, 1:5) = {
                t_var_raw,
                best_matches{k}{1},
                'Semantic',
                best_matches{k}{2},
                sprintf('T:%s | S:%s', t_var, best_matches{k}{3})
            };
        end
    end
end

fprintf('Found %d semantic matches\n\n', size(semantic_matches, 1)); %[output:763249d7]

%% Combine Results and Filter by Confidence >= 0.7
fprintf('=== COMBINING RESULTS ===\n'); %[output:73e69610]
all_matches = [exact_matches; dict_matches; semantic_matches];

if ~isempty(all_matches) %[output:group:68ff45c5]
    % Convert to table
    match_tbl = cell2table(all_matches, ...
        'VariableNames', {'Telemetry_Variable', 'Sensor_Variable', 'MatchType', 'Confidence', 'Description'});
    
    % Extract confidence values (they're in column 4 of the cell array)
    confidence_values = [all_matches{:,4}];
    
    % Filter for confidence >= 0.7
    high_conf_idx = confidence_values >= 0.7;
    high_conf_matches = match_tbl(high_conf_idx, :);
    
    % Sort by confidence
    [~, sort_idx] = sort(confidence_values(high_conf_idx), 'descend');
    high_conf_matches = high_conf_matches(sort_idx, :);
    
    fprintf('\nTotal matches found (all confidence levels): %d\n', height(match_tbl)); %[output:5a71ca4f]
    fprintf('Matches with confidence >= 0.7: %d\n', height(high_conf_matches)); %[output:9c08fc78]
    
    fprintf('\nTop 30 matches (confidence >= 0.7):\n'); %[output:4ff0c20f]
    disp(high_conf_matches(1:min(30, height(high_conf_matches)), :)); %[output:7af44b71]
    
    % Save all results
    writetable(match_tbl, 'variable_matches_all.csv');
    fprintf('\nAll results saved to: variable_matches_all.csv\n'); %[output:3e94d7ff]
    
    % Save high confidence results
    writetable(high_conf_matches, 'variable_matches_high_confidence.csv');
    fprintf('High confidence results (>= 0.7) saved to: variable_matches_high_confidence.csv\n'); %[output:3575db5f]
else
    fprintf('No matches found.\n');
end %[output:group:68ff45c5]

%% Summary Statistics
fprintf('\n=== SUMMARY STATISTICS ===\n'); %[output:3ca1c610]
fprintf('Exact name matches: %d\n', size(exact_matches, 1)); %[output:7b822c88]
fprintf('Dictionary matches: %d\n', size(dict_matches, 1)); %[output:88d7730c]
fprintf('Semantic matches: %d\n', size(semantic_matches, 1)); %[output:4b8c13bb]
fprintf('Total matches (all): %d\n', size(all_matches, 1)); %[output:5ac29460]

if ~isempty(all_matches) %[output:group:07eed4c1]
    % Statistics for all matches
    fprintf('\nAll Matches:\n'); %[output:22db1705]
    fprintf('  Telemetry variables matched: %d / %d (%.1f%%)\n', ... %[output:1d7de3d9]
        length(unique(all_matches(:,1))), length(telemetry_headers), ... %[output:1d7de3d9]
        100 * length(unique(all_matches(:,1))) / length(telemetry_headers)); %[output:1d7de3d9]
    fprintf('  Sensor variables matched: %d / %d (%.1f%%)\n', ... %[output:23a21a10]
        length(unique(all_matches(:,2))), length(sensor_headers), ... %[output:23a21a10]
        100 * length(unique(all_matches(:,2))) / length(sensor_headers)); %[output:23a21a10]
    
    % Statistics for high confidence matches (>= 0.7)
    if exist('high_conf_matches', 'var') && height(high_conf_matches) > 0
        high_conf_all = all_matches(high_conf_idx, :);
        high_conf_telem = unique(high_conf_all(:,1));
        high_conf_sensor = unique(high_conf_all(:,2));
        
        fprintf('\nHigh Confidence Matches (>= 0.7):\n'); %[output:4dbf52b9]
        fprintf('  Telemetry variables matched: %d / %d (%.1f%%)\n', ... %[output:94370095]
            length(high_conf_telem), length(telemetry_headers), ... %[output:94370095]
            100 * length(high_conf_telem) / length(telemetry_headers)); %[output:94370095]
        fprintf('  Sensor variables matched: %d / %d (%.1f%%)\n', ... %[output:89b25a11]
            length(high_conf_sensor), length(sensor_headers), ... %[output:89b25a11]
            100 * length(high_conf_sensor) / length(sensor_headers)); %[output:89b25a11]
    end
end %[output:group:07eed4c1]

fprintf('\n=== COMPLETE ===\n'); %[output:3bca2874]

%[appendix]{"version":"1.0"}
%---
%[metadata:view]
%   data: {"layout":"onright","rightPanelPercent":59.4}
%---
%[output:963e497d]
%   data: {"dataType":"text","outputData":{"text":"=== LOADING DICTIONARY ===\n","truncated":false}}
%---
%[output:79c9dbf1]
%   data: {"dataType":"text","outputData":{"text":"Dictionary loaded: 818 entries\n\n","truncated":false}}
%---
%[output:0c7ce6af]
%   data: {"dataType":"text","outputData":{"text":"=== LOADING TELEMETRY DATA (MOTEC) ===\n","truncated":false}}
%---
%[output:8e95651d]
%   data: {"dataType":"text","outputData":{"text":"Telemetry variables: 215\n","truncated":false}}
%---
%[output:8d9c9816]
%   data: {"dataType":"text","outputData":{"text":"=== LOADING SENSOR DATA (CARSIM) ===\n","truncated":false}}
%---
%[output:13b00aac]
%   data: {"dataType":"text","outputData":{"text":"Sensor variables: 1755\n\n","truncated":false}}
%---
%[output:18eaba69]
%   data: {"dataType":"text","outputData":{"text":"=== PASS 1: EXACT VARIABLE NAME MATCHES ===\n","truncated":false}}
%---
%[output:078abb7d]
%   data: {"dataType":"text","outputData":{"text":"Found 1 exact variable name matches\n\n","truncated":false}}
%---
%[output:38eb9012]
%   data: {"dataType":"text","outputData":{"text":"=== PASS 2: DICTIONARY-BASED MATCHING ===\n","truncated":false}}
%---
%[output:87f1db3d]
%   data: {"dataType":"text","outputData":{"text":"Found 1 dictionary-based matches\n\n","truncated":false}}
%---
%[output:322c8cb7]
%   data: {"dataType":"text","outputData":{"text":"=== PASS 3: SEMANTIC TOKEN MATCHING ===\n","truncated":false}}
%---
%[output:763249d7]
%   data: {"dataType":"text","outputData":{"text":"Found 0 semantic matches\n\n","truncated":false}}
%---
%[output:73e69610]
%   data: {"dataType":"text","outputData":{"text":"=== COMBINING RESULTS ===\n","truncated":false}}
%---
%[output:5a71ca4f]
%   data: {"dataType":"text","outputData":{"text":"\nTotal matches found (all confidence levels): 2\n","truncated":false}}
%---
%[output:9c08fc78]
%   data: {"dataType":"text","outputData":{"text":"Matches with confidence >= 0.7: 2\n","truncated":false}}
%---
%[output:4ff0c20f]
%   data: {"dataType":"text","outputData":{"text":"\nTop 30 matches (confidence >= 0.7):\n","truncated":false}}
%---
%[output:7af44b71]
%   data: {"dataType":"text","outputData":{"text":"    <strong>Telemetry_Variable<\/strong>    <strong>Sensor_Variable<\/strong>          <strong>MatchType<\/strong>          <strong>Confidence<\/strong>               <strong>Description<\/strong>            \n    <strong>__________________<\/strong>    <strong>________________<\/strong>    <strong>____________________<\/strong>    <strong>__________<\/strong>    <strong>__________________________________<\/strong>\n\n     {'Time'        }     {'Time'        }    {'Exact'           }        1         {'Identical variable names'      }\n     {'GPS Altitude'}     {'GPS_Altitude'}    {'Dictionary-Exact'}        1         {'T:GPSAltitude | S:GPS_Altitude'}\n\n","truncated":false}}
%---
%[output:3e94d7ff]
%   data: {"dataType":"text","outputData":{"text":"\nAll results saved to: variable_matches_all.csv\n","truncated":false}}
%---
%[output:3575db5f]
%   data: {"dataType":"text","outputData":{"text":"High confidence results (>= 0.7) saved to: variable_matches_high_confidence.csv\n","truncated":false}}
%---
%[output:3ca1c610]
%   data: {"dataType":"text","outputData":{"text":"\n=== SUMMARY STATISTICS ===\n","truncated":false}}
%---
%[output:7b822c88]
%   data: {"dataType":"text","outputData":{"text":"Exact name matches: 1\n","truncated":false}}
%---
%[output:88d7730c]
%   data: {"dataType":"text","outputData":{"text":"Dictionary matches: 1\n","truncated":false}}
%---
%[output:4b8c13bb]
%   data: {"dataType":"text","outputData":{"text":"Semantic matches: 0\n","truncated":false}}
%---
%[output:5ac29460]
%   data: {"dataType":"text","outputData":{"text":"Total matches (all): 2\n","truncated":false}}
%---
%[output:22db1705]
%   data: {"dataType":"text","outputData":{"text":"\nAll Matches:\n","truncated":false}}
%---
%[output:1d7de3d9]
%   data: {"dataType":"text","outputData":{"text":"  Telemetry variables matched: 2 \/ 215 (0.9%)\n","truncated":false}}
%---
%[output:23a21a10]
%   data: {"dataType":"text","outputData":{"text":"  Sensor variables matched: 2 \/ 1755 (0.1%)\n","truncated":false}}
%---
%[output:4dbf52b9]
%   data: {"dataType":"text","outputData":{"text":"\nHigh Confidence Matches (>= 0.7):\n","truncated":false}}
%---
%[output:94370095]
%   data: {"dataType":"text","outputData":{"text":"  Telemetry variables matched: 2 \/ 215 (0.9%)\n","truncated":false}}
%---
%[output:89b25a11]
%   data: {"dataType":"text","outputData":{"text":"  Sensor variables matched: 2 \/ 1755 (0.1%)\n","truncated":false}}
%---
%[output:3bca2874]
%   data: {"dataType":"text","outputData":{"text":"\n=== COMPLETE ===\n","truncated":false}}
%---
