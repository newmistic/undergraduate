function varargout = GUI1(varargin)
% GUI1 MATLAB code for GUI1.fig
%      GUI1, by itself, creates a new GUI1 or raises the existing
%      singleton*.
%
%      H = GUI1 returns the handle to a new GUI1 or the handle to
%      the existing singleton*.
%
%      GUI1('CALLBACK',hObject,eventData,handles,...) calls the local
%      function named CALLBACK in GUI1.M with the given input arguments.
%
%      GUI1('Property','Value',...) creates a new GUI1 or raises the
%      existing singleton*.  Starting from the left, property value pairs are
%      applied to the GUI before GUI1_OpeningFcn gets called.  An
%      unrecognized property name or invalid value makes property application
%      stop.  All inputs are passed to GUI1_OpeningFcn via varargin.
%
%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
%      instance to run (singleton)".
%
% See also: GUIDE, GUIDATA, GUIHANDLES

% Edit the above text to modify the response to help GUI1

% Last Modified by GUIDE v2.5 12-Jun-2025 19:57:48

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @GUI1_OpeningFcn, ...
                   'gui_OutputFcn',  @GUI1_OutputFcn, ...
                   'gui_LayoutFcn',  [] , ...
                   'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT


% --- Executes just before GUI1 is made visible.
function GUI1_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to GUI1 (see VARARGIN)

% Choose default command line output for GUI1
handles.output = hObject;

handles.FunctionSwitch = 1;  % 默认启用所有功能

%隐藏坐标轴
set(handles.axes1,'visible','off');
set(handles.axes2,'visible','off');
set(handles.axes3,'visible','off');
set(handles.axes4,'visible','off');
set(handles.axes5,'visible','off');
set(handles.axes6,'visible','off');
set(handles.axes7,'visible','off');
set(handles.axes8,'visible','off');
set(handles.axes9,'visible','off');
set(handles.axes10,'visible','off');
set(handles.axes11,'visible','off');
set(handles.axes12,'visible','off');
set(handles.axes14,'visible','off');


% Update handles structure
guidata(hObject, handles);

% UIWAIT makes GUI1 wait for user response (see UIRESUME)
% uiwait(handles.figure1);


% --- Outputs from this function are returned to the command line.
function varargout = GUI1_OutputFcn(hObject, eventdata, handles) 
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
varargout{1} = handles.output;

%%%%%%%%%%%%%%%%%%%%%%%% 获取图像 %%%%%%%%%%%%%%%%%%%%%%%%%%%
% 打开本地图片
function openLocal_Callback(hObject,eventdata,handles)
%关于uigetfile

[filename, pathname]=uigetfile({'*.jpg; *.png; *.bmp; *.tif';'*.png';'All Image Files';'*.*'},'请选择图片路径');
if pathname==0
    return;
end
I=imread([pathname filename]);
%显示原图
axes(handles.axes1)     %将Tag值为axes1的坐标轴置为当前
imshow(I,[]);   %解决图像太大无法显示的问题.貌似会自动缩放
title('原图');
handles.I=I;        %更新图像
% Update handles structure
guidata(hObject, handles);


%%%%%%%%%%%%%%%%%%%%%%%% 图像预处理 %%%%%%%%%%%%%%%%%%%%%%%%%%%
% 灰度处理
function btnGray1_Callback(hObject, eventdata, handles) %#ok<*INUSL>
I=handles.I;          % 从handles结构体获取原始图像
I = rgb2gray(I);
axes(handles.axes2)     %将Tag值为axes2的坐标轴置为当前
imshow(I,[]);           %解决图像太大无法显示的问题
title('灰度处理');
figure,imhist(I);title('灰度图直方图');
handles.gray1=I;     %更新原图
% Update handles structure
guidata(hObject, handles);

