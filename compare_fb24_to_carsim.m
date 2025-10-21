% === CONFIGURATION ===
motecFile = 'motec.csv';      % Your MoTeC export
carsimFile = 'oct14Carsim.csv'; % Your CarSim data

% === STEP 1: READ FILES ===
motecData = readcell(motecFile);
carsimData = readcell(carsimFile);

% === STEP 2: FIND HEADER ROW (the one that starts with "Time") ===
headerRow = find(strcmp(motecData(:,1), 'Time'), 1);
headers = motecData(headerRow, :);

% === STEP 3: FIND ROW CONTAINING 'fb24' ===
fb24Row = [];
for i = 1:size(motecData,1)
    rowStr = string(motecData(i,:));
    if any(contains(rowStr, 'fb24', 'IgnoreCase', true))
        fb24Row = i;
        break;
    end
end

if isempty(fb24Row)
    error('No row containing "fb24" was found.');
end

% === STEP 4: Extract fb24 data ===
fb24Values = motecData(fb24Row, :);

% === STEP 5: Extract CarSim data (assume values are in row 1) ===
carsimHeaders = carsimData(1, :);
carsimValues = carsimData(2, :);

% === STEP 6: Create dictionaries (containers.Map) ===
fb24Map = containers.Map(headers, fb24Values);
carsimMap = containers.Map(carsimHeaders, carsimValues);

% === STEP 7: Compare values ===
sameKeys = intersect(keys(fb24Map), keys(carsimMap));
matches = {};
differences = {};

for k = 1:length(sameKeys)
    key = sameKeys{k};
    val1 = fb24Map(key);
    val2 = carsimMap(key);

    % Convert numeric strings to numbers if possible
    num1 = str2double(val1);
    num2 = str2double(val2);
    if isnan(num1) || isnan(num2)
        equal = isequal(val1, val2);
    else
        equal = abs(num1 - num2) < 1e-6; % tolerance for float equality
    end

    if equal
        matches(end+1,:) = {key, val1}; %#ok<AGROW>
    else
        differences(end+1,:) = {key, val1, val2}; %#ok<AGROW>
    end
end

% === STEP 8: Display results ===
fprintf('✅ %d matching values found.\n', size(matches,1));
fprintf('⚠️ %d differing values found.\n', size(differences,1));

if ~isempty(differences)
    disp('--- Differences ---');
    diffTable = cell2table(differences, 'VariableNames', {'Channel', 'MoTeC_FB24', 'CarSim'});
    disp(diffTable);
end


%[appendix]{"version":"1.0"}
%---
%[metadata:view]
%   data: {"layout":"onright"}
%---
