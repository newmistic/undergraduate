function BW = my_imbinarize(I, T)
% MY_IMBINARIZE Binarizes a grayscale image using a specified threshold.
%   BW = MY_IMBINARIZE(I, T) creates a binary image BW from a grayscale
%   image I by replacing all values greater than or equal to the threshold T
%   with 1 (true) and all other values with 0 (false).
%
%   I: The input grayscale image (numeric array, e.g., uint8, double).
%   T: The global image threshold, specified as a scalar brightness value.
%
%   BW: The resulting binary image (logical type).

if nargin < 2
    error('my_imbinarize requires two input arguments: I and T (threshold).');
end

if ~isnumeric(I)
    error('Input image I must be a numeric array.');
end

if ~isnumeric(T) || ~isscalar(T)
    error('Threshold T must be a numeric scalar.');
end

I_double = im2double(I);

BW = (I_double >= T);

end