% 边缘检测.
function btnEdge_Callback(hObject, eventdata, handles)
I=handles.gray1;    % 从handles获取灰度图像
edit2_a=get(handles.edit2,'string');  % 从编辑框获取文本
edit2_aa=str2double(edit2_a);
I = my_edge(I, 'Sobel', edit2_aa, 'both');  % 使用Sobel算子,'both'：检测水平和垂直两个方向的边缘
axes(handles.axes3)     %将Tag值为axes3的坐标轴置为当前
imshow(I,[]);   %解决图像太大无法显示的问题.
title('预处理边缘检测');
handles.edge=I;     %更新原图
% Update handles structure
guidata(hObject, handles);

%  边缘检测参数调试
function edit2_Callback(hObject, eventdata, handles)

guidata(hObject, handles);

%%%%%%%%%%%%%%%%%%%%%%%% 车牌定位 %%%%%%%%%%%%%%%%%%%%%%%%%%%
%  图像腐蚀.
function btnFushi_Callback(hObject, eventdata, handles)
I=handles.edge;  % 从handles获取边缘检测后的图像
edit3_a=get(handles.edit3,'string');  % 获取用户设置的腐蚀参数
edit3_aa=round(str2double(edit3_a));
SE = my_strel('rectangle',[edit3_aa,1]); % 创建矩形腐蚀结构元素
I = imerode(I, SE);  % 对边缘图像进行腐蚀
axes(handles.axes4)    % 定位到axes4坐标轴
imshow(I,[]);   
title('图像腐蚀');

handles.Fushi=I;     %更新原图
guidata(hObject, handles);


% 平滑处理
function btnSoft_Callback(hObject, eventdata, handles)
I=handles.Fushi;  % 从handles获取腐蚀后的图像
edit4_a=get(handles.edit4,'string');  % 获取用户设置的平滑参数
edit4_aa=round(str2double(edit4_a));
se = my_strel('rectangle', [edit4_aa, edit4_aa]);  % 创建正方形结构元素
I = imclose(I, se);     %执行闭运算，闭运算 = 先膨胀 + 后腐蚀
axes(handles.axes5)     
imshow(I,[]);   
title('平滑处理');

handles.Soft=I;    
guidata(hObject, handles);

% 移除对象
function btnRemove_Callback(hObject, eventdata, handles)
I=handles.Soft;  % 从handles获取平滑处理后的二值图像
edit5_a=get(handles.edit5,'string');  % 获取用户设置的小对象移除阈值
edit5_aa=double(str2double(edit5_a)) ;  
I = my_bwareaopen(I, edit5_aa);  % 移除像素数小于阈值的连通区域
axes(handles.axes6)     % 定位到axes6坐标轴
imshow(I,[]);   
title('移除对象');
handles.Remove=I;     
guidata(hObject, handles);

%  定位剪切
function btnCut_Callback(hObject, eventdata, handles)
img7=handles.Remove;  % 获取移除小对象后的二值图像
[y, x, z] = size(img7);
img8 = double(img7);    % 转成双精度浮点型

% 车牌的蓝色区域
% Y方向（垂直）定位车牌区域
blue_Y = zeros(y, 1);
for i = 1:y
    for j = 1:x
        if(img8(i, j) == 1) % 统计每行中的白色像素（车牌区域）
            blue_Y(i, 1) = blue_Y(i, 1) + 1;    % 像素点统计
        end
    end
end

% 找到车牌上边界（跳过空白行）
img_Y1 = 1;
while (blue_Y(img_Y1) < 5) && (img_Y1 < y)  % 5像素阈值，避免噪声影响
    img_Y1 = img_Y1 + 1;
end

% 找到Y坐标的最大值，找到车牌下边界
img_Y2 = y;
while (blue_Y(img_Y2) < 5) && (img_Y2 > img_Y1)
    img_Y2 = img_Y2 - 1;
end

% X方向（水平）定位车牌区域
blue_X = zeros(1, x);
for j = 1:x
    for i = 1:y
        if(img8(i, j) == 1)  % 统计每列中的白色像素（车牌区域）
            blue_X(1, j) = blue_X(1, j) + 1;
        end
    end
end

