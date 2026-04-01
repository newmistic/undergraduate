function J = my_histeq(I, n_bins)
% MY_HISTEQ Performs histogram equalization on an image.
%   J = MY_HISTEQ(I, n_bins) transforms the grayscale image I,
%   so that the histogram of the output grayscale image J is
%   approximately flat with n_bins.
%
%   I:       The input grayscale image (uint8 or double).
%   n_bins:  The desired number of bins for the output histogram.
%            If not specified, a default of 256 is used for uint8,
%            or a suitable range for double images.
%
%   J:       The resulting image after histogram equalization,
%            with the same class as the input image I.

if nargin < 1
    error('my_histeq requires at least one input argument: I.');
end

% Determine the input image class and max pixel value for normalization
original_class = class(I);
if islogical(I)
    % Convert logical to uint8 for histogram calculation
    I = uint8(I);
    max_val = 1; % Logical image only has 0 and 1
    num_levels = 2;
elseif isa(I, 'uint8')
    max_val = 255;
    num_levels = 256; % Number of possible gray levels for uint8
elseif isa(I, 'uint16')
    max_val = 65535;
    num_levels = 65536;
elseif isa(I, 'double') || isa(I, 'single')
    max_val = 1; 
    num_levels = 256; % For double, we often target 256 output levels unless specified
else
    error('Unsupported image class. Only logical, uint8, uint16, double, or single images are supported.');
end

if nargin < 2
    n_bins = num_levels; % Default to full range of possible levels
end

% Ensure n_bins is a positive integer
if ~isnumeric(n_bins) || ~isscalar(n_bins) || n_bins <= 0 || mod(n_bins, 1) ~= 0
    error('n_bins must be a positive integer scalar.');
end

I_double = im2double(I); 
hist_counts = zeros(num_levels, 1);
for val = 0 : (num_levels - 1)
    % Map scaled double value to original level for counting
    pixel_val = val / (num_levels - 1); 
    hist_counts(val + 1) = sum(I_double(:) == pixel_val);
end

if isa(I, 'double') || isa(I, 'single')
    % Determine bin edges for double image
    bin_edges = linspace(0, 1, num_levels + 1);
    hist_counts = histcounts(I_double(:), bin_edges)';
end


cdf = cumsum(hist_counts);

total_pixels = sum(hist_counts);
if total_pixels == 0
    J = I; % Return original if no pixels
    return;
end
cdf_normalized = cdf / total_pixels;


% Create a lookup table (LUT) for transformation
transform_lut = round(cdf_normalized * (n_bins - 1)); % Map to 0 to n_bins-1 range
transform_lut = transform_lut / (n_bins - 1) * max_val; % Scale to original intensity range [0, max_val]

% Ensure LUT values are within valid range (e.g., for uint8, [0, 255])
transform_lut = max(0, min(max_val, transform_lut)); 

J_double = zeros(size(I_double));
% Iterate through each possible original pixel value
for val_idx = 1 : num_levels
    original_pixel_value_scaled = (val_idx - 1) / (num_levels - 1); % 0 to 1 range
    % Find all pixels in I_double that match this value and apply the transformation
    J_double(I_double == original_pixel_value_scaled) = transform_lut(val_idx);
end

% Convert the output image J back to the original class
J = cast(J_double, original_class);

end