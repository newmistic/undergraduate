function BW2 = my_bwareaopen(BW, P)
% MY_BWAREAOPEN Removes small connected components from a binary image.
%   BW2 = MY_BWAREAOPEN(BW, P) removes all connected components (objects)
%   from the binary image BW that have fewer than P pixels, and returns

%   the resulting binary image BW2.
%
%   BW: A binary image (logical or numeric, will be converted to logical).
%   P:  The minimum number of pixels for an object to be retained.
%   BW2: The output binary image with small objects removed.

if nargin < 2
    error('my_bwareaopen requires two input arguments: BW and P.');
end

if ~islogical(BW)
    % Ensure the input image is logical for consistent behavior
    BW = logical(BW);
end

[L, num_objects] = bwlabel(BW);

% Initialize the output image as a copy of the input
BW2 = BW; 

% If no objects found, return the original (empty) image
if num_objects == 0
    return;
end

stats = regionprops(L, 'Area');

% Iterate through each object
for k = 1:num_objects
    % Check if the area of the current object is less than the threshold P
    if stats(k).Area < P
        % If it's a small object, remove it from BW2
        % This is done by setting all pixels corresponding to this label to false (0)
        BW2(L == k) = false; 
    end
end

end