% 找到x坐标的最小值，找到车牌左边界
img_X1 = 1;
while (blue_X(1, img_X1) < 5) && (img_X1 < x)  % 5像素阈值，避免噪声影响
    img_X1 = img_X1 + 1;
end

% 找到x坐标的最小值，找到车牌右边界
img_X2 = x;
while (blue_X(1, img_X2) < 5) && (img_X2 > img_X1)
    img_X2 = img_X2 - 1;
end

% 对图像进行裁剪
img9 = handles.I(img_Y1:img_Y2, img_X1:img_X2, :);  % 从原图裁剪车牌区域
axes(handles.axes7)   % 定位到显示坐标轴
imshow(img9,[]);    % 显示裁剪后的车牌
title('图像裁剪');
imwrite(img9, '车牌图像.jpg');
handles.Cut=img9;     

%%%%%%%%%%%%%%%%%% 车牌颜色识别

% 分离RGB通道
r = img9(:,:,1);
g = img9(:,:,2);
b = img9(:,:,3);

% 计算各通道的平均值
mean_r = mean(r(:));
mean_g = mean(g(:));
mean_b = mean(b(:));

% 基于通道平均值进行颜色分类
if mean_b > mean_g && mean_b > mean_r
    numberplate_color=1;
    color='蓝色';
    disp('车牌颜色：蓝色');
    msgbox('车牌颜色：蓝色','识别出的车牌颜色')
elseif mean_g > mean_b && mean_g > mean_r
    numberplate_color=3;
    color='绿色';
    disp('车牌颜色：绿色');
    msgbox('车牌颜色：绿色','识别出的车牌颜色')
elseif mean_r > 170 && mean_g > 170 && mean_b > 170
    numberplate_color=4;
    color='白色';
    disp('车牌颜色：白色');
    msgbox('车牌颜色：白色','识别出的车牌颜色')
else
    numberplate_color=2;
    color='黄色';
    disp('车牌颜色：黄色');
    msgbox('车牌颜色：黄色','识别出的车牌颜色')
end

handles.numberplate_color=numberplate_color;
handles.color=color;
% Update handles structure
guidata(hObject, handles);

%%%%%%%%%%%%%%%%%%%%%%%% 车牌识别 %%%%%%%%%%%%%%%%%%%%%%%%%%%

% 灰度处理
function btnGray2_Callback(hObject, eventdata, handles)
I=handles.Cut;   % 获取车牌定位后裁剪的彩色图像
I = rgb2gray(I);
axes(handles.axes8)     
imshow(I,[]);    % 显示灰度车牌图像（自动对比度调整）
title('灰度处理');
handles.gray2=I;     
guidata(hObject, handles);

%  直方图均衡化
function btnBalance_Callback(hObject, eventdata, handles)
I=handles.gray2;   % 获取前一步的灰度车牌图像
edit6_a=get(handles.edit6,'string');
edit6_aa=double(str2double(edit6_a));
I = my_histeq(I,edit6_aa);  % 执行直方图均衡化，增强图像对比度
axes(handles.axes9)    
imshow(I,[]);   
title('直方图均衡化');
figure,subplot(1,2,1),imhist(handles.gray2);title('灰度直方图');
subplot(1,2,2),imhist(I);title('均衡化后的直方图');

handles.balance=I;     
guidata(hObject, handles);

% 二值化图像
function btnDouble_Callback(hObject, eventdata, handles)
I=handles.balance;  % 获取直方图均衡化处理后的车牌图像
edit8_a=get(handles.edit8,'string');  % 获取用户设置的二值化阈值
edit8_aa=double(str2double(edit8_a));
% 非蓝色车牌图像取反
if handles.numberplate_color~=1
    I=imcomplement(I);  % 反转图像（黑变白，白变黑）
end
I = my_imbinarize(I, edit8_aa);  % 使用指定阈值进行二值化
axes(handles.axes10)    
imshow(I,[]);   
title('图像二值化');
handles.double=I;    
guidata(hObject, handles);

