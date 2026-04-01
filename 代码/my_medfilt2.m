function J = my_medfilt2(I, filter_size)
% MY_MEDFILT2 Performs 2D median filtering on an image.
%   J = MY_MEDFILT2(I, filter_size) performs median filtering,
%   where each output pixel contains the median value in the
%   m x n neighborhood around the corresponding pixel in the input image.
%
%   I:            The input image (grayscale, numeric).
%   filter_size:  A 1x2 vector [m n] specifying the dimensions of the
%                 neighborhood (filter mask).
%
%   J:            The resulting image after median filtering,
%                 with the same class as the input image I.

if nargin < 2
    error('my_medfilt2 requires two input arguments: I and filter_size.');
end

if ~isnumeric(I) && ~islogical(I)
    error('Input image I must be a numeric or logical array.');
end

if ~isnumeric(filter_size) || numel(filter_size) ~= 2 || any(filter_size <= 0)
    error('filter_size must be a 1x2 numeric vector [m n] with positive values.');
end

m = filter_size(1); % Height of the filter mask
n = filter_size(2); % Width of the filter mask

% Convert image to double for processing, then convert back at the end
original_class = class(I);
I_double = double(I);

[rows, cols] = size(I_double);
J = zeros(rows, cols); % Initialize output image

% Calculate padding required for the filter mask
pad_m = floor(m / 2); % Padding rows
pad_n = floor(n / 2); % Padding columns


I_padded = padarray(I_double, [pad_m, pad_n], 'replicate', 'both');

% Iterate over each pixel in the original image dimensions
for r = 1:rows
    for c = 1:cols
        window = I_padded(r : r + m - 1, c : c + n - 1);
        % Calculate the median of the pixel values in the window
        J(r, c) = median(window(:)); % Use (:) to treat the window as a 1D array for median calculation
    end
end

% Convert the output image J back to its original class
J = cast(J, original_class);

end