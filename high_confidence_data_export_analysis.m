% MATLAB Analysis Script for high_confidence_data_export
% Generated: 2025-11-12 02:39:28 UTC
% This script loads the exported telemetry data and creates analysis plots

clear; clc; close all;

%% Load Data
fprintf('Loading data from high_confidence_data_export.csv...\n');
data = readtable('high_confidence_data_export.csv');

%% Display Summary Statistics
fprintf('\n=== Data Summary ===\n');
fprintf('Total samples: %d\n', height(data));
fprintf('Variables: %d\n', width(data));
disp(summary(data));

%% Get numeric columns for plotting
numeric_cols = varfun(@isnumeric, data, 'OutputFormat', 'uniform');
numeric_data = data(:, numeric_cols);
variable_names = numeric_data.Properties.VariableNames;

fprintf('\nFound %d numeric variables for plotting\n', length(variable_names));

%% Create Time Series Plots
figure('Name', 'Telemetry Data Overview', 'Position', [100, 100, 1200, 800]);

num_vars = length(variable_names);
num_plots = min(num_vars, 9); % Plot up to 9 variables

for i = 1:num_plots
    subplot(3, 3, i);
    var_name = variable_names{i};
    
    % Plot the variable
    plot(numeric_data.(var_name), 'LineWidth', 1.5);
    
    title(strrep(var_name, '_', '\_'), 'FontSize', 10);
    xlabel('Sample Index');
    ylabel('Value');
    grid on;
end

sgtitle('Telemetry Data - First 9 Variables', 'FontSize', 14, 'FontWeight', 'bold');

%% Create Correlation Matrix (if enough variables)
if num_vars > 1
    figure('Name', 'Correlation Matrix', 'Position', [150, 150, 800, 600]);
    
    % Calculate correlation matrix
    corr_matrix = corr(table2array(numeric_data), 'Rows', 'complete');
    
    % Plot heatmap
    imagesc(corr_matrix);
    colorbar;
    colormap('jet');
    caxis([-1 1]);
    
    title('Variable Correlation Matrix', 'FontSize', 14);
    xlabel('Variable Index');
    ylabel('Variable Index');
    
    % Add text annotations
    [rows, cols] = size(corr_matrix);
    for i = 1:min(rows, 20) % Limit to 20x20 for readability
        for j = 1:min(cols, 20)
            text(j, i, sprintf('%.2f', corr_matrix(i,j)), ...
                'HorizontalAlignment', 'center', ...
                'FontSize', 8);
        end
    end
end

%% Statistical Analysis
fprintf('\n=== Statistical Analysis ===\n');
for i = 1:min(num_vars, 5) % Show stats for first 5 variables
    var_name = variable_names{i};
    var_data = numeric_data.(var_name);
    
    fprintf('\n%s:\n', var_name);
    fprintf('  Mean: %.4f\n', mean(var_data, 'omitnan'));
    fprintf('  Std:  %.4f\n', std(var_data, 'omitnan'));
    fprintf('  Min:  %.4f\n', min(var_data));
    fprintf('  Max:  %.4f\n', max(var_data));
    fprintf('  Range: %.4f\n', range(var_data));
end

%% Distribution Plots
figure('Name', 'Data Distributions', 'Position', [200, 200, 1200, 600]);

for i = 1:min(num_plots, 6)
    subplot(2, 3, i);
    var_name = variable_names{i};
    
    histogram(numeric_data.(var_name), 30, 'Normalization', 'probability');
    title(strrep(var_name, '_', '\_'), 'FontSize', 10);
    xlabel('Value');
    ylabel('Probability');
    grid on;
end

sgtitle('Variable Distributions', 'FontSize', 14, 'FontWeight', 'bold');

%% Export Summary
fprintf('\n=== Export Complete ===\n');
fprintf('All plots generated successfully!\n');
fprintf('You can now analyze the data further or save the figures.\n');

% Optionally save figures
% saveas(gcf, 'telemetry_distributions.png');