% 移除对象
% --- Executes on button press in remove2.
function remove2_Callback(hObject, eventdata, handles)
I=handles.double;   % 获取二值化后的车牌图像
edit11_a=get(handles.edit11,'string');   % 获取用户设置的对象移除阈值
edit11_aa=double(str2double(edit11_a)) ;
I = my_bwareaopen(I, edit11_aa);  % 执行小对象移除操作
axes(handles.axes11)    
imshow(I,[]);   
title('移除对象');
handles.Remove2=I;   
guidata(hObject, handles);

% 中值滤波
function btnMid_Callback(hObject, eventdata, handles)
I=handles.Remove2;  % 获取经过小对象移除处理后的二值图像
edit9_a=get(handles.edit9,'string');  % 获取用户设置的滤波参数
edit9_aa=double(str2double(edit9_a));
% 执行二维中值滤波
I = my_medfilt2(I,[1 edit9_aa]);  % 水平方向滤波
I = my_medfilt2(I,[edit9_aa 1 ]); % 垂直方向滤波
axes(handles.axes12)    
imshow(I,[]);  
imwrite(I,'中值滤波.jpg')
title('中值滤波');

handles.Mid=I;   
guidata(hObject, handles);


%  图像切割
function btnCut2_Callback(hObject, eventdata, handles)
I=handles.Mid;  % 经过中值滤波处理后的二值化车牌图像
I = imsplit(I);  % 切割图像
[m, n] = size(I);

figure;
imshow(I);

s = sum(I);    %sum(x)就是竖向相加，求每列的和，结果是行向量;
               % 基于垂直投影 s 来大致分离字符

%%%%% 初步字符分离（基于垂直投影）
j = 1;  % 遍历列
k1 = 1; % 标记字符的起始列
k2 = 1; % 标记字符的结束列
while j ~= n  % 遍历所有列
    while s(j) == 0  % 跳过黑色区域（列和为0）
        j = j + 1;
    end
    k1 = j;
    while s(j) ~= 0 && j <= n-1  % 遍历字符区域（列和不为0）
        j = j + 1;
    end
    k2 = j + 1;
    if k2 - k1 > round(n / 6.5)  % round(n / 6.5) 是一个经验值，大约是单个字符的平均宽度
        [val, num] = min(sum(I(:, [k1+5:k2-5]))); %如果宽度过大，在当前连通区域的内部（排除边缘5像素）寻找垂直投影的最小值。
        I(:, k1+num+5) = 0; %在找到的最小投影处（即最适合切割的位置），将该列的所有像素设置为0（黑色）。这相当于在字符间插入一条黑线，强制将粘连的字符分割开
    end
end
%%%%% 逐个提取字符（从左到右）
y1 = 10;   %字符的最小宽度阈值
y2 = 0.05;  %字符中间区域像素密度阈值
flag = 0;   %当第一个有效字符被成功提取时设为1
word1 = [];  %存储第一个字符
while flag == 0
    [m, n] = size(I);
    left = 1;
    width = 0;  %测量当前连续白色区域的宽度
    while sum(I(:, width+1)) ~= 0 || width<n/9  %寻找第一个字符的右边界
        width = width + 1;
    end
    if width < y1  %如果当前找到的连续区域宽度小于y1（10），则认为这是噪声
        I(:, [1:width]) = 0;
        I = imsplit(I);
    else
        temp = imsplit(imcrop(I, [1,1,width,m])); %裁剪出这个潜在的字符区域
        [m, n] = size(temp);
        all = sum(sum(temp));  %计算所有白色像素的总和
        two_thirds=sum(sum(temp([round(m/3):2*round(m/3)],:)));  %计算图像中间三分之一区域的白色像素总和
        if two_thirds/all > y2  %如果中间三分之一区域的像素密度（白色像素比例）大于 y2（0.05），则认为这是一个有效的字符
            flag = 1;  %第一个字符已找到，退出外部循环
            word1 = temp;  %将找到的第一个字符保存到 word1
        end
        I(:, [1:width]) = 0; %将已提取的字符区域从原图中移除
        I = imsplit(I);
    end
end

 % 分割出第二个字符
 [word2,I]=getword(I);  %重复多次
 % 分割出第三个字符
 [word3,I]=getword(I);
 % 分割出第四个字符
 [word4,I]=getword(I);
 % 分割出第五个字符
 [word5,I]=getword(I);
 % 分割出第六个字符
 [word6,I]=getword(I);
 % 分割出第七个字符
 [word7,I]=getword(I);
 
 % 新能源汽车加一个字符
 if handles.numberplate_color==3
  [word8,I]=getword(I);
 end
 
 figure;

 word1=imresize(word1,[40 20]);%imresize对图像做缩放处理，常用调用格式为：B=imresize(A,ntimes,method)；其中method可选nearest,bilinear（双线性）,bicubic,box,lanczors2,lanczors3等
 word2=imresize(word2,[40 20]);%将每个分割出的字符图像统一调整大小为 40x20 像素
 word3=imresize(word3,[40 20]);
 word4=imresize(word4,[40 20]);
 word5=imresize(word5,[40 20]);
 word6=imresize(word6,[40 20]);
 word7=imresize(word7,[40 20]);

 
if handles.numberplate_color==3
   word8=imresize(word8,[40 20]);
end

 subplot(5,8,17),imshow(word1),title('1');
 subplot(5,8,18),imshow(word2),title('2');
 subplot(5,8,19),imshow(word3),title('3');
 subplot(5,8,20),imshow(word4),title('4');
 subplot(5,8,21),imshow(word5),title('5');
 subplot(5,8,22),imshow(word6),title('6');
 subplot(5,8,23),imshow(word7),title('7');

 
if handles.numberplate_color==3
   subplot(5,8,24),imshow(word8),title('8');
end
 
 imwrite(word1,'1.jpg'); % 创建七位车牌字符图像
 imwrite(word2,'2.jpg');
 imwrite(word3,'3.jpg');
 imwrite(word4,'4.jpg');
 imwrite(word5,'5.jpg');
 imwrite(word6,'6.jpg');
 imwrite(word7,'7.jpg');

 
if handles.numberplate_color==3
  imwrite(word8,'8.jpg');
end


% 模板匹配
function btnSelect_Callback(hObject, eventdata, handles)
liccode=char(['0':'9' 'A':'Z' '川赣贵黑吉冀津晋京警辽鲁蒙闽宁陕苏皖湘豫粤浙']);%建立自动识别字符代码表；'京津沪渝港澳吉辽鲁豫冀鄂湘晋青皖苏赣浙闽粤琼台陕甘云川贵黑藏蒙桂新宁'

