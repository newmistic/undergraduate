function [edge_image] = my_edge(input_image, method, threshold, direction)
% MY_EDGE Performs edge detection on an image using specified method and parameters.
%   [edge_image] = MY_EDGE(input_image, method, threshold, direction)
%
%   input_image: The grayscale input image (double type, 0-1 range, or uint8).
%   method:      'Sobel' is currently supported.
%   threshold:   Scalar threshold for edge magnitude (between 0 and 1 if input is normalized).
%   direction:   'both' for horizontal and vertical edges.
%
%   edge_image: The resulting binary edge image.

if nargin < 4
    direction = 'both'; % Default direction
end
if nargin < 3
    threshold = 0.1; % Default threshold
end
if nargin < 2
    method = 'Sobel'; % Default method
end

% Ensure input_image is double and normalized to [0, 1] for calculations
if ~isa(input_image, 'double')
    input_image = im2double(input_image);
end

[rows, cols] = size(input_image);
edge_image = zeros(rows, cols); % Initialize output image

switch lower(method)
    case 'sobel'
        % Sobel kernels
        sobel_x = [-1 0 1; -2 0 2; -1 0 1];
        sobel_y = [-1 -2 -1; 0 0 0; 1 2 1];

        % Pad the image to handle borders
        padded_image = padarray(input_image, [1 1], 'replicate', 'both');

        % Convolve image with Sobel kernels
        Gx = zeros(rows, cols);
        Gy = zeros(rows, cols);

        for r = 1:rows
            for c = 1:cols
                % Extract 3x3 neighborhood
                neighborhood = padded_image(r:r+2, c:c+2);
                
                % Compute convolution
                Gx(r, c) = sum(sum(neighborhood .* sobel_x));
                Gy(r, c) = sum(sum(neighborhood .* sobel_y));
            end
        end

        % Calculate gradient magnitude
        gradient_magnitude = sqrt(Gx.^2 + Gy.^2);
        

        max_mag = max(gradient_magnitude(:));
        if max_mag > 0
            gradient_magnitude = gradient_magnitude / max_mag;
        end

        % Apply thresholding
        edge_image = gradient_magnitude > threshold;

    otherwise
        error('Unsupported edge detection method. Currently, only ''Sobel'' is supported.');
end

end