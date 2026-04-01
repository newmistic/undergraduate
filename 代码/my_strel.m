function SE_Neighborhood_Matrix = my_strel(shape, parameters)
% MY_STREL Creates a structuring element (binary matrix) for morphological operations.
%   SE_Neighborhood_Matrix = MY_STREL(shape, parameters)
%
%   shape:      String, currently only 'rectangle' is supported.
%   parameters: For 'rectangle', a 1x2 vector [height, width] specifying
%               the dimensions of the rectangle.
%
%   SE_Neighborhood_Matrix: A binary (logical) matrix defining the shape of the SE.

if nargin < 2
    error('my_strel requires at least two input arguments: shape and parameters.');
end

if ~ischar(shape)
    error('Shape must be a string (e.g., ''rectangle'').');
end

switch lower(shape)
    case 'rectangle'
        if ~isnumeric(parameters) || numel(parameters) ~= 2 || any(parameters <= 0)
            error('For ''rectangle'' shape, parameters must be a 1x2 numeric vector [height, width] with positive values.');
        end
        
        height = parameters(1);
        width = parameters(2);
        
        % Directly return the binary matrix (logical type is good for SE)
        SE_Neighborhood_Matrix = true(height, width); % Use true for 1, false for 0
        
    otherwise
        error('Unsupported shape. Currently, only ''rectangle'' is supported for my_strel.');
end

end