subBw2 = zeros(40, 20);
 num = 1;   % 车牌位数
 
 % 判断车牌位数
 if handles.numberplate_color==3
   car_size=8;
 else
   car_size=7;     
 end
 
 for i = 1:car_size  % 遍历车牌的每一位字符
    ii = int2str(i);    % 用于构建文件名
    word = imread([ii,'.jpg']); % 读取之前分割出的字符的图片
    segBw2 = imresize(word, [40,20], 'nearest');    % 调整图片的大小
    segBw2 = imbinarize(segBw2, 0.5);    % 图像二值化
    if i == 1   % 字符第一位为汉字，定位汉字所在字段
        kMin = 37;
        kMax = 58;
    elseif i == 2   % 第二位为英文字母，定位字母所在字段
        kMin = 11;
        kMax = 36;
    elseif i >= 3   % 第三位开始就是数字或字母了，定位数字和字母所在字段
        kMin = 1;
        kMax = 37;
    end
    
    l = 1;
    disp(kMin);
    disp(kMax);
    for k = kMin : kMax  % 遍历当前位字符应该匹配的模板库范围
        fname = strcat('车牌匹配库\',liccode(k),'.jpg');  % 根据字符库找到图片模板
        samBw2 = imread(fname); % 读取模板库中的图片
        if size(samBw2, 3) == 3 % RGB图像转为灰度图像
            samBw2 = rgb2gray(samBw2); 
        end
        samBw2 = imbinarize(samBw2, 0.5);    % 图像二值化
        
        % 将待识别图片与模板图片做差（核心）
        for i1 = 1:40
            for j1 = 1:20
                subBw2(i1, j1) = segBw2(i1, j1) - samBw2(i1 ,j1); %由于是二值图像（0或1），如果两个像素相同，差值为0；如果不同，差值为-1或1
            end
        end
        
        % 统计两幅图片不同点的个数，并保存下来
        Dmax = 0;  %待识别字符与当前模板图片之间像素不一致的数量
        for i2 = 1:40
            for j2 = 1:20
                if subBw2(i2, j2) ~= 0
                    Dmax = Dmax + 1;
                end
            end
        end
        error(l) = Dmax; %记录所有模板的差异值
        l = l + 1;
        disp(Dmax); %差异值
        disp(liccode(k));  %当前匹配的字符模板
        disp(fname); %模板文件名
    end
    
    % 找到图片差别最少的图像
    errorMin = min(error);
    disp(errorMin);
    findc = find(error == errorMin);
%     error
%     findc
       
    % 根据字库，对应到识别的字符
    Code(num) = liccode(findc(1) + kMin - 1);
    num = num + 1;
    % 白色警车
    if handles.numberplate_color==4
        Code(7) = '警';
    end
    
 end
 
 handles.CodeID=Code;
 axes(handles.axes14)     %将Tag值为axes1的坐标轴置为当前
 imshow(handles.Cut,[]);   %解决图像太大无法显示的问题.
 title('车牌');

 %    [IDCP,IDNUM,IDNAME]=IDFind(Code);
 msg = ['车牌号：', Code, ', 这是一张', handles.color, '车牌'];
 msgbox(msg,'识别出的车牌号');
 disp(Code);

 
 guidata(hObject, handles);


%%%%%%%%%%%%%%%%%%%%%%%% 文本编辑 %%%%%%%%%%%%%%%%%%%%%%%%%%%

function edit6_Callback(hObject, eventdata, handles)
% hObject    handle to edit6 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edit6 as text
%        str2double(get(hObject,'String')) returns contents of edit6 as a double


% --- Executes during object creation, after setting all properties.
function edit6_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit6 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end



function edit8_Callback(hObject, eventdata, handles)
% hObject    handle to edit8 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edit8 as text
%        str2double(get(hObject,'String')) returns contents of edit8 as a double


% --- Executes during object creation, after setting all properties.
function edit8_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit8 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end



function edit9_Callback(hObject, eventdata, handles)
% hObject    handle to edit9 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edit9 as text
%        str2double(get(hObject,'String')) returns contents of edit9 as a double


% --- Executes during object creation, after setting all properties.
function edit9_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit9 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end



function edit11_Callback(hObject, eventdata, handles)
% hObject    handle to edit11 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edit11 as text
%        str2double(get(hObject,'String')) returns contents of edit11 as a double


% --- Executes during object creation, after setting all properties.
function edit11_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit11 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end





function edit5_Callback(hObject, eventdata, handles)
% hObject    handle to edit5 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edit5 as text
%        str2double(get(hObject,'String')) returns contents of edit5 as a double


% --- Executes during object creation, after setting all properties.
function edit5_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit5 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edit4_Callback(hObject, eventdata, handles)
% hObject    handle to edit4 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edit4 as text
%        str2double(get(hObject,'String')) returns contents of edit4 as a double


% --- Executes during object creation, after setting all properties.
function edit4_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit4 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function edit3_Callback(hObject, eventdata, handles)
% hObject    handle to edit3 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edit3 as text
%        str2double(get(hObject,'String')) returns contents of edit3 as a double


% --- Executes during object creation, after setting all properties.
function edit3_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit3 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end



% --- Executes during object creation, after setting all properties.
function edit2_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit2 